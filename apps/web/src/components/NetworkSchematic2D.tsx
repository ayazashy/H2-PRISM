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

// Explicit vertical/horizontal badge offsets for dense Simscape junctions so labels never collide
const BADGE_OFFSETS: Record<string, [number, number]> = {
  PS7: [0, -48],
  PS1: [0, -48],
  PS2: [-36, -48],
  PS6: [48, 48],
  PS10: [0, -48],
  PS3: [0, -48],
  PS9: [0, -48],
  PS4: [0, 50],
  PS8: [0, 48],
  MFS3: [0, 46],
  MFS1: [0, 44],
  MFS2: [-24, -44],
  MFS4: [24, 46],
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
  const nodeMap = new Map(topology.nodes.map((n) => [n.id, n]));
  const channelMap = new Map(scenario.sensor_channels.map((c) => [c.id, c]));

  const xs = topology.nodes.map((n) => n.x);
  const ys = topology.nodes.map((n) => n.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs) || 1;
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys) || 1;

  const project = (x: number, y: number) => ({
    cx: 85 + ((x - minX) / Math.max(1e-6, maxX - minX)) * 630,
    cy: 96 + ((y - minY) / Math.max(1e-6, maxY - minY)) * 228,
  });

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

  const flowDurationSec = Math.max(0.45, 1.8 / Math.max(0.5, speed));

  const getDeviation = (channelId: string) => {
    const ch = channelMap.get(channelId);
    if (!ch || !ch.observable) {
      return { val: null as number | null, delta: null as number | null, alertLevel: 0 };
    }
    const val = ch.values[timeIndex] ?? null;
    const base = ch.values.find((v) => v !== null) ?? null;
    if (val === null || base === null) return { val, delta: null, alertLevel: 0 };
    const delta = val - base;
    const denom = ch.variable === 'pressure' ? 0.35 : 0.45;
    const alertLevel = Math.min(1, Math.abs(delta) / denom);
    return { val, delta, alertLevel };
  };

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column' }}>
      <svg
        viewBox="0 0 800 420"
        width="100%"
        height="100%"
        role="img"
        aria-label="Interactive 2D gas network schematic with symbolic flow"
        style={{ maxHeight: 410, userSelect: 'none' }}
      >
        <defs>
          <pattern id="grid-dots" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="#D5D7CB" opacity="0.65" />
          </pattern>
          <filter id="soft-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <rect x="0" y="0" width="800" height="420" fill="url(#grid-dots)" />

        {/* Pipes / Edges */}
        {topology.edges.map((edge) => {
          const src = nodeMap.get(edge.source);
          const dst = nodeMap.get(edge.target);
          if (!src || !dst) return null;
          const p1 = project(src.x, src.y);
          const p2 = project(dst.x, dst.y);
          const mx = (p1.cx + p2.cx) / 2;
          const my = (p1.cy + p2.cy) / 2;
          const isTruth = showTruthLayer && truthTargets.has(edge.id);
          const isPred = predictedTarget === edge.id;
          const isHovered = hoveredId === edge.id;
          const attachedSensor = topology.sensors.find((s) => s.attached_to === edge.id);
          const dev = attachedSensor ? getDeviation(attachedSensor.channel_id) : { alertLevel: 0 };

          return (
            <g
              key={edge.id}
              onMouseEnter={() => setHoveredId(edge.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <line
                x1={p1.cx}
                y1={p1.cy}
                x2={p2.cx}
                y2={p2.cy}
                stroke={isPred ? '#007F86' : isHovered ? '#0E3F3C' : '#10263E'}
                strokeWidth={isPred || isHovered ? 12 : 10}
                strokeLinecap="round"
                opacity={0.92}
              />
              <line
                x1={p1.cx}
                y1={p1.cy}
                x2={p2.cx}
                y2={p2.cy}
                stroke="#1B3B5A"
                strokeWidth={6}
                strokeLinecap="round"
              />
              {showSymbolicFlow && (
                <line
                  x1={p1.cx}
                  y1={p1.cy}
                  x2={p2.cx}
                  y2={p2.cy}
                  stroke={dev.alertLevel > 0.35 && isPostOnset ? '#F59E0B' : '#2DD4BF'}
                  strokeWidth={3.2}
                  strokeLinecap="round"
                  strokeDasharray="10 14"
                  className={isPlaying ? 'pipe-flow-anim' : 'pipe-flow-paused'}
                  style={{ animationDuration: `${flowDurationSec}s` }}
                  opacity={0.95}
                />
              )}
              {isTruth && (
                <line
                  x1={p1.cx}
                  y1={p1.cy}
                  x2={p2.cx}
                  y2={p2.cy}
                  stroke="#DC2626"
                  strokeWidth={16}
                  strokeDasharray="10 7"
                  strokeLinecap="round"
                  className={isPostOnset && isPlaying ? 'truth-pulse' : ''}
                  opacity={isPostOnset ? 0.78 : 0.4}
                />
              )}
              <rect
                x={mx - 24}
                y={my - 10}
                width={48}
                height={18}
                rx={4}
                fill={isTruth ? '#FEE2E2' : '#F4F4E9'}
                stroke={isTruth ? '#B91C1C' : '#9AA6A3'}
                strokeWidth={1.1}
              />
              <text
                x={mx}
                y={my + 2.5}
                textAnchor="middle"
                fontSize="9.5"
                fontWeight="700"
                fill={isTruth ? '#991B1B' : '#10263E'}
              >
                {edge.component_group}
              </text>
            </g>
          );
        })}

        {/* Nodes */}
        {topology.nodes.map((node) => {
          const { cx, cy } = project(node.x, node.y);
          const isComp = node.kind === 'compressor';
          const isTruth = showTruthLayer && truthTargets.has(node.id);
          const attachedSensor = topology.sensors.find((s) => s.attached_to === node.id);
          const dev = attachedSensor ? getDeviation(attachedSensor.channel_id) : { alertLevel: 0 };

          return (
            <g key={node.id}>
              {dev.alertLevel > 0.25 && (
                <circle
                  cx={cx}
                  cy={cy}
                  r={isComp ? 25 : 20}
                  fill="none"
                  stroke="#F59E0B"
                  strokeWidth={2.5}
                  opacity={0.3 + dev.alertLevel * 0.55}
                  className={isPlaying ? 'sensor-halo-pulse' : ''}
                />
              )}
              {isTruth && (
                <circle
                  cx={cx}
                  cy={cy}
                  r={isComp ? 27 : 22}
                  fill="none"
                  stroke="#DC2626"
                  strokeWidth={3}
                  strokeDasharray="5 4"
                  className={isPostOnset && isPlaying ? 'truth-pulse' : ''}
                />
              )}
              {isComp && (
                <circle
                  cx={cx}
                  cy={cy}
                  r={21}
                  fill="none"
                  stroke="#007F86"
                  strokeWidth={2}
                  strokeDasharray="6 6"
                  className={isPlaying && showSymbolicFlow ? 'compressor-spin' : ''}
                  style={{ transformOrigin: `${cx}px ${cy}px` }}
                />
              )}
              <circle
                cx={cx}
                cy={cy}
                r={isComp ? 16 : 12.5}
                fill={isComp ? '#0E3F3C' : node.kind === 'source' ? '#007F86' : '#FFFFFF'}
                stroke="#10263E"
                strokeWidth={2.3}
              />
              <text
                x={cx}
                y={cy + 3.5}
                textAnchor="middle"
                fontSize="9"
                fontWeight="700"
                fill={isComp || node.kind === 'source' ? '#F4F4E9' : '#10263E'}
              >
                {node.id}
              </text>
            </g>
          );
        })}

        {/* Sensor Badges */}
        {topology.sensors.map((sensor) => {
          const ch = channelMap.get(sensor.channel_id);
          if (!ch) return null;
          const node = nodeMap.get(sensor.attached_to);
          const edge = topology.edges.find((e) => e.id === sensor.attached_to);
          let ax = 0;
          let ay = 0;
          if (node) {
            const p = project(node.x, node.y);
            ax = p.cx;
            ay = p.cy;
          } else if (edge) {
            const n1 = nodeMap.get(edge.source);
            const n2 = nodeMap.get(edge.target);
            if (!n1 || !n2) return null;
            const p1 = project(n1.x, n1.y);
            const p2 = project(n2.x, n2.y);
            ax = (p1.cx + p2.cx) / 2;
            ay = (p1.cy + p2.cy) / 2;
          }

          const [dx, dy] = BADGE_OFFSETS[ch.id] ?? [0, -44];
          const sx = Math.max(54, Math.min(746, ax + dx));
          const sy = Math.max(24, Math.min(396, ay + dy));

          const { val, delta, alertLevel } = getDeviation(ch.id);
          const formatted = !ch.observable
            ? 'ABSENT'
            : val !== null
            ? val.toFixed(2)
            : 'NULL';
          const deltaStr =
            delta !== null && Math.abs(delta) >= 0.01
              ? `${delta > 0 ? '+' : ''}${delta.toFixed(2)}`
              : '0.00';
          const isSelected = selectedChannelId === ch.id;
          const isPressure = ch.variable === 'pressure';
          const isShifted = alertLevel > 0.3;

          return (
            <g
              key={ch.id}
              role="button"
              tabIndex={0}
              aria-label={`${ch.id} (${ch.variable}): ${formatted} ${ch.observable ? ch.unit : ''}`}
              style={{ cursor: 'pointer', opacity: ch.observable ? 1 : 0.6 }}
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
                stroke={isSelected ? '#007F86' : '#9AA6A3'}
                strokeWidth={1.1}
                strokeDasharray="3 2"
              />
              <rect
                x={sx - 46}
                y={sy - 17}
                width={92}
                height={34}
                rx={6}
                fill={isSelected ? '#0E3F3C' : !ch.observable ? '#F1F5F9' : '#FFFFFF'}
                stroke={
                  isSelected
                    ? '#007F86'
                    : isShifted
                    ? '#D97706'
                    : isPressure
                    ? '#10263E'
                    : '#007F86'
                }
                strokeWidth={isSelected || isShifted ? 2 : 1.3}
                filter={isSelected ? 'url(#soft-glow)' : undefined}
              />
              <text
                x={sx - 40}
                y={sy - 3}
                fontSize="9"
                fontWeight="700"
                fill={isSelected ? '#A7F3D0' : '#3D5166'}
              >
                {ch.id}
              </text>
              <text
                x={sx + 40}
                y={sy - 3}
                textAnchor="end"
                fontSize="8.3"
                fontWeight="600"
                fontFamily="monospace"
                fill={isSelected ? '#FDE68A' : isShifted ? '#B45309' : '#64748B'}
              >
                {ch.observable ? `Δ${deltaStr}` : 'PAD'}
              </text>
              <text
                x={sx}
                y={sy + 11}
                textAnchor="middle"
                fontSize="9.5"
                fontWeight="700"
                fontFamily="monospace"
                fill={isSelected ? '#FFFFFF' : !ch.observable ? '#64748B' : '#10263E'}
              >
                {formatted} {ch.observable ? ch.unit : ''}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Accessible 2D channel selector strip covering all 16 channels */}
      <div
        aria-label="Sensor channel list"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 5,
          padding: '8px 12px',
          borderTop: '1px solid var(--border-subtle)',
          background: '#F4F4E9',
        }}
      >
        {scenario.sensor_channels.map((ch) => {
          const active = selectedChannelId === ch.id;
          const v = ch.values[timeIndex];
          return (
            <button
              key={ch.id}
              type="button"
              className={`seg-btn ${active ? 'active' : ''}`}
              style={{ fontSize: '0.72rem', padding: '3px 7px', opacity: ch.observable ? 1 : 0.65 }}
              title={ch.status_note ?? ch.node_or_edge}
              onClick={() => onSelectChannel(active ? null : ch.id)}
            >
              {ch.id}:{' '}
              {!ch.observable
                ? 'Absent'
                : v !== null && v !== undefined
                ? `${v.toFixed(2)} ${ch.unit}`
                : 'NULL'}
            </button>
          );
        })}
      </div>
    </div>
  );
}
