import { FileSearch } from 'lucide-react';
import type { CatalogScenarioEntry, ProvenanceStatus } from '../data/types';

interface TopBarProps {
  scenarios: CatalogScenarioEntry[];
  selectedId: string;
  onSelectScenario: (id: string) => void;
  activeTab: 'workspace' | 'benchmarks' | 'methods';
  onChangeTab: (tab: 'workspace' | 'benchmarks' | 'methods') => void;
  onOpenEvidence: () => void;
  provenanceStatus?: ProvenanceStatus;
}

export function TopBar({
  scenarios,
  selectedId,
  onSelectScenario,
  activeTab,
  onChangeTab,
  onOpenEvidence,
  provenanceStatus,
}: TopBarProps) {
  const isFixture = provenanceStatus === 'FIXTURE_ONLY';

  return (
    <header className="topbar">
      <div className="topbar-brand">
        <span className="brand-title">H2-PRISM</span>
        <span className={`replay-pill ${isFixture ? 'fixture' : ''}`}>
          {isFixture ? 'Fixture Only · Replay' : 'Simulation Replay · Audited'}
        </span>
      </div>

      <div className="topbar-controls">
        <label htmlFor="scenario-select" style={{ position: 'absolute', left: '-9999px' }}>
          Select scenario
        </label>
        <select
          id="scenario-select"
          className="scenario-select"
          value={selectedId}
          onChange={(e) => onSelectScenario(e.target.value)}
        >
          {scenarios.map((s) => (
            <option key={s.id} value={s.id}>
              {s.display_name} ({s.scenario_class})
            </option>
          ))}
        </select>

        <nav className="nav-tabs" aria-label="Primary views">
          <button
            type="button"
            className={`nav-tab ${activeTab === 'workspace' ? 'active' : ''}`}
            onClick={() => onChangeTab('workspace')}
          >
            Workspace
          </button>
          <button
            type="button"
            className={`nav-tab ${activeTab === 'benchmarks' ? 'active' : ''}`}
            onClick={() => onChangeTab('benchmarks')}
          >
            Benchmarks
          </button>
          <button
            type="button"
            className={`nav-tab ${activeTab === 'methods' ? 'active' : ''}`}
            onClick={() => onChangeTab('methods')}
          >
            Methods &amp; Limits
          </button>
        </nav>

        <button type="button" className="btn-outline-light" onClick={onOpenEvidence}>
          <FileSearch size={15} />
          Evidence
        </button>
      </div>
    </header>
  );
}
