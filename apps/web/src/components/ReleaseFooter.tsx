import type { CatalogScenarioEntry, CatalogV1 } from '../data/types';

interface ReleaseFooterProps {
  catalog: CatalogV1;
  activeEntry: CatalogScenarioEntry;
  onOpenMethods: () => void;
}

export function ReleaseFooter({ catalog, activeEntry, onOpenMethods }: ReleaseFooterProps) {
  return (
    <footer
      style={{
        background: 'var(--bg-subtle)',
        borderTop: '1px solid var(--border-subtle)',
        padding: '7px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        flexWrap: 'wrap',
        fontSize: '0.75rem',
        color: 'var(--ink-muted)',
      }}
    >
      <div className="mono">
        release: {catalog.release_id} · sha256: {catalog.data_release_checksum.slice(0, 12)}… ·
        commit: {catalog.source_repository_commit} · scenario: {activeEntry.id} ({activeEntry.provenance_status})
      </div>
      <button
        type="button"
        className="seg-btn"
        style={{ padding: '2px 8px', fontSize: '0.74rem' }}
        onClick={onOpenMethods}
      >
        Methods &amp; Limitations
      </button>
    </footer>
  );
}
