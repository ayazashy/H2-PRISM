import { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { MetricsV1, SupportedFeatures } from '../data/types';

interface BenchmarksViewProps {
  metrics: MetricsV1 | null;
  features: SupportedFeatures;
}

function ConfusionHeatmap({ metrics }: { metrics: MetricsV1 }) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const { labels, matrix } = metrics.confusion_matrix;
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
          `True: <b>${labels[p.value[1]]}</b><br/>Pred: <b>${labels[p.value[0]]}</b><br/>Count: <b>${p.value[2]}</b>`,
      },
      grid: { left: 82, right: 20, top: 20, bottom: 48 },
      xAxis: {
        type: 'category',
        data: labels,
        name: 'Predicted',
        nameLocation: 'middle',
        nameGap: 28,
        axisLabel: { fontSize: 11, color: '#3D5166' },
      },
      yAxis: {
        type: 'category',
        data: labels,
        inverse: true,
        axisLabel: { fontSize: 11, color: '#3D5166' },
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
          label: { show: true, fontWeight: 700, fontSize: 13 },
        },
      ],
    });

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(ref.current);
    return () => {
      ro.disconnect();
      chart.dispose();
    };
  }, [metrics]);

  return <div ref={ref} style={{ width: '100%', height: 240 }} />;
}

function RiskCoverageChart({
  metrics,
  showBaseline,
}: {
  metrics: MetricsV1;
  showBaseline: boolean;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const series: Record<string, unknown>[] = [
      {
        name: 'H2-PRISM Selective Risk',
        type: 'line',
        smooth: false,
        symbolSize: 7,
        itemStyle: { color: '#0E3F3C' },
        lineStyle: { width: 2.5, color: '#0E3F3C' },
        data: metrics.risk_coverage.map((p) => [p.coverage * 100, p.h2_prism_risk * 100]),
      },
    ];
    if (showBaseline) {
      series.push({
        name: 'Baseline Confidence Risk',
        type: 'line',
        smooth: false,
        symbolSize: 7,
        itemStyle: { color: '#B45309' },
        lineStyle: { width: 2, type: 'dashed', color: '#B45309' },
        data: metrics.risk_coverage.map((p) => [
          p.coverage * 100,
          p.baseline_risk !== null ? p.baseline_risk * 100 : null,
        ]),
      });
    }

    chart.setOption({
      tooltip: { trigger: 'axis', valueFormatter: (v: unknown) => `${Number(v).toFixed(1)}%` },
      legend: { top: 0, textStyle: { fontSize: 11, color: '#3D5166' } },
      grid: { left: 50, right: 20, top: 34, bottom: 40 },
      xAxis: {
        type: 'value',
        name: 'Coverage (%)',
        nameLocation: 'middle',
        nameGap: 24,
        min: 0,
        max: 100,
      },
      yAxis: {
        type: 'value',
        name: 'Risk (%)',
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
  }, [metrics, showBaseline]);

  return <div ref={ref} style={{ width: '100%', height: 240 }} />;
}

export function BenchmarksView({ metrics, features }: BenchmarksViewProps) {
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

  return (
    <main className="benchmarks-page">
      <div
        className="hint-strip"
        style={{ borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}
      >
        <span>
          <strong>Split:</strong> {metrics.split} · <strong>Cohort N:</strong> {metrics.cohort_n} ·{' '}
          <strong>CI:</strong> {metrics.ci_method}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="mono">artifact: {metrics.artifact_hash}</span>
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
          <div className="meta-label">Decision Coverage</div>
          <div className="kpi-value">{(metrics.summary.coverage * 100).toFixed(1)}%</div>
        </div>
        <div className="kpi-card">
          <div className="meta-label">Selective Risk (on Covered)</div>
          <div className="kpi-value">{(metrics.summary.selective_risk * 100).toFixed(1)}%</div>
        </div>
        <div className="kpi-card">
          <div className="meta-label">False Physical Attribution (FPAR)</div>
          <div className="kpi-value">{(metrics.summary.fpar * 100).toFixed(1)}%</div>
        </div>
        <div className="kpi-card">
          <div className="meta-label">Leak Recall</div>
          <div className="kpi-value">{(metrics.summary.leak_recall * 100).toFixed(1)}%</div>
        </div>
      </section>

      <section className="charts-grid">
        <div className="panel" style={{ padding: 14 }}>
          <h3 className="panel-title" style={{ marginBottom: 10 }}>
            Per-Class Confusion &amp; Support
          </h3>
          {asTable ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>True \ Pred</th>
                  {metrics.confusion_matrix.labels.map((lbl) => (
                    <th key={lbl}>{lbl}</th>
                  ))}
                  <th>Support (n)</th>
                </tr>
              </thead>
              <tbody>
                {metrics.confusion_matrix.labels.map((rowLbl, rIdx) => (
                  <tr key={rowLbl}>
                    <td><strong>{rowLbl}</strong></td>
                    {metrics.confusion_matrix.matrix[rIdx].map((val, cIdx) => (
                      <td key={cIdx} className="mono">{val}</td>
                    ))}
                    <td className="mono">{metrics.confusion_matrix.supports[rIdx]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <ConfusionHeatmap metrics={metrics} />
          )}
        </div>

        <div className="panel" style={{ padding: 14 }}>
          <h3 className="panel-title" style={{ marginBottom: 10 }}>
            Abstention Risk–Coverage {features.baseline_comparison ? '(vs. Baseline)' : ''}
          </h3>
          {asTable ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Coverage</th>
                  <th>H2-PRISM Risk</th>
                  {features.baseline_comparison && <th>Baseline Risk</th>}
                </tr>
              </thead>
              <tbody>
                {metrics.risk_coverage.map((pt) => (
                  <tr key={pt.coverage}>
                    <td className="mono">{(pt.coverage * 100).toFixed(0)}%</td>
                    <td className="mono">{(pt.h2_prism_risk * 100).toFixed(1)}%</td>
                    {features.baseline_comparison && (
                      <td className="mono">
                        {pt.baseline_risk !== null ? `${(pt.baseline_risk * 100).toFixed(1)}%` : 'N/A'}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <RiskCoverageChart
              metrics={metrics}
              showBaseline={features.baseline_comparison}
            />
          )}
        </div>
      </section>
    </main>
  );
}
