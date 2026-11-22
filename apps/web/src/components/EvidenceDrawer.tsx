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
            <div>gas_metadata: {entry.gas_metadata_status}</div>
          </div>
        </div>

        {scenario && (
          <div className="meta-box">
            <div className="meta-label">Model Artifact Provenance</div>
            <div className="mono" style={{ fontSize: '0.78rem', lineHeight: 1.5 }}>
              <div>experiment_id: {scenario.model_result.experiment_id}</div>
              <div>model_version: {scenario.model_result.model_version}</div>
              <div>artifact_hash: {scenario.model_result.artifact_hash}</div>
              <div>reason_code: {scenario.model_result.reason_code}</div>
            </div>
          </div>
        )}

        <div>
          <h3 style={{ fontSize: '0.88rem', margin: '0 0 6px' }}>Tri-State Decision Semantics</h3>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.83rem', color: 'var(--ink-secondary)', lineHeight: 1.5 }}>
            <li><strong>SPECIFIC</strong>: Evidence supports a single event class above the calibrated abstention threshold.</li>
            <li><strong>AMBIGUOUS</strong>: Anomaly detected, but competing hypotheses (e.g., overlapping leaks or transient vs. leak) cannot be separated.</li>
            <li><strong>UNRESOLVED</strong>: Insufficient or conflicting evidence; model abstains rather than guessing.</li>
          </ul>
        </div>

        <div>
          <h3 style={{ fontSize: '0.88rem', margin: '0 0 6px' }}>Scientific Scope &amp; Limitations</h3>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.83rem', color: 'var(--ink-secondary)', lineHeight: 1.5 }}>
            <li>Replays saved H2-SimNet simulation runs; not a live industrial SCADA feed.</li>
            <li>Network geometry is a schematic representation; physical sensor coordinates and pipe lengths are not verified in the audited dataset.</li>
            <li>Temperature, density, and flow velocity are not directly measured channels.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
