import { X } from 'lucide-react';
import type { CatalogScenarioEntry, CatalogV1, ScenarioPayloadV1 } from '../data/types';

interface EvidenceDrawerProps {
  open: boolean;
  onClose: () => void;
  catalog: CatalogV1;
  entry: CatalogScenarioEntry;
  scenario: ScenarioPayloadV1 | null;
}

export function EvidenceDrawer({ open, onClose, catalog, entry, scenario }: EvidenceDrawerProps) {
  if (!open) return null;

  return (
    <div className="drawer-backdrop" role="dialog" aria-modal="true" aria-label="Evidence and provenance">
      <div className="drawer-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ margin: 0, fontSize: '1.05rem' }}>Evidence, Provenance &amp; Limits</h2>
          <button type="button" className="seg-btn" onClick={onClose} aria-label="Close drawer">
            <X size={16} />
          </button>
        </div>

        <div className="meta-box">
          <div className="meta-label">Release &amp; Integrity</div>
          <div className="mono" style={{ fontSize: '0.78rem', lineHeight: 1.5 }}>
            <div>release_id: {catalog.release_id}</div>
            <div>commit: {catalog.source_repository_commit}</div>
            <div>scenario_sha256: {entry.sha256.slice(0, 16)}…</div>
            <div>split: {entry.split} · family: {entry.family_id}</div>
            <div>provenance: {entry.provenance_status}</div>
          </div>
        </div>

        {scenario && (
          <div className="meta-box">
            <div className="meta-label">Scenario Source &amp; Projection</div>
            <div className="mono" style={{ fontSize: '0.78rem', lineHeight: 1.5 }}>
              <div>source: {scenario.source_artifact}</div>
              <div>{scenario.decimation_note}</div>
            </div>
          </div>
        )}

        <div className="meta-box">
          <div className="meta-label">Per-Run Model Artifact Provenance</div>
          {scenario?.model_result ? (
            <div className="mono" style={{ fontSize: '0.78rem', lineHeight: 1.5 }}>
              <div>experiment_id: {scenario.model_result.experiment_id}</div>
              <div>model_version: {scenario.model_result.model_version}</div>
              <div>artifact_hash: {scenario.model_result.artifact_hash}</div>
              <div>reason_code: {scenario.model_result.reason_code}</div>
            </div>
          ) : (
            <div style={{ fontSize: '0.8rem', color: 'var(--ink-secondary)', lineHeight: 1.45 }}>
              Per-run window predictions are not included in this sample recording export.
              See the <strong>Benchmarks</strong> view for Primary R2 LOTO evaluation results
              (<span className="mono">a10530f1fcf2</span>).
            </div>
          )}
        </div>

        <div>
          <h3 style={{ fontSize: '0.88rem', margin: '0 0 6px' }}>Tri-State Decision Semantics</h3>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.83rem', color: 'var(--ink-secondary)', lineHeight: 1.5 }}>
            <li><strong>SPECIFIC</strong>: Evidence supports a single event class above the calibrated threshold.</li>
            <li><strong>AMBIGUOUS</strong>: Anomaly detected, but competing hypotheses cannot be separated.</li>
            <li><strong>UNRESOLVED</strong>: Insufficient or out-of-support evidence; model abstains safely.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
