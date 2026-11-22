import { AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react';
import type { ScenarioPayloadV1, SupportedFeatures } from '../data/types';

interface DecisionCardProps {
  scenario: ScenarioPayloadV1;
  features: SupportedFeatures;
  timeIndex: number;
}

export function DecisionCard({ scenario, features, timeIndex }: DecisionCardProps) {
  const { model_result, event, location_prediction } = scenario;
  const decision = model_result.decision;
  const currentT = scenario.time_seconds[timeIndex] ?? 0;
  const phaseLabel =
    event.onset_time === null
      ? 'Nominal Run'
      : currentT >= event.onset_time
      ? 'Post-Onset Window'
      : 'Pre-Onset Baseline';

  const Icon =
    decision === 'SPECIFIC'
      ? CheckCircle2
      : decision === 'AMBIGUOUS'
      ? AlertTriangle
      : HelpCircle;

  return (
    <section className="panel" aria-label="Model decision and ground truth">
      <div className="panel-header">
        <h2 className="panel-title">Diagnostic Decision</h2>
        <span
          className={`phase-pill ${
            event.onset_time === null
              ? 'nominal'
              : currentT >= event.onset_time
              ? 'post'
              : 'pre'
          }`}
        >
          {phaseLabel}
        </span>
      </div>

      <div className="decision-body">
        <div className="decision-row">
          <span className={`decision-badge ${decision}`}>
            <Icon size={15} />
            {decision}
          </span>
          <span className="mono" title="Reason code">
            {model_result.reason_code}
          </span>
        </div>

        <p style={{ margin: 0, fontSize: '0.86rem', color: 'var(--ink-secondary)', lineHeight: 1.45 }}>
          {model_result.reason_summary}
        </p>

        <div className="decision-meta-grid">
          <div className="meta-box">
            <div className="meta-label">Model Prediction</div>
            <div className="meta-value">
              {model_result.predicted_class ?? 'Abstained (no specific class)'}
            </div>
          </div>

          <div className="meta-box" style={{ borderColor: 'rgba(185, 28, 28, 0.25)' }}>
            <div className="meta-label" style={{ color: 'var(--truth-accent)' }}>
              Ground Truth ({event.label_status})
            </div>
            <div className="meta-value">{event.ground_truth_class}</div>
          </div>

          <div className="meta-box">
            <div className="meta-label">
              {model_result.score_definition ?? 'Selective Score'}
            </div>
            <div className="meta-value mono">
              {model_result.score !== null ? model_result.score.toFixed(3) : 'Not reported'}
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
