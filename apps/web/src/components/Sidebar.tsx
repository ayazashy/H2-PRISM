import { Activity, BarChart3, BookOpen, FileSearch, X } from 'lucide-react';
import type { CatalogV1 } from '../data/types';

export type NavTab = 'workspace' | 'benchmarks' | 'methods';

interface SidebarProps {
  activeTab: NavTab;
  onChangeTab: (tab: NavTab) => void;
  onOpenEvidence: () => void;
  catalog: CatalogV1;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

function SidebarContent({
  activeTab,
  onChangeTab,
  onOpenEvidence,
  catalog,
  onCloseMobile,
}: Omit<SidebarProps, 'mobileOpen'>) {
  const navItems: { id: NavTab; label: string; icon: typeof Activity }[] = [
    { id: 'workspace', label: 'Digital Twin', icon: Activity },
    { id: 'benchmarks', label: 'Benchmarks (R2)', icon: BarChart3 },
    { id: 'methods', label: 'Methods & Limits', icon: BookOpen },
  ];

  return (
    <>
      <div className="sidebar-brand">
        <div className="brand-mark">
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: 'var(--accent-primary)',
              display: 'inline-block',
            }}
          />
          H2-PRISM
        </div>
        <div className="brand-sub">Diagnostic Replay &amp; Evidence</div>
      </div>

      <nav className="sidebar-nav" aria-label="Primary navigation">
        <div className="sidebar-section-label">Views</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => {
                onChangeTab(item.id);
                onCloseMobile();
              }}
            >
              <Icon size={18} strokeWidth={1.9} />
              <span>{item.label}</span>
            </button>
          );
        })}

        <div className="sidebar-section-label" style={{ marginTop: 10 }}>
          Inspection
        </div>
        <button
          type="button"
          className="nav-item"
          onClick={() => {
            onCloseMobile();
            onOpenEvidence();
          }}
        >
          <FileSearch size={18} strokeWidth={1.9} />
          <span>Evidence &amp; Provenance</span>
        </button>
      </nav>

      <div className="sidebar-footer-card">
        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          Fail-Closed Integrity
        </div>
        <div className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
          {catalog.release_id}
        </div>
        <div style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>
          Localization: Not evaluated · Static replay only
        </div>
      </div>
    </>
  );
}

export function Sidebar(props: SidebarProps) {
  return (
    <>
      <aside className="sidebar" aria-label="Desktop navigation">
        <SidebarContent {...props} />
      </aside>

      {props.mobileOpen && (
        <div
          className="drawer-backdrop left"
          role="dialog"
          aria-modal="true"
          aria-label="Mobile navigation"
          onClick={props.onCloseMobile}
        >
          <div
            className="drawer-panel"
            style={{ width: 264, borderLeft: 'none', borderRight: '1px solid var(--border-default)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="button"
                className="seg-btn"
                aria-label="Close navigation"
                onClick={props.onCloseMobile}
              >
                <X size={16} />
              </button>
            </div>
            <SidebarContent {...props} />
          </div>
        </div>
      )}
    </>
  );
}
