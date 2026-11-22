import { Component, type ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Html, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import type { ScenarioPayloadV1, SupportedFeatures, TopologyV1 } from '../data/types';

interface NetworkScene3DProps {
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

class WebGLErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)' }}>
          <strong>3D WebGL unavailable on this device.</strong>
          <p style={{ margin: '6px 0 0', fontSize: '13px' }}>
            Switch back to <strong>2D Schematic</strong> for full interactive replay.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

// Well-spread 3D coordinates derived from Simscape node graph so node tags never stack
const NODE_POS_3D: Record<string, [number, number, number]> = {
  N47: [-5.4, 0, 0.0],
  N50: [-3.4, 0, 0.0],
  N239: [-1.4, 0, 0.0],
  N309: [0.6, 0, 0.0],
  N106: [2.4, 0, -1.9],
  N221: [4.2, 0, 0.0],
  N109: [2.4, 0, 1.9],
  N195: [5.4, 0, 1.9],
};

function PipeSegment3D({
  start,
  end,
  color,
  isPlaying,
  speed,
  showSymbolicFlow,
}: {
  start: THREE.Vector3;
  end: THREE.Vector3;
  color: string;
  isPlaying: boolean;
  speed: number;
  showSymbolicFlow: boolean;
}) {
  const { midpoint, length, quaternion } = useMemo(() => {
    const dir = new THREE.Vector3().subVectors(end, start);
    const len = dir.length();
    const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
    const quat = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      dir.clone().normalize()
    );
    return { midpoint: mid, length: len, quaternion: quat };
  }, [start, end]);

  const particleRefs = useRef<(THREE.Mesh | null)[]>([]);
  const phaseRef = useRef(0);

  useFrame((_, delta) => {
    if (!showSymbolicFlow) return;
    if (isPlaying) {
      phaseRef.current = (phaseRef.current + delta * 0.4 * Math.max(0.5, speed)) % 1;
    }
    const count = 3;
    for (let i = 0; i < count; i++) {
      const mesh = particleRefs.current[i];
      if (!mesh) continue;
      const u = (phaseRef.current + i / count) % 1;
      mesh.position.lerpVectors(start, end, u);
    }
  });

  return (
    <group>
      <mesh position={midpoint} quaternion={quaternion}>
        <cylinderGeometry args={[0.1, 0.1, length, 16]} />
        <meshStandardMaterial color={color} metalness={0.35} roughness={0.55} />
      </mesh>
      {showSymbolicFlow &&
        [0, 1, 2].map((i) => (
          <mesh
            key={i}
            ref={(el) => {
              particleRefs.current[i] = el;
            }}
            position={start}
          >
            <sphereGeometry args={[0.075, 10, 10]} />
            <meshStandardMaterial color="#91D7C6" emissive="#34B5A5" emissiveIntensity={0.65} />
          </mesh>
        ))}
    </group>
  );
}

function CompressorRing3D({
  position,
  isPlaying,
  showSymbolicFlow,
}: {
  position: THREE.Vector3;
  isPlaying: boolean;
  showSymbolicFlow: boolean;
}) {
  const ringRef = useRef<THREE.Mesh | null>(null);
  useFrame((_, delta) => {
    if (ringRef.current && isPlaying && showSymbolicFlow) {
      ringRef.current.rotation.z += delta * 1.8;
    }
  });
  return (
    <mesh ref={ringRef} position={position} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[0.36, 0.035, 10, 28]} />
      <meshStandardMaterial color="#34B5A5" metalness={0.3} roughness={0.4} />
    </mesh>
  );
}

