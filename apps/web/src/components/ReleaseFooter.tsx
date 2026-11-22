import type { CatalogScenarioEntry, CatalogV1 } from '../data/types';

interface ReleaseFooterProps {
  catalog: CatalogV1;
  activeEntry: CatalogScenarioEntry;
  onOpenMethods: () => void;
}

export function ReleaseFooter({ catalog, activeEntry, onOpenMethods }: ReleaseFooterProps) {
  return (
    <footer className="release-footer">
      <div className="mono" style={{ overflowWrap: 'anywhere' }}>
        release: {catalog.release_id} · sha256: {catalog.data_release_checksum.slice(0, 12)}… ·
        commit: {catalog.source_repository_commit} · scenario: {activeEntry.id} ({activeEntry.provenance_status})
      </div>
      <button
        type="button"
        className="seg-btn"
        style={{ minHeight: 28, padding: '2px 10px', fontSize: '12px' }}
        onClick={onOpenMethods}
      >
        Methods &amp; Limitations
      </button>
    </footer>
  );
}
