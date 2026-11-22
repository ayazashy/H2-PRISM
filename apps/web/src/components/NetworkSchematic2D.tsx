import { useState } from 'react';
import type { ScenarioPayloadV1, SupportedFeatures, TopologyV1 } from '../data/types';

interface NetworkSchematic2DProps {
  topology: TopologyV1;
  scenario: ScenarioPayloadV1;
  features: SupportedFeatures;
  timeIndex: number;
  isPlaying: boolean;
  speed: number;
  showSymbolicFlow: boolean;
  selectedChannelId: string | null;
  onSelectChannel: (id: string | null) => void;
  showTruthLayer: boolean;
}

// Well-spaced schematic positions on a 900x400 canvas so zero nodes or labels overlap
const NODE_POS_2D: Record<string, [number, number]> = {
  N47: [80, 210],
  N50: [220, 210],
  N239: [360, 210],
  N309: [500, 210],
  N106: [625, 105],
  N221: [745, 210],
  N109: [625, 315],
  N195: [825, 315],
};

// Non-overlapping anchor offsets for small sensor marker pills
const SENSOR_PIN_POS: Record<string, [number, number]> = {
  PS7: [80, 152],
  PS1: [220, 152],
  PS2: [360, 152],
  PS6: [360, 268],
  PS10: [500, 152],
  PS3: [625, 52],
  PS9: [745, 152],
  PS4: [625, 368],
  PS8: [825, 258],
  MFS3: [290, 264],
  MFS1: [430, 264],
  MFS2: [535, 128],
  MFS4: [725, 366],
};

