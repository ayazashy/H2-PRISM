import { FileSearch, Menu } from 'lucide-react';
import type { CatalogScenarioEntry, ProvenanceStatus } from '../data/types';
import type { NavTab } from './Sidebar';

interface TopBarProps {
  activeTab: NavTab;
  scenarios: CatalogScenarioEntry[];
  selectedId: string;
  onSelectScenario: (id: string) => void;
  onOpenEvidence: () => void;
  onOpenMobileNav: () => void;
  provenanceStatus?: ProvenanceStatus;
}

const TAB_TITLES: Record<NavTab, string> = {
  workspace: 'Digital Twin & Replay',
  benchmarks: 'Primary R2 Benchmarks',
  methods: 'Methods & Limitations',
};

export function TopBar({
  activeTab,
  scenarios,
  selectedId,
  onSelectScenario,
  onOpenEvidence,
  onOpenMobileNav,
  provenanceStatus,
}: TopBarProps) {
  const isFixture = provenanceStatus === 'FIXTURE_ONLY';

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="mobile-menu-btn"
          aria-label="Open navigation menu"
          onClick={onOpenMobileNav}
        >
          <Menu size={18} />
        </button>
        <h1 className="page-heading">{TAB_TITLES[activeTab]}</h1>
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

        <button type="button" className="btn-secondary" onClick={onOpenEvidence}>
          <FileSearch size={15} />
          Evidence
        </button>
      </div>
    </header>
  );
}
