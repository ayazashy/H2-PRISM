import type { CatalogV1, MetricsV1 } from '../data/types';

interface MethodsViewProps {
  catalog: CatalogV1;
  metrics: MetricsV1 | null;
}

export function MethodsView({ catalog, metrics }: MethodsViewProps) {
  return (
    <main className="benchmarks-page">
      <div className="panel" style={{ padding: 18 }}>
        <h2 style={{ margin: '0 0 8px', fontSize: '18px', fontWeight: 600 }}>
          Methods, Plain-English Glossary &amp; Research Limitations
        </h2>
        <p style={{ margin: 0, fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
          H2-PRISM replays audited simulation recordings and frozen Leave-One-Topology-Out (LOTO)
          experiments. It is a documented research demonstration—not a live industrial SCADA feed
          and not a general physics simulator.
        </p>
      </div>

      <section className="charts-grid">
        <div className="panel" style={{ padding: 16 }}>
          <h3 className="panel-title" style={{ marginBottom: 10 }}>
            Tri-State Selective Decision Glossary
          </h3>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: 1.65 }}>
            <li>
              <strong style={{ color: 'var(--accent-soft)' }}>SPECIFIC</strong>: Both calibrated class probability and empirical neighbor
              support <span className="mono">D(x)</span> exceed the development-selected threshold.
            </li>
            <li>
              <strong style={{ color: 'var(--state-warning)' }}>AMBIGUOUS</strong>: An operational anomaly is supported, but competing hypotheses
              (e.g., transient vs. leak) cannot be reliably separated; outputs a bounded candidate set.
            </li>
            <li>
              <strong style={{ color: 'var(--state-unresolved)' }}>UNRESOLVED</strong>: Out-of-support or conflicting evidence; the selective policy
              abstains rather than issuing an unsupported classification.
            </li>
            <li>
              <strong style={{ color: 'var(--text-primary)' }}>D(x) &amp; s_C</strong>: <span className="mono">D(x)</span> is a family-excluded
              nearest-neighbor support statistic (<span className="mono">k=25</span>), not a calibrated
              physical probability. <span className="mono">s_C</span> combines classifier evidence with{' '}
              <span className="mono">D(x)</span>.
            </li>
          </ul>
        </div>

        <div className="panel" style={{ padding: 16 }}>
          <h3 className="panel-title" style={{ marginBottom: 10 }}>
            Audited Dataset &amp; Protocol Limitations
          </h3>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: 1.65 }}>
            <li>
              <strong style={{ color: 'var(--text-primary)' }}>R-18 Attribution Finding</strong>: In the published H2-SimNet archive,{' '}
              <span className="mono">anom_gestcent</span> exports the 16-sensor Down-model signature
              (<span className="mono">PS11, PS12, MFS4</span> active), whereas{' '}
              <span className="mono">normality_gest_center</span> pads those 3 channels with constants.
            </li>
            <li>
              <strong style={{ color: 'var(--text-primary)' }}>Cross-Topology Estimand</strong>: Folds transfer across Center, Downstream, and
              Upstream topologies; base scenario families appear in multiple topologies, so results are
              not unseen-family validation.
            </li>
            <li>
              <strong style={{ color: 'var(--text-primary)' }}>Gas &amp; Sensor Scope</strong>: Center Simscape blocks use air-like properties (
              <span className="mono">R = 0.287 kJ/(kg·K)</span>). Temperature, density, and fluid
              velocity are not directly measured.
            </li>
          </ul>
        </div>
      </section>

      {metrics && (
        <section className="panel" style={{ padding: 16 }}>
          <h3 className="panel-title" style={{ marginBottom: 10 }}>
            Explicitly Prohibited Claims (Run {metrics.run_key.slice(0, 12)})
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {metrics.prohibited_claims.map((claim) => (
              <span
                key={claim}
                style={{
                  background: 'var(--state-event-bg)',
                  color: 'var(--state-event)',
                  border: '1px solid rgba(220, 119, 108, 0.4)',
                  borderRadius: 999,
                  padding: '4px 11px',
                  fontSize: '12px',
                  fontWeight: 600,
                }}
              >
                No claim of {claim}
              </span>
            ))}
          </div>
        </section>
      )}

      <section className="panel" style={{ padding: 16 }}>
        <h3 className="panel-title" style={{ marginBottom: 8 }}>
          Project Governance &amp; Provenance
        </h3>
        <div className="mono" style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.7, overflowWrap: 'anywhere' }}>
          <div>release_id: {catalog.release_id} · commit: {catalog.source_repository_commit}</div>
          <div>data_release_checksum: {catalog.data_release_checksum}</div>
          <div>roles: Research Lead (Ahmed Zayed) · Modeling &amp; UI (Faisal) · Dataset Readiness (Yazan)</div>
        </div>
      </section>
    </main>
  );
}
