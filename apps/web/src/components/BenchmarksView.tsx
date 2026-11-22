import { useEffect, useRef, useState } from 'react';
import { Download } from 'lucide-react';
import * as echarts from 'echarts';
import type { MetricsV1, SupportedFeatures } from '../data/types';

interface BenchmarksViewProps {
  metrics: MetricsV1 | null;
  features: SupportedFeatures;
}

function ConfusionHeatmap({
  labels,
  matrix,
}: {
  labels: string[];
  matrix: number[][];
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const data: [number, number, number][] = [];
    let maxVal = 1;
    matrix.forEach((row, r) =>
      row.forEach((val, c) => {
        data.push([c, r, val]);
        if (val > maxVal) maxVal = val;
      })
    );

    chart.setOption({
      tooltip: {
        position: 'top',
        formatter: (p: { value: [number, number, number] }) =>
          `True: <b>${labels[p.value[1]]}</b><br/>Pred: <b>${labels[p.value[0]]}</b><br/>Windows: <b>${p.value[2]}</b>`,
      },
      grid: { left: 132, right: 20, top: 18, bottom: 52 },
      xAxis: {
        type: 'category',
        data: labels.map((l) => l.replace('COMPRESSOR_', 'COMP_')),
        name: 'Predicted Class',
        nameLocation: 'middle',
        nameGap: 32,
        axisLabel: { fontSize: 10, color: '#3D5166' },
      },
      yAxis: {
        type: 'category',
        data: labels.map((l) => l.replace('COMPRESSOR_', 'COMP_')),
        inverse: true,
        axisLabel: { fontSize: 10, color: '#3D5166' },
      },
      visualMap: {
        min: 0,
        max: maxVal,
        show: false,
        inRange: { color: ['#F4F4E9', '#7CC6C3', '#007F86', '#0E3F3C'] },
      },
      series: [
        {
          type: 'heatmap',
          data,
          label: { show: true, fontWeight: 700, fontSize: 12 },
        },
      ],
    });

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(ref.current);
    return () => {
      ro.disconnect();
      chart.dispose();
    };
  }, [labels, matrix]);

  return <div ref={ref} style={{ width: '100%', height: 260 }} />;
}

function RiskCoverageChart({
  metrics,
  scope,
}: {
  metrics: MetricsV1;
  scope: string;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const methodMeta: { id: string; label: string; color: string; dashed?: boolean }[] = [
      { id: 's_C', label: 's_C (H2-PRISM)', color: '#0E3F3C' },
      { id: 's_C_minus_D', label: 's_C−D (No D)', color: '#007F86', dashed: true },
      { id: 'confidence', label: 'Baseline Confidence', color: '#B45309', dashed: true },
      { id: 'D_only', label: 'D(x) Only', color: '#64748B', dashed: true },
    ];

    const series = methodMeta.map((m) => {
      const pts = metrics.risk_coverage_series
        .filter((p) => p.scope === scope && p.method === m.id && p.status === 'ESTIMABLE')
        .map((p) => [
          Number(((p.coverage ?? 0) * 100).toFixed(2)),
          Number(((p.selective_risk ?? 0) * 100).toFixed(2)),
        ]);
      return {
        name: m.label,
        type: 'line',
        smooth: false,
        symbolSize: 6,
        itemStyle: { color: m.color },
        lineStyle: { width: m.dashed ? 1.8 : 2.6, type: m.dashed ? 'dashed' : 'solid', color: m.color },
        data: pts,
      };
    });

    chart.setOption({
      tooltip: { trigger: 'axis', valueFormatter: (v: unknown) => `${Number(v).toFixed(2)}%` },
      legend: { top: 0, textStyle: { fontSize: 10.5, color: '#3D5166' } },
      grid: { left: 52, right: 18, top: 36, bottom: 40 },
      xAxis: {
        type: 'value',
        name: 'Realized Coverage (%)',
        nameLocation: 'middle',
        nameGap: 24,
        min: 0,
        max: 100,
      },
      yAxis: {
        type: 'value',
        name: 'Selective Risk (%)',
        min: 0,
      },
      series,
    });

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(ref.current);
    return () => {
      ro.disconnect();
      chart.dispose();
    };
  }, [metrics, scope]);

  return <div ref={ref} style={{ width: '100%', height: 260 }} />;
}

