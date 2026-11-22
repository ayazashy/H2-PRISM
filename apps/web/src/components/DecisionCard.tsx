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
              <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {model_result.reason_code}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {model_result.reason_summary}
            </p>
          </>
        ) : (
          <>
            <div className="decision-row">
              <span className="decision-badge UNRESOLVED">
                <Info size={15} />
                PER-RUN INFERENCE NOT EXPORTED
              </span>
              <button type="button" className="seg-btn" onClick={onOpenBenchmarks}>
                View R2 Benchmarks
              </button>
            </div>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              This replay displays verified <span className="mono">{scenario.source_artifact}</span>{' '}
              telemetry and ground truth only. No fabricated per-run score is shown.
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

          <div className="meta-box" style={{ borderColor: 'rgba(220, 119, 108, 0.45)' }}>
            <div className="meta-label" style={{ color: 'var(--state-event)' }}>
              Ground Truth ({event.label_status})
            </div>
            <div className="meta-value">
              {event.ground_truth_class}
              {event.onset_time !== null && (
                <span
                  className="mono"
                  style={{
                    display: 'block',
                    fontSize: '11.5px',
                    fontWeight: 500,
                    color: 'var(--text-secondary)',
                    marginTop: 2,
                  }}
                >
                  [{event.onset_time.toFixed(0)}s,{' '}
                  {(event.end_time ?? scenario.time_seconds[scenario.time_seconds.length - 1])?.toFixed(0)}s]
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
                <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
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
