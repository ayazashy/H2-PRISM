import { Suspense, lazy, useCallback, useEffect, useState } from 'react';
import { BenchmarksView } from './components/BenchmarksView';
import { DecisionCard } from './components/DecisionCard';
import { EvidenceDrawer } from './components/EvidenceDrawer';
import { MethodsView } from './components/MethodsView';
import { NetworkSchematic2D } from './components/NetworkSchematic2D';
import { PlaybackBar } from './components/PlaybackBar';
import { ReleaseFooter } from './components/ReleaseFooter';
import { SignalCharts } from './components/SignalCharts';
import { TopBar } from './components/TopBar';
import {
  loadCatalog,
  loadMetricsVerified,
  loadScenarioVerified,
  loadTopology,
} from './data/loader';
import type {
  CatalogV1,
  MetricsV1,
  ScenarioPayloadV1,
  TopologyV1,
} from './data/types';

const NetworkScene3D = lazy(() =>
  import('./components/NetworkScene3D').then((m) => ({ default: m.NetworkScene3D }))
);

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export function App() {
  const [catalog, setCatalog] = useState<CatalogV1 | null>(null);
  const [classFilter, setClassFilter] = useState<string>('ALL');
  const [selectedId, setSelectedId] = useState<string>('');
  const [topology, setTopology] = useState<TopologyV1 | null>(null);
  const [scenario, setScenario] = useState<ScenarioPayloadV1 | null>(null);
  const [metrics, setMetrics] = useState<MetricsV1 | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'workspace' | 'benchmarks' | 'methods'>('workspace');
  const [networkMode, setNetworkMode] = useState<'2d' | '3d'>('2d');
  const [showTruthLayer, setShowTruthLayer] = useState(false);
  const [showSymbolicFlow, setShowSymbolicFlow] = useState(() => !prefersReducedMotion());
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null);
  const [timeIndex, setTimeIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [evidenceOpen, setEvidenceOpen] = useState(false);

  const handleTogglePlay = useCallback(() => setIsPlaying((p) => !p), []);
  const handleStopPlay = useCallback(() => setIsPlaying(false), []);

  useEffect(() => {
    const ac = new AbortController();
    loadCatalog(ac.signal)
      .then((cat) => {
        setCatalog(cat);
        setSelectedId(cat.scenarios[0].id);
        if (cat.metrics_catalog.length > 0) {
          loadMetricsVerified(cat.metrics_catalog[0], ac.signal)
            .then(setMetrics)
            .catch(() => setMetrics(null));
        }
      })
      .catch((err: unknown) => {
        if (ac.signal.aborted) return;
        setError(err instanceof Error ? err.message : 'Failed to load catalog.');
      });
    return () => ac.abort();
  }, []);

  useEffect(() => {
    if (!catalog || !selectedId) return;
    const entry = catalog.scenarios.find((s) => s.id === selectedId);
    if (!entry) return;

    const ac = new AbortController();
    setError(null);
    setIsPlaying(false);
    setTimeIndex(0);
    setSelectedChannelId(null);

    loadTopology(entry.topology_id, ac.signal)
      .then(async (topo) => {
        const scen = await loadScenarioVerified(
          entry,
          topo,
          catalog.supported_features.localization,
          ac.signal
        );
        if (ac.signal.aborted) return;
        setTopology(topo);
        setScenario(scen);
      })
      .catch((err: unknown) => {
        if (ac.signal.aborted) return;
        setScenario(null);
        setError(err instanceof Error ? err.message : 'Integrity error loading scenario.');
      });

    return () => ac.abort();
  }, [catalog, selectedId]);

  if (error && !catalog) {
    return (
      <div className="integrity-error" role="alert">
        <h2>Integrity Check Failed — Diagnostics Disabled</h2>
        <p style={{ margin: 0 }}>{error}</p>
      </div>
    );
  }

  if (!catalog) {
    return (
      <div style={{ padding: 24, color: 'var(--ink-secondary)' }}>
        Loading verified catalog…
      </div>
    );
  }

  const filteredScenarios =
    classFilter === 'ALL'
      ? catalog.scenarios
      : catalog.scenarios.filter((s) => s.scenario_class === classFilter);

  const activeEntry =
    catalog.scenarios.find((s) => s.id === selectedId) ?? catalog.scenarios[0];

  const handleFilterChange = (cls: string) => {
    setClassFilter(cls);
    const nextList =
      cls === 'ALL'
        ? catalog.scenarios
        : catalog.scenarios.filter((s) => s.scenario_class === cls);
    if (nextList.length > 0 && !nextList.some((s) => s.id === selectedId)) {
      setSelectedId(nextList[0].id);
    }
  };

  const handleResetWorkspace = () => {
    setIsPlaying(false);
    setTimeIndex(0);
    setSelectedChannelId(null);
    setShowTruthLayer(false);
  };

  return (
    <div className="app-shell">
      <TopBar
        scenarios={filteredScenarios}
        selectedId={selectedId}
        onSelectScenario={setSelectedId}
        activeTab={activeTab}
        onChangeTab={setActiveTab}
        onOpenEvidence={() => setEvidenceOpen(true)}
        provenanceStatus={activeEntry.provenance_status}
      />

      <div className="hint-strip">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span>
            <strong>{activeEntry.display_name}:</strong> {activeEntry.summary_hint}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          {(['ALL', ...catalog.label_set] as const).map((cls) => (
            <button
              key={cls}
              type="button"
              className={`seg-btn ${classFilter === cls ? 'active' : ''}`}
              style={{ fontSize: '0.72rem', padding: '2px 7px' }}
              onClick={() => handleFilterChange(cls)}
            >
              {cls}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="integrity-error" role="alert">
          <h2>Scenario Integrity Failure — Diagnostics Disabled</h2>
          <p style={{ margin: 0 }}>{error}</p>
        </div>
      ) : activeTab === 'benchmarks' ? (
        <BenchmarksView metrics={metrics} features={catalog.supported_features} />
      ) : activeTab === 'methods' ? (
        <MethodsView catalog={catalog} metrics={metrics} />
      ) : scenario && topology ? (
        <>
          <main className="workspace-main">
            <section className="panel" aria-label="Gas network topology">
              <div className="panel-header">
                <h2 className="panel-title">Network Topology</h2>
                <div className="network-toolbar">
                  <button
                    type="button"
                    className={`seg-btn ${networkMode === '2d' ? 'active' : ''}`}
                    onClick={() => setNetworkMode('2d')}
                  >
                    2D Schematic
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${networkMode === '3d' ? 'active' : ''}`}
                    onClick={() => setNetworkMode('3d')}
                  >
                    3D View
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${showSymbolicFlow ? 'active' : ''}`}
                    onClick={() => setShowSymbolicFlow((v) => !v)}
                    title="Toggle symbolic gas flow direction (not measured fluid velocity)"
                  >
                    {showSymbolicFlow ? 'Symbolic Flow: On' : 'Symbolic Flow: Off'}
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${showTruthLayer ? 'active' : ''}`}
                    onClick={() => setShowTruthLayer((v) => !v)}
                  >
                    {showTruthLayer ? 'Hide Ground Truth' : 'Show Ground Truth'}
                  </button>
                  <button type="button" className="seg-btn" onClick={handleResetWorkspace}>
                    Reset
                  </button>
                </div>
              </div>

              <div className="network-stage">
                {topology.is_schematic && (
                  <div className="schematic-badge">
                    Schematic · Not to Physical Scale
                    {showSymbolicFlow ? ' · Symbolic Flow (not velocity)' : ''}
                  </div>
                )}
                {networkMode === '2d' ? (
                  <NetworkSchematic2D
                    topology={topology}
                    scenario={scenario}
                    features={catalog.supported_features}
                    timeIndex={timeIndex}
                    isPlaying={isPlaying}
                    speed={speed}
                    showSymbolicFlow={showSymbolicFlow}
                    selectedChannelId={selectedChannelId}
                    onSelectChannel={setSelectedChannelId}
                    showTruthLayer={showTruthLayer}
                  />
                ) : (
                  <Suspense fallback={<div style={{ padding: 24 }}>Loading 3D renderer…</div>}>
                    <NetworkScene3D
                      topology={topology}
                      scenario={scenario}
                      features={catalog.supported_features}
                      timeIndex={timeIndex}
                      isPlaying={isPlaying}
                      speed={speed}
                      showSymbolicFlow={showSymbolicFlow}
                      selectedChannelId={selectedChannelId}
                      onSelectChannel={setSelectedChannelId}
                      showTruthLayer={showTruthLayer}
                    />
                  </Suspense>
                )}
              </div>

              <div className="network-legend">
                <span>
                  Click any sensor to isolate its curve · Space: Play/Pause · O: Jump to Onset
                </span>
                <span>
                  {selectedChannelId ? `Focused: ${selectedChannelId}` : 'All observable channels plotted'}
                </span>
              </div>
            </section>

            <div className="right-stack">
              <DecisionCard
                scenario={scenario}
                features={catalog.supported_features}
                timeIndex={timeIndex}
                onOpenBenchmarks={() => setActiveTab('benchmarks')}
              />
              <SignalCharts
                scenario={scenario}
                timeIndex={timeIndex}
                onChangeTimeIndex={setTimeIndex}
                selectedChannelId={selectedChannelId}
              />
            </div>
          </main>

          <PlaybackBar
            timeSeconds={scenario.time_seconds}
            timeIndex={timeIndex}
            onChangeTimeIndex={setTimeIndex}
            isPlaying={isPlaying}
            onTogglePlay={handleTogglePlay}
            onStopPlay={handleStopPlay}
            speed={speed}
            onChangeSpeed={setSpeed}
            onsetTime={scenario.event.onset_time}
          />
        </>
      ) : (
        <div style={{ padding: 24, color: 'var(--ink-secondary)' }}>
          Validating SHA-256 integrity &amp; loading scenario…
        </div>
      )}

      <ReleaseFooter
        catalog={catalog}
        activeEntry={activeEntry}
        onOpenMethods={() => setActiveTab('methods')}
      />

      <EvidenceDrawer
        open={evidenceOpen}
        onClose={() => setEvidenceOpen(false)}
        catalog={catalog}
        entry={activeEntry}
        scenario={scenario}
      />
    </div>
  );
}
export default App;
