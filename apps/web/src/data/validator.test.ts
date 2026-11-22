import { describe, expect, it } from 'vitest';
import type { TopologyV1 } from './types';
import { IntegrityError, validateCatalog, validateScenario } from './validator';

const mockTopology: TopologyV1 = {
  schema_version: '1.0.0',
  topology_id: 'h2_simnet_center_v1',
  is_schematic: true,
  coordinate_note: 'Schematic only',
  nodes: [
    { id: 'N1', label: 'Source', kind: 'source', x: 0, y: 0, z: 0 },
    { id: 'N2', label: 'Junction', kind: 'junction', x: 1, y: 0, z: 0 },
  ],
  edges: [
    { id: 'G3', label: 'Pipe G3', source: 'N1', target: 'N2', component_group: 'G3' },
  ],
  sensors: [{ channel_id: 'PS1', attached_to: 'N1', variable: 'pressure' }],
};

const validScenario = {
  schema_version: '1.0.0',
  id: 'scen_test',
  provenance_status: 'FIXTURE_ONLY',
  topology_id: 'h2_simnet_center_v1',
  time_seconds: [0, 1, 2],
  sensor_channels: [
    {
      id: 'PS1',
      node_or_edge: 'N1',
      variable: 'pressure',
      unit: 'MPa',
      pressure_reference: 'absolute',
      values: [3.7, null, 3.5],
      observable: true,
    },
  ],
  event: {
    ground_truth_class: 'LEAK_G3',
    onset_time: 1,
    end_time: 2,
    true_edges_or_nodes: ['G3'],
    label_status: 'VERIFIED',
  },
  model_result: {
    experiment_id: 'exp_01',
    artifact_hash: 'abc1234',
    model_version: 'v1',
    predicted_class: 'LEAK_G3',
    decision: 'SPECIFIC',
    reason_code: 'HIGH_MARGIN',
    reason_summary: 'Distinct pressure drop across G3.',
    score: 0.91,
    score_definition: 'Selective margin',
    timestamp_scope: 'window_post_onset',
  },
  location_prediction: null,
};

describe('v1 contract validator (fail-closed)', () => {
  it('accepts a valid scenario with null samples and null localization', () => {
    const res = validateScenario(validScenario, mockTopology, false);
    expect(res.id).toBe('scen_test');
    expect(res.sensor_channels[0].values[1]).toBeNull();
  });

  it('rejects non-monotonic time_seconds', () => {
    const broken = { ...validScenario, time_seconds: [0, 2, 1] };
    expect(() => validateScenario(broken, mockTopology, false)).toThrow(IntegrityError);
  });

  it('rejects mismatched vector length', () => {
    const broken = {
      ...validScenario,
      sensor_channels: [{ ...validScenario.sensor_channels[0], values: [3.7, 3.6] }],
    };
    expect(() => validateScenario(broken, mockTopology, false)).toThrow(IntegrityError);
  });

  it('rejects unsupported decision enum', () => {
    const broken = {
      ...validScenario,
      model_result: { ...validScenario.model_result, decision: 'MAYBE' },
    };
    expect(() => validateScenario(broken, mockTopology, false)).toThrow(IntegrityError);
  });

  it('rejects location_prediction when localization is unsupported', () => {
    const broken = {
      ...validScenario,
      location_prediction: {
        predicted_edge_or_node: 'G3',
        metric_name: 'edge_match',
        error_value: 0,
        error_unit: 'edges',
      },
    };
    expect(() => validateScenario(broken, mockTopology, false)).toThrow(IntegrityError);
  });

  it('rejects catalog with malformed sha256', () => {
    expect(() =>
      validateCatalog({
        schema_version: '1.0.0',
        supported_features: {
          localization: false,
          inference: true,
          baseline_comparison: true,
          gas_comparison: false,
          operating_condition_analysis: false,
        },
        scenarios: [{ id: 's1', sha256: 'not-a-hash' }],
      })
    ).toThrow(IntegrityError);
  });
});
