import { Component, type ReactNode, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Html, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import type { ScenarioPayloadV1, SupportedFeatures, TopologyNode, TopologyV1 } from '../data/types';

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
        <div style={{ padding: 24, textAlign: 'center', color: 'var(--ink-secondary)' }}>
          <strong>3D WebGL unavailable on this device.</strong>
          <p style={{ margin: '6px 0 0', fontSize: '0.84rem' }}>
            Switch back to <strong>2D Schematic</strong> for full interactive replay.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

function nodeToVec3(n: TopologyNode): THREE.Vector3 {
  // Center topology around origin in Three.js XZ plane
  return new THREE.Vector3(n.x - 3.0, n.z, n.y - 1.0);
}

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
      phaseRef.current = (phaseRef.current + delta * 0.45 * Math.max(0.5, speed)) % 1;
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
        <cylinderGeometry args={[0.095, 0.095, length, 16]} />
        <meshStandardMaterial color={color} metalness={0.25} roughness={0.45} />
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
            <sphereGeometry args={[0.07, 10, 10]} />
            <meshStandardMaterial
              color="#2DD4BF"
              emissive="#007F86"
              emissiveIntensity={0.9}
            />
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
      ringRef.current.rotation.z += delta * 2.0;
    }
  });
  return (
    <mesh ref={ringRef} position={position} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[0.34, 0.035, 10, 28]} />
      <meshStandardMaterial color="#007F86" emissive="#007F86" emissiveIntensity={0.4} />
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

  const nodeMap = new Map(topology.nodes.map((n) => [n.id, n]));
  const channelMap = new Map(scenario.sensor_channels.map((c) => [c.id, c]));
  const truthTargets = new Set(scenario.event.true_edges_or_nodes ?? []);
  const predictedTarget =
    features.localization && scenario.location_prediction
      ? scenario.location_prediction.predicted_edge_or_node
      : null;

  const camPos: [number, number, number] =
    preset === 'iso' ? [0.2, 4.2, 5.8] : [0, 7.6, 0.01];

  return (
    <WebGLErrorBoundary>
      <div style={{ position: 'relative', width: '100%', height: 420 }}>
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
            Reset
          </button>
        </div>

        <Canvas
          key={`${preset}-${resetTick}`}
          camera={{ position: camPos, fov: 44 }}
          dpr={[1, 1.75]}
        >
          <color attach="background" args={['#FAFBF7']} />
          <ambientLight intensity={0.85} />
          <directionalLight position={[6, 10, 6]} intensity={0.7} />
          <gridHelper args={[12, 18, '#CBD5E1', '#E2E8F0']} position={[0, -0.45, 0]} />
          <OrbitControls enableDamping maxDistance={14} minDistance={2.5} />

          {topology.edges.map((edge) => {
            const src = nodeMap.get(edge.source);
            const dst = nodeMap.get(edge.target);
            if (!src || !dst) return null;
            const isTruth = showTruthLayer && truthTargets.has(edge.id);
            const isPred = predictedTarget === edge.id;
            const color = isTruth ? '#DC2626' : isPred ? '#007F86' : '#10263E';

            return (
              <PipeSegment3D
                key={edge.id}
                start={nodeToVec3(src)}
                end={nodeToVec3(dst)}
                color={color}
                isPlaying={isPlaying}
                speed={speed}
                showSymbolicFlow={showSymbolicFlow}
              />
            );
          })}

          {topology.nodes.map((node) => {
            const pos = nodeToVec3(node);
            const isComp = node.kind === 'compressor';
            return (
              <group key={node.id}>
                <mesh position={pos}>
                  <sphereGeometry args={[isComp ? 0.24 : 0.17, 18, 18]} />
                  <meshStandardMaterial
                    color={
                      isComp
                        ? '#0E3F3C'
                        : node.kind === 'source'
                        ? '#007F86'
                        : '#3D5166'
                    }
                    metalness={0.2}
                    roughness={0.4}
                  />
                </mesh>
                {isComp && (
                  <CompressorRing3D
                    position={pos}
                    isPlaying={isPlaying}
                    showSymbolicFlow={showSymbolicFlow}
                  />
                )}
                <Html distanceFactor={8} position={[pos.x, pos.y + 0.36, pos.z]}>
                  <div
                    style={{
                      background: 'rgba(244,244,233,0.94)',
                      border: '1px solid #9AA6A3',
                      borderRadius: 4,
                      padding: '1px 5px',
                      fontSize: 10,
                      fontWeight: 700,
                      color: '#10263E',
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

          {topology.sensors.map((s) => {
            const ch = channelMap.get(s.channel_id);
            const node = nodeMap.get(s.attached_to);
            if (!ch || !node) return null;
            const pos = nodeToVec3(node);
            const val = ch.values[timeIndex];
            const isSelected = selectedChannelId === ch.id;
            return (
              <Html key={ch.id} distanceFactor={8} position={[pos.x, pos.y - 0.42, pos.z]}>
                <button
                  type="button"
                  onClick={() => onSelectChannel(isSelected ? null : ch.id)}
                  style={{
                    background: isSelected ? '#0E3F3C' : '#FFFFFF',
                    color: isSelected ? '#FFFFFF' : '#10263E',
                    border: `1.5px solid ${isSelected ? '#2DD4BF' : '#007F86'}`,
                    borderRadius: 5,
                    padding: '2px 6px',
                    fontSize: 9.5,
                    fontFamily: 'monospace',
                    fontWeight: 700,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {ch.id}: {val !== null && val !== undefined ? val.toFixed(2) : 'NULL'} {ch.unit}
                </button>
              </Html>
            );
          })}
        </Canvas>
      </div>
    </WebGLErrorBoundary>
  );
}