export function NetworkSchematic2D({
  topology,
  scenario,
  features,
  timeIndex,
  isPlaying,
  speed,
  showSymbolicFlow,
  selectedChannelId,
  onSelectChannel,
  showTruthLayer,
}: NetworkSchematic2DProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const channelMap = new Map(scenario.sensor_channels.map((c) => [c.id, c]));

  const currentT = scenario.time_seconds[timeIndex] ?? 0;
  const isPostOnset =
    scenario.event.onset_time !== null &&
    currentT >= scenario.event.onset_time &&
    (scenario.event.end_time === null || currentT <= scenario.event.end_time);

  const truthTargets = new Set(scenario.event.true_edges_or_nodes ?? []);
  const predictedTarget =
    features.localization && scenario.location_prediction
      ? scenario.location_prediction.predicted_edge_or_node
      : null;

  const flowDurationSec = Math.max(0.5, 2.0 / Math.max(0.5, speed));

  const getChannelMetrics = (channelId: string) => {
    const ch = channelMap.get(channelId);
    if (!ch || !ch.observable) {
      return { ch, val: null as number | null, delta: null as number | null, alertLevel: 0 };
    }
    const val = ch.values[timeIndex] ?? null;
    const base = ch.values.find((v) => v !== null) ?? null;
    if (val === null || base === null) return { ch, val, delta: null, alertLevel: 0 };
    const delta = val - base;
    const denom = ch.variable === 'pressure' ? 0.35 : 0.45;
    const alertLevel = Math.min(1, Math.abs(delta) / denom);
    return { ch, val, delta, alertLevel };
  };

  const inspectedId = hoveredId ?? selectedChannelId;
  const inspected = inspectedId ? getChannelMetrics(inspectedId) : null;

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ position: 'relative', width: '100%' }}>
        <svg
          viewBox="0 0 900 400"
          width="100%"
          height="100%"
          role="img"
          aria-label="Interactive 2D gas network schematic"
          style={{ display: 'block', maxHeight: 410, userSelect: 'none' }}
        >
          <defs>
            <pattern id="petrol-grid" width="28" height="28" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="1" fill="#24524A" opacity="0.55" />
            </pattern>
          </defs>

          <rect x="0" y="0" width="900" height="400" fill="url(#petrol-grid)" />

          {/* Pipes / Edges */}
          {topology.edges.map((edge) => {
            const p1 = NODE_POS_2D[edge.source];
            const p2 = NODE_POS_2D[edge.target];
            if (!p1 || !p2) return null;
            const mx = (p1[0] + p2[0]) / 2;
            const my = (p1[1] + p2[1]) / 2;
            const isTruth = showTruthLayer && truthTargets.has(edge.id);
            const isPred = predictedTarget === edge.id;

            return (
              <g key={edge.id}>
                <line
                  x1={p1[0]}
                  y1={p1[1]}
                  x2={p2[0]}
                  y2={p2[1]}
                  stroke={isPred ? '#34B5A5' : '#24524A'}
                  strokeWidth={13}
                  strokeLinecap="round"
                />
                <line
                  x1={p1[0]}
                  y1={p1[1]}
                  x2={p2[0]}
                  y2={p2[1]}
                  stroke="#0B2B28"
                  strokeWidth={7}
                  strokeLinecap="round"
                />
                {showSymbolicFlow && (
                  <line
                    x1={p1[0]}
                    y1={p1[1]}
                    x2={p2[0]}
                    y2={p2[1]}
                    stroke={isPostOnset ? '#E5AB65' : '#34B5A5'}
                    strokeWidth={2.6}
                    strokeLinecap="round"
                    strokeDasharray="9 15"
                    className={isPlaying ? 'pipe-flow-anim' : 'pipe-flow-paused'}
                    style={{ animationDuration: `${flowDurationSec}s` }}
                    opacity={0.9}
                  />
                )}
                {isTruth && (
                  <line
                    x1={p1[0]}
                    y1={p1[1]}
                    x2={p2[0]}
                    y2={p2[1]}
                    stroke="#DC776C"
                    strokeWidth={17}
                    strokeDasharray="10 7"
                    strokeLinecap="round"
                    className={isPostOnset && isPlaying ? 'truth-pulse' : ''}
                    opacity={isPostOnset ? 0.78 : 0.4}
                  />
                )}
                <rect
                  x={mx - 15}
                  y={my - 9}
                  width={30}
                  height={18}
                  rx={4}
                  fill="#0B2B28"
                  stroke={isTruth ? '#DC776C' : '#326C62'}
                  strokeWidth={1}
                />
                <text
                  x={mx}
                  y={my + 3.5}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="600"
                  fontFamily="IBM Plex Mono, monospace"
                  fill={isTruth ? '#DC776C' : '#9CB9B1'}
                >
                  {edge.component_group}
                </text>
              </g>
            );
          })}

          {/* Junction Nodes */}
          {topology.nodes.map((node) => {
            const pos = NODE_POS_2D[node.id];
            if (!pos) return null;
            const [cx, cy] = pos;
            const isComp = node.kind === 'compressor';
            const isTruth = showTruthLayer && truthTargets.has(node.id);

            return (
              <g key={node.id}>
                {isTruth && (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={isComp ? 26 : 22}
                    fill="none"
                    stroke="#DC776C"
                    strokeWidth={2.5}
                    strokeDasharray="5 4"
                    className={isPostOnset && isPlaying ? 'truth-pulse' : ''}
                  />
                )}
                {isComp && (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={22}
                    fill="none"
                    stroke="#34B5A5"
                    strokeWidth={1.8}
                    strokeDasharray="5 5"
                    className={isPlaying && showSymbolicFlow ? 'compressor-spin' : ''}
                    style={{ transformOrigin: `${cx}px ${cy}px` }}
                  />
                )}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isComp ? 17 : 14}
                  fill={isComp ? '#16433D' : node.kind === 'source' ? '#103632' : '#0B2B28'}
                  stroke={isComp ? '#34B5A5' : '#91D7C6'}
                  strokeWidth={2}
                />
                <text
                  x={cx}
                  y={cy + 3.5}
                  textAnchor="middle"
                  fontSize="9.5"
                  fontWeight="600"
                  fontFamily="IBM Plex Mono, monospace"
                  fill="#EDF5F1"
                >
                  {node.id}
                </text>
              </g>
            );
          })}

          {/* Compact, Non-Overlapping Sensor Tags */}
          {topology.sensors.map((sensor) => {
            const { ch, alertLevel } = getChannelMetrics(sensor.channel_id);
            if (!ch) return null;
            const pin = SENSOR_PIN_POS[ch.id];
            if (!pin) return null;
            const [sx, sy] = pin;

            const nodePos = NODE_POS_2D[sensor.attached_to];
            const edge = topology.edges.find((e) => e.id === sensor.attached_to);
            let ax = sx;
            let ay = sy;
            if (nodePos) {
              ax = nodePos[0];
              ay = nodePos[1];
            } else if (edge) {
              const p1 = NODE_POS_2D[edge.source];
              const p2 = NODE_POS_2D[edge.target];
              if (p1 && p2) {
                ax = (p1[0] + p2[0]) / 2;
                ay = (p1[1] + p2[1]) / 2;
              }
            }

            const isSelected = selectedChannelId === ch.id;
            const isHovered = hoveredId === ch.id;
            const isShifted = alertLevel > 0.3;

            return (
              <g
                key={ch.id}
                role="button"
                tabIndex={0}
                aria-label={`Select sensor ${ch.id}`}
                style={{ cursor: 'pointer', opacity: ch.observable ? 1 : 0.45 }}
                onMouseEnter={() => setHoveredId(ch.id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => onSelectChannel(isSelected ? null : ch.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectChannel(isSelected ? null : ch.id);
                  }
                }}
              >
                <line
                  x1={ax}
                  y1={ay}
                  x2={sx}
                  y2={sy}
                  stroke={isSelected || isHovered ? '#34B5A5' : '#24524A'}
                  strokeWidth={1.2}
                  strokeDasharray="3 3"
                />
                <rect
                  x={sx - 23}
                  y={sy - 11}
                  width={46}
                  height={22}
                  rx={5}
                  fill={isSelected ? '#34B5A5' : isHovered ? '#16433D' : '#103632'}
                  stroke={
                    isSelected
                      ? '#91D7C6'
                      : isShifted
                      ? '#E5AB65'
                      : ch.variable === 'pressure'
                      ? '#326C62'
                      : '#34B5A5'
                  }
                  strokeWidth={isSelected || isShifted ? 1.8 : 1.2}
                />
                <text
                  x={sx}
                  y={sy + 3.5}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="700"
                  fontFamily="IBM Plex Mono, monospace"
                  fill={isSelected ? '#071F1D' : isShifted ? '#E5AB65' : '#EDF5F1'}
                >
                  {ch.id}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Single Clean Anchored Readout Pill when Hovering/Selecting a Sensor */}
        {inspected?.ch && (
          <div
            style={{
              position: 'absolute',
              top: 10,
              right: 12,
              background: 'var(--bg-sidebar)',
              border: '1px solid var(--accent-primary)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 10px',
              fontSize: '12px',
              color: 'var(--text-primary)',
              pointerEvents: 'none',
            }}
          >
            <strong className="mono">{inspected.ch.id}</strong> · {inspected.ch.node_or_edge} ·{' '}
            <span className="mono">
              {!inspected.ch.observable
                ? 'Absent (Center)'
                : inspected.val !== null
                ? `${inspected.val.toFixed(3)} ${inspected.ch.unit}`
                : 'Missing (null)'}
            </span>
          </div>
        )}
      </div>

      {/* Live 16-Channel Tabular Grid — Zero Overlaps, Clear Numbers */}
      <div className="sensor-chip-grid" aria-label="Live sensor telemetry grid">
        {scenario.sensor_channels.map((ch) => {
          const { val, delta, alertLevel } = getChannelMetrics(ch.id);
          const active = selectedChannelId === ch.id;
          const isShifted = alertLevel > 0.3;

          return (
            <button
              key={ch.id}
              type="button"
              className={`sensor-chip ${active ? 'active' : ''} ${!ch.observable ? 'absent' : ''}`}
              title={ch.status_note ?? ch.node_or_edge}
              onClick={() => onSelectChannel(active ? null : ch.id)}
            >
              <span className="mono" style={{ fontWeight: 700, color: active ? 'var(--accent-soft)' : 'var(--text-secondary)' }}>
                {ch.id}
              </span>
              <span
                className="mono"
                style={{
                  fontWeight: 600,
                  color: !ch.observable
                    ? 'var(--text-muted)'
                    : isShifted
                    ? 'var(--state-warning)'
                    : 'var(--text-primary)',
                }}
              >
                {!ch.observable
                  ? 'Absent'
                  : val !== null
                  ? `${val.toFixed(2)} ${ch.unit}`
                  : 'NULL'}
                {ch.observable && delta !== null && Math.abs(delta) >= 0.05
                  ? ` (${delta > 0 ? '+' : ''}${delta.toFixed(2)})`
                  : ''}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