export function NetworkScene3D({
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
}: NetworkScene3DProps) {
  const [preset, setPreset] = useState<'iso' | 'top'>('iso');
  const [resetTick, setResetTick] = useState(0);
  const [tabHidden, setTabHidden] = useState(
    typeof document !== 'undefined' ? document.hidden : false
  );

  useEffect(() => {
    const onVis = () => setTabHidden(document.hidden);
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, []);

  const channelMap = new Map(scenario.sensor_channels.map((c) => [c.id, c]));
  const truthTargets = new Set(scenario.event.true_edges_or_nodes ?? []);
  const predictedTarget =
    features.localization && scenario.location_prediction
      ? scenario.location_prediction.predicted_edge_or_node
      : null;

  const focusedCh = selectedChannelId ? channelMap.get(selectedChannelId) ?? null : null;
  const focusedVal = focusedCh ? focusedCh.values[timeIndex] : null;

  const camPos: [number, number, number] =
    preset === 'iso' ? [0.0, 6.8, 10.8] : [0.0, 13.0, 0.01];

  return (
    <WebGLErrorBoundary>
      <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
        <div style={{ position: 'relative', width: '100%', height: 420 }}>
          {/* Corner Camera Presets */}
          <div
            style={{
              position: 'absolute',
              top: 10,
              right: 12,
              zIndex: 3,
              display: 'flex',
              gap: 6,
            }}
          >
            <button
              type="button"
              className={`seg-btn ${preset === 'iso' ? 'active' : ''}`}
              onClick={() => setPreset('iso')}
            >
              Iso
            </button>
            <button
              type="button"
              className={`seg-btn ${preset === 'top' ? 'active' : ''}`}
              onClick={() => setPreset('top')}
            >
              Top
            </button>
            <button
              type="button"
              className="seg-btn"
              onClick={() => setResetTick((k) => k + 1)}
            >
              Fit View
            </button>
          </div>

          {/* Dedicated Corner Telemetry HUD (replaces overlapping floating HTML boxes) */}
          <div
            style={{
              position: 'absolute',
              top: 10,
              left: 12,
              zIndex: 3,
              background: 'rgba(11, 43, 40, 0.92)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 10px',
              fontSize: '12px',
              color: 'var(--text-primary)',
              pointerEvents: 'none',
            }}
          >
            {focusedCh ? (
              <>
                <strong className="mono">{focusedCh.id}</strong> ({focusedCh.node_or_edge}):{' '}
                <span className="mono" style={{ color: 'var(--accent-soft)' }}>
                  {!focusedCh.observable
                    ? 'Absent (Center)'
                    : focusedVal !== null && focusedVal !== undefined
                    ? `${focusedVal.toFixed(3)} ${focusedCh.unit}`
                    : 'NULL'}
                </span>
              </>
            ) : (
              <span style={{ color: 'var(--text-secondary)' }}>
                Select a sensor chip below to highlight &amp; inspect
              </span>
            )}
          </div>

          <Canvas
            key={`${preset}-${resetTick}`}
            frameloop={tabHidden ? 'never' : 'always'}
            camera={{ position: camPos, fov: 42 }}
            dpr={[1, 1.5]}
          >
            <color attach="background" args={['#071F1D']} />
            <fog attach="fog" args={['#071F1D', 12, 24]} />
            <ambientLight intensity={0.75} />
            <directionalLight position={[6, 12, 8]} intensity={0.9} color="#EDF5F1" />
            <directionalLight position={[-6, 4, -6]} intensity={0.35} color="#34B5A5" />
            <gridHelper args={[18, 22, '#24524A', '#103632']} position={[0, -0.5, 0]} />
            <OrbitControls enableDamping maxDistance={18} minDistance={4} />

            {topology.edges.map((edge) => {
              const p1 = NODE_POS_3D[edge.source];
              const p2 = NODE_POS_3D[edge.target];
              if (!p1 || !p2) return null;
              const isTruth = showTruthLayer && truthTargets.has(edge.id);
              const isPred = predictedTarget === edge.id;
              const color = isTruth ? '#DC776C' : isPred ? '#34B5A5' : '#2E6760';

              return (
                <PipeSegment3D
                  key={edge.id}
                  start={new THREE.Vector3(...p1)}
                  end={new THREE.Vector3(...p2)}
                  color={color}
                  isPlaying={isPlaying}
                  speed={speed}
                  showSymbolicFlow={showSymbolicFlow}
                />
              );
            })}

            {topology.nodes.map((node) => {
              const coords = NODE_POS_3D[node.id];
              if (!coords) return null;
              const pos = new THREE.Vector3(...coords);
              const isComp = node.kind === 'compressor';
              const isTruth = showTruthLayer && truthTargets.has(node.id);
              return (
                <group key={node.id}>
                  <mesh position={pos}>
                    <sphereGeometry args={[isComp ? 0.26 : 0.19, 18, 18]} />
                    <meshStandardMaterial
                      color={isTruth ? '#DC776C' : isComp ? '#34B5A5' : '#91D7C6'}
                      metalness={0.3}
                      roughness={0.45}
                    />
                  </mesh>
                  {isComp && (
                    <CompressorRing3D
                      position={pos}
                      isPlaying={isPlaying}
                      showSymbolicFlow={showSymbolicFlow}
                    />
                  )}
                  <Html distanceFactor={10} position={[pos.x, pos.y + 0.42, pos.z]}>
                    <div
                      style={{
                        background: '#0B2B28',
                        border: '1px solid #24524A',
                        borderRadius: 4,
                        padding: '1px 5px',
                        fontSize: 10,
                        fontWeight: 600,
                        fontFamily: 'IBM Plex Mono, monospace',
                        color: '#EDF5F1',
                        whiteSpace: 'nowrap',
                        pointerEvents: 'none',
                      }}
                    >
                      {node.id}
                    </div>
                  </Html>
                </group>
              );
            })}
          </Canvas>
        </div>

        {/* Same 16-channel telemetry grid below 3D viewport for non-overlapping reading */}
        <div className="sensor-chip-grid" aria-label="Live sensor telemetry grid">
          {scenario.sensor_channels.map((ch) => {
            const val = ch.values[timeIndex];
            const active = selectedChannelId === ch.id;
            return (
              <button
                key={ch.id}
                type="button"
                className={`sensor-chip ${active ? 'active' : ''} ${!ch.observable ? 'absent' : ''}`}
                onClick={() => onSelectChannel(active ? null : ch.id)}
              >
                <span className="mono" style={{ fontWeight: 700, color: active ? 'var(--accent-soft)' : 'var(--text-secondary)' }}>
                  {ch.id}
                </span>
                <span className="mono" style={{ fontWeight: 600 }}>
                  {!ch.observable
                    ? 'Absent'
                    : val !== null && val !== undefined
                    ? `${val.toFixed(2)} ${ch.unit}`
                    : 'NULL'}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </WebGLErrorBoundary>
  );
}
