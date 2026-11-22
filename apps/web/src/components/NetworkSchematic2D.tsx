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
    cx: 92 + ((x - minX) / Math.max(1e-6, maxX - minX)) * 616,
    cy: 86 + ((y - minY) / Math.max(1e-6, maxY - minY)) * 248,
  });

  const currentT = scenario.time_seconds[timeIndex] ?? 0;
  const isPostOnset =
    scenario.event.onset_time !== null && currentT >= scenario.event.onset_time;

  const truthTargets = new Set(scenario.event.true_edges_or_nodes ?? []);
  const predictedTarget =
    features.localization && scenario.location_prediction
      ? scenario.location_prediction.predicted_edge_or_node
      : null;

  // Symbolic animation duration responds gently to replay speed (paused when not playing)
  const flowDurationSec = Math.max(0.45, 1.8 / Math.max(0.5, speed));

  // Helper to compute relative deviation from t=0 baseline for visual emphasis
  const getDeviation = (channelId: string) => {
    const ch = channelMap.get(channelId);
    if (!ch) return { val: null as number | null, delta: null as number | null, alertLevel: 0 };
    const val = ch.values[timeIndex] ?? null;
    const base = ch.values.find((v) => v !== null) ?? null;
    if (val === null || base === null) return { val, delta: null, alertLevel: 0 };
    const delta = val - base;
    const denom = ch.variable === 'pressure' ? 0.35 : 0.45;
    const alertLevel = Math.min(1, Math.abs(delta) / denom);
    return { val, delta, alertLevel };
  };

  return (
    <svg
      viewBox="0 0 800 420"
      width="100%"
      height="100%"
      role="img"
      aria-label="Interactive 2D gas network schematic with symbolic flow"
      style={{ maxHeight: 450, userSelect: 'none' }}
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
        <marker
          id="flow-arrow"
          viewBox="0 0 10 10"
          refX="6"
          refY="5"
          markerWidth="5"
          markerHeight="5"
          orient="auto-start-reverse"
        >
          <path d="M 0 1 L 8 5 L 0 9 z" fill="#007F86" />
        </marker>
      </defs>

      {/* Subtle engineering grid background */}
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

        // Check if an attached mass-flow sensor has strong deviation
        const attachedSensor = topology.sensors.find((s) => s.attached_to === edge.id);
        const dev = attachedSensor ? getDeviation(attachedSensor.channel_id) : { alertLevel: 0 };

        return (
          <g
            key={edge.id}
            onMouseEnter={() => setHoveredId(edge.id)}
            onMouseLeave={() => setHoveredId(null)}
          >
            {/* Outer pipe casing */}
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

            {/* Inner pipe bore */}
            <line
              x1={p1.cx}
              y1={p1.cy}
              x2={p2.cx}
              y2={p2.cy}
              stroke="#1B3B5A"
              strokeWidth={6}
              strokeLinecap="round"
            />

            {/* Symbolic animated gas stream (labeled as symbolic, not velocity) */}
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

            {/* Ground Truth overlay (distinct dashed red, pulses when post-onset) */}
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

            {/* Edge ID tag */}
            <rect
              x={mx - 19}
              y={my - 11}
              width={38}
              height={20}
              rx={5}
              fill={isTruth ? '#FEE2E2' : '#F4F4E9'}
              stroke={isTruth ? '#B91C1C' : '#9AA6A3'}
              strokeWidth={1.2}
            />
            <text
              x={mx}
              y={my + 3}
              textAnchor="middle"
              fontSize="10.5"
              fontWeight="700"
              fill={isTruth ? '#991B1B' : '#10263E'}
            >
              {edge.id}
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
            {/* Pressure deviation halo when signal departs from baseline */}
            {dev.alertLevel > 0.25 && (
              <circle
                cx={cx}
                cy={cy}
                r={isComp ? 26 : 21}
                fill="none"
                stroke="#F59E0B"
                strokeWidth={2.5}
                opacity={0.3 + dev.alertLevel * 0.55}
                className={isPlaying ? 'sensor-halo-pulse' : ''}
              />
            )}

            {/* Ground truth node ring */}
            {isTruth && (
              <circle
                cx={cx}
                cy={cy}
                r={isComp ? 28 : 23}
                fill="none"
                stroke="#DC2626"
                strokeWidth={3}
                strokeDasharray="5 4"
                className={isPostOnset && isPlaying ? 'truth-pulse' : ''}
              />
            )}

            {/* Compressor spinning ring */}
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
              strokeWidth={2.4}
            />
            <text
              x={cx}
              y={cy + 3.8}
              textAnchor="middle"
              fontSize="10"
              fontWeight="700"
              fill={isComp || node.kind === 'source' ? '#F4F4E9' : '#10263E'}
            >
              {node.id}
            </text>
          </g>
        );
      })}

      {/* Sensor Badges with live value + delta */}
      {topology.sensors.map((sensor, idx) => {
        const ch = channelMap.get(sensor.channel_id);
        if (!ch) return null;
        const node = nodeMap.get(sensor.attached_to);
        const edge = topology.edges.find((e) => e.id === sensor.attached_to);
        let sx = 0;
        let sy = 0;
        let ax = 0;
        let ay = 0;

        if (node) {
          const p = project(node.x, node.y);
          ax = p.cx;
          ay = p.cy;
          sx = p.cx;
          sy = p.cy - 44;
        } else if (edge) {
          const n1 = nodeMap.get(edge.source);
          const n2 = nodeMap.get(edge.target);
          if (!n1 || !n2) return null;
          const p1 = project(n1.x, n1.y);
          const p2 = project(n2.x, n2.y);
          ax = (p1.cx + p2.cx) / 2;
          ay = (p1.cy + p2.cy) / 2;
          sx = ax;
          sy = ay + (idx % 2 === 0 ? 44 : -44);
        }

        const { val, delta, alertLevel } = getDeviation(ch.id);
        const formatted = val !== null ? val.toFixed(2) : 'NULL';
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
            aria-label={`${ch.id} (${ch.variable}): ${formatted} ${ch.unit}`}
            style={{ cursor: 'pointer' }}
            onClick={() => onSelectChannel(isSelected ? null : ch.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelectChannel(isSelected ? null : ch.id);
              }
            }}
          >
            {/* Leader line connecting badge to node/edge */}
            <line
              x1={ax}
              y1={ay}
              x2={sx}
              y2={sy}
              stroke={isSelected ? '#007F86' : '#9AA6A3'}
              strokeWidth={1.2}
              strokeDasharray="3 2"
            />

            <rect
              x={sx - 54}
              y={sy - 19}
              width={108}
              height={38}
              rx={7}
              fill={isSelected ? '#0E3F3C' : val === null ? '#F1F5F9' : '#FFFFFF'}
              stroke={
                isSelected
                  ? '#007F86'
                  : isShifted
                  ? '#D97706'
                  : isPressure
                  ? '#10263E'
                  : '#007F86'
              }
              strokeWidth={isSelected || isShifted ? 2.2 : 1.4}
              filter={isSelected ? 'url(#soft-glow)' : undefined}
            />

            <text
              x={sx - 46}
              y={sy - 4}
              fontSize="9.5"
              fontWeight="700"
              fill={isSelected ? '#A7F3D0' : '#3D5166'}
            >
              {ch.id}
            </text>

            <text
              x={sx + 46}
              y={sy - 4}
              textAnchor="end"
              fontSize="8.8"
              fontWeight="600"
              fontFamily="monospace"
              fill={
                isSelected
                  ? '#FDE68A'
                  : isShifted
                  ? '#B45309'
                  : '#64748B'
              }
            >
              Δ{deltaStr}
            </text>

            <text
              x={sx}
              y={sy + 12}
              textAnchor="middle"
              fontSize="10.5"
              fontWeight="700"
              fontFamily="monospace"
              fill={isSelected ? '#FFFFFF' : val === null ? '#64748B' : '#10263E'}
            >
              {formatted} {val !== null ? ch.unit : ''}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
