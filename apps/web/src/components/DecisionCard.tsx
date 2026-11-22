import { AlertTriangle, CheckCircle2, HelpCircle, Info } from 'lucide-react';
import type { ScenarioPayloadV1, SupportedFeatures } from '../data/types';

interface DecisionCardProps {
  scenario: ScenarioPayloadV1;
  features: SupportedFeatures;
  timeIndex: number;
  onOpenBenchmarks: () => void;
}

export function DecisionCard({
  scenario,
  features,
  timeIndex,
  onOpenBenchmarks,
}: DecisionCardProps) {
  const { model_result, event, location_prediction } = scenario;
  const currentT = scenario.time_seconds[timeIndex] ?? 0;

  let phaseLabel = 'Nominal Run';
  let phaseClass = 'nominal';
  if (event.onset_time !== null) {
    if (currentT < event.onset_time) {
      phaseLabel = 'Pre-Onset Baseline';
      phaseClass = 'pre';
    } else if (event.end_time !== null && currentT > event.end_time) {
      phaseLabel = 'Post-Event Recovery';
      phaseClass = 'pre';
    } else {
      phaseLabel = 'Active Event Window';
      phaseClass = 'post';
    }
  }

  const decision = model_result?.decision ?? null;
  const Icon =
    decision === 'SPECIFIC'
      ? CheckCircle2
      : decision === 'AMBIGUOUS'
      ? AlertTriangle
      : decision === 'UNRESOLVED'
      ? HelpCircle
      : Info;

  return (
    <section className="panel" aria-label="Model decision and ground truth">
      <div className="panel-header">
        <h2 className="panel-title">Diagnostic Decision</h2>
        <span className={`phase-pill ${phaseClass}`}>{phaseLabel}</span>
      </div>

      <div className="decision-body">
        {model_result ? (
          <>
            <div className="decision-row">
              <span className={`decision-badge ${model_result.decision}`}>
                <Icon size={15} />
                {model_result.decision}
              </span>
              <span className="mono" title="Reason code">
                {model_result.reason_code}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--ink-secondary)', lineHeight: 1.45 }}>
              {model_result.reason_summary}
            </p>
          </>
        ) : (
          <>
            <div className="decision-row">
              <span className="decision-badge UNRESOLVED">
                <Info size={15} />
                EVIDENCE UNAVAILABLE (PER-RUN INFERENCE NOT EXPORTED)
              </span>
              <button type="button" className="seg-btn" onClick={onOpenBenchmarks}>
                View R2 Benchmarks
              </button>
            </div>
            <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--ink-secondary)', lineHeight: 1.45 }}>
              This replay exposes verified <span className="mono">{scenario.source_artifact}</span> sensor
              telemetry and audited ground truth only. No fabricated per-run score is shown.
            </p>
          </>
        )}

        <div className="decision-meta-grid">
          <div className="meta-box">
            <div className="meta-label">Model Prediction</div>
            <div className="meta-value">
              {model_result
                ? model_result.predicted_class ?? 'No specific event justified'
                : 'Evidence unavailable'}
            </div>
          </div>

          <div className="meta-box" style={{ borderColor: 'rgba(185, 28, 28, 0.25)' }}>
            <div className="meta-label" style={{ color: 'var(--truth-accent)' }}>
              Ground Truth ({event.label_status})
            </div>
            <div className="meta-value">
              {event.ground_truth_class}
              {event.onset_time !== null && (
                <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 500, color: 'var(--ink-muted)' }}>
                  Window: [{event.onset_time.toFixed(0)}s, {(event.end_time ?? scenario.time_seconds[scenario.time_seconds.length - 1])?.toFixed(0)}s]
                </span>
              )}
            </div>
          </div>

          <div className="meta-box">
            <div className="meta-label">
              {model_result?.score_definition ?? 'Selective Score'}
            </div>
            <div className="meta-value mono">
              {model_result && model_result.score !== null
                ? model_result.score.toFixed(3)
                : 'Not available'}
            </div>
          </div>

          <div className="meta-box">
            <div className="meta-label">Localization</div>
            <div className="meta-value">
              {features.localization && location_prediction ? (
                <span>
                  {location_prediction.predicted_edge_or_node}
                  {location_prediction.error_value !== null
                    ? ` (${location_prediction.error_value} ${location_prediction.error_unit ?? ''})`
                    : ''}
                </span>
              ) : (
                <span style={{ color: 'var(--ink-muted)', fontWeight: 500 }}>
                  Location not evaluated
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