export function BenchmarksView({ metrics, features }: BenchmarksViewProps) {
  const [scope, setScope] = useState<string>('pooled');
  const [asTable, setAsTable] = useState(false);

  if (!metrics) {
    return (
      <main className="benchmarks-page">
        <div className="panel" style={{ padding: 18 }}>
          <h2 style={{ margin: '0 0 6px', fontSize: '1rem' }}>Evaluation Metrics Unavailable</h2>
          <p style={{ margin: 0, color: 'var(--ink-secondary)', fontSize: '0.88rem' }}>
            No verified evaluation bundle is attached to this catalog release.
          </p>
        </div>
      </main>
    );
  }

  const cm = metrics.confusion_matrices_by_scope[scope] ?? metrics.confusion_matrices_by_scope.pooled;
  const sC06 = metrics.matched_coverage_06.find((r) => r.method === 's_C');
  const conf06 = metrics.matched_coverage_06.find((r) => r.method === 'confidence');

  const downloadEvidenceCsv = () => {
    const header = 'method,target_coverage,coverage,selective_risk,n_specific,n_eligible,n_families,folds_estimable';
    const rows = metrics.matched_coverage_06.map(
      (r) =>
        `${r.method},${r.target_coverage},${r.coverage},${r.selective_risk},${r.n_specific},${r.n_eligible},${r.n_families},${r.folds_estimable}`
    );
    const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `h2-prism-${metrics.run_key.slice(0, 10)}-matched-coverage.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="benchmarks-page">
      <div
        className="hint-strip"
        style={{
          borderRadius: 'var(--radius-md)',
          border: '1px solid rgba(180, 83, 9, 0.35)',
          background: '#FEF3C7',
          color: '#78350F',
        }}
      >
        <span>
          <strong>{metrics.rq1_status}:</strong> {metrics.rq1_note}
        </span>
      </div>

      <div
        className="hint-strip"
        style={{ borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}
      >
        <span>
          <strong>Split:</strong> {metrics.split} · <strong>Total N:</strong> {metrics.cohort_n.toLocaleString()} windows ·{' '}
          <strong>Estimable (target 0.60):</strong> {metrics.estimable_n.toLocaleString()} (2/3 folds) ·{' '}
          <strong>CI:</strong> {metrics.ci_method}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button type="button" className="seg-btn" onClick={downloadEvidenceCsv}>
            <Download size={13} />
            CSV
          </button>
          <button
            type="button"
            className={`seg-btn ${asTable ? 'active' : ''}`}
            onClick={() => setAsTable((v) => !v)}
          >
            {asTable ? 'Show Charts' : 'Show Tables'}
          </button>
        </div>
      </div>

      <section className="kpi-grid" aria-label="Summary evaluation metrics">
        <div className="kpi-card">
          <div className="meta-label">s_C Selective Risk (0.60, 2 folds)</div>
          <div className="kpi-value">
            {sC06 ? `${(sC06.selective_risk * 100).toFixed(2)}%` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--ink-muted)' }}>
            n={sC06?.n_specific.toLocaleString()} / {sC06?.n_eligible.toLocaleString()} (Downstream|Upstream)
          </div>
        </div>
        <div className="kpi-card">
          <div className="meta-label">Confidence Risk (0.60, 2 folds)</div>
          <div className="kpi-value">
            {conf06 ? `${(conf06.selective_risk * 100).toFixed(2)}%` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--ink-muted)' }}>
            26 families · rank-matched coverage
          </div>
        </div>
        <div className="kpi-card">
          <div className="meta-label">Center Max Coverage</div>
          <div className="kpi-value">25.8%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--ink-muted)' }}>
            Fold 1 NOT_ESTIMABLE at 0.60 / 0.80 / 0.90
          </div>
        </div>
        <div className="kpi-card">
          <div className="meta-label">Registered RQ1 / H1</div>
          <div className="kpi-value" style={{ fontSize: '1.15rem', color: '#B45309' }}>
            NOT ESTIMABLE
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--ink-muted)' }}>
            Run {metrics.run_key.slice(0, 12)}
          </div>
        </div>
      </section>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--ink-secondary)' }}>
          Topology Fold Scope:
        </span>
        {(['pooled', 'Downstream', 'Upstream', 'Center'] as const).map((sc) => (
          <button
            key={sc}
            type="button"
            className={`seg-btn ${scope === sc ? 'active' : ''}`}
            onClick={() => setScope(sc)}
          >
            {sc} ({metrics.confusion_matrices_by_scope[sc]?.total_windows.toLocaleString()})
          </button>
        ))}
      </div>

      <section className="charts-grid">
        <div className="panel" style={{ padding: 14 }}>
          <h3 className="panel-title" style={{ marginBottom: 10 }}>
            Confusion Matrix — {scope} (n={cm.total_windows.toLocaleString()})
          </h3>
          {asTable ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>True \ Pred</th>
                  {cm.labels.map((lbl) => (
                    <th key={lbl}>{lbl}</th>
                  ))}
                  <th>Support</th>
                </tr>
              </thead>
              <tbody>
                {cm.labels.map((rowLbl, rIdx) => (
                  <tr key={rowLbl}>
                    <td><strong>{rowLbl}</strong></td>
                    {cm.matrix[rIdx].map((val, cIdx) => (
                      <td key={cIdx} className="mono">{val}</td>
                    ))}
                    <td className="mono">{cm.supports[rIdx]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <ConfusionHeatmap labels={cm.labels} matrix={cm.matrix} />
          )}
        </div>

        <div className="panel" style={{ padding: 14 }}>
          <h3 className="panel-title" style={{ marginBottom: 10 }}>
            Risk–Coverage Curve — {scope} {features.baseline_comparison ? '(vs. Baseline)' : ''}
          </h3>
          {asTable ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Target</th>
                  <th>Coverage</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {metrics.matched_coverage_06.map((pt) => (
                  <tr key={pt.method}>
                    <td className="mono">{pt.method}</td>
                    <td className="mono">{(pt.target_coverage * 100).toFixed(0)}%</td>
                    <td className="mono">{(pt.coverage * 100).toFixed(2)}%</td>
                    <td className="mono">{(pt.selective_risk * 100).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <RiskCoverageChart metrics={metrics} scope={scope} />
          )}
        </div>
      </section>

      <section className="panel" style={{ padding: 14 }}>
        <h3 className="panel-title" style={{ marginBottom: 10 }}>
          Per-Class Three-Outcome Breakdown (s_C, Target 0.60, Downstream | Upstream)
        </h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Class</th>
              <th>Windows (n)</th>
              <th>Runs / Families</th>
              <th>SPECIFIC (Correct)</th>
              <th>AMBIGUITY_SET (Includes True)</th>
              <th>UNRESOLVED</th>
            </tr>
          </thead>
          <tbody>
            {metrics.three_outcome_by_class
              .filter((r) => r.scope === 'POOLED_ESTIMABLE')
              .map((r) => (
                <tr key={r.class}>
                  <td><strong>{r.class}</strong></td>
                  <td className="mono">{r.n_windows.toLocaleString()}</td>
                  <td className="mono">{r.n_runs} / {r.n_families}</td>
                  <td className="mono">{r.n_specific.toLocaleString()} ({r.n_specific_correct.toLocaleString()})</td>
                  <td className="mono">{r.n_ambiguity_set} ({r.n_ambiguity_includes_true})</td>
                  <td className="mono">{r.n_unresolved.toLocaleString()}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>

      <section className="kpi-grid" aria-label="Feature availability gates">
        <div className="kpi-card">
          <div className="meta-label">Leak Localization</div>
          <div className="meta-value" style={{ color: 'var(--ink-muted)' }}>
            {features.localization ? 'Enabled' : 'Not available (unevaluable)'}
          </div>
          <div style={{ fontSize: '0.76rem', color: 'var(--ink-muted)', marginTop: 4 }}>
            Physical sensor coordinates &amp; meter-level truth are absent in H2-SimNet.
          </div>
        </div>
        <div className="kpi-card">
          <div className="meta-label">Gas Composition Comparison</div>
          <div className="meta-value" style={{ color: 'var(--ink-muted)' }}>
            {features.gas_comparison ? 'Enabled' : 'Not available (unsupported)'}
          </div>
          <div style={{ fontSize: '0.76rem', color: 'var(--ink-muted)', marginTop: 4 }}>
            Center model uses air-like R=0.287 kJ/(kg·K); H2/CH4 blend transfer unvalidated.
          </div>
        </div>
        <div className="kpi-card">
          <div className="meta-label">Operating-Condition Analysis</div>
          <div className="meta-value" style={{ color: 'var(--ink-muted)' }}>
            {features.operating_condition_analysis ? 'Enabled' : 'Not available (confounded)'}
          </div>
          <div style={{ fontSize: '0.76rem', color: 'var(--ink-muted)', marginTop: 4 }}>
            Not separately evaluated under the frozen primary R2 protocol.
          </div>
        </div>
      </section>
    </main>
  );
}
