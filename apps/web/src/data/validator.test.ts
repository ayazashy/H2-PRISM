import { describe, expect, it, vi } from 'vitest';
import type { CatalogScenarioEntry, TopologyV1 } from './types';
import { loadScenarioVerified } from './loader';
import { IntegrityError, sha256Hex, validateCatalog, validateScenario } from './validator';

const mockTopology: TopologyV1 = {
  schema_version: '1.0.0',
  topology_id: 'h2_simnet_center_v1',
  is_schematic: true,
  coordinate_note: 'Schematic only',
  nodes: [
    { id: 'N47', label: 'Source', kind: 'source', x: 0, y: 0, z: 0 },
    { id: 'N50', label: 'Junction', kind: 'junction', x: 1, y: 0, z: 0 },
  ],
  edges: [
    { id: 'Pipe_G1', label: 'Pipe G1', source: 'N47', target: 'N50', component_group: 'G1' },
  ],
  sensors: [{ channel_id: 'PS1', attached_to: 'N50', variable: 'pressure' }],
};

const validScenario = {
  schema_version: '1.0.0',
  id: 'scen_test',
  provenance_status: 'VERIFIED_EXPORT',
  source_artifact: 'data/sample/leakG4.parquet',
  topology_id: 'h2_simnet_center_v1',
  decimation_note: 'Test fixture',
  time_seconds: [0, 1, 2],
  sensor_channels: [
    {
      id: 'PS1',
      node_or_edge: 'N50',
      variable: 'pressure',
      unit: 'MPa',
      pressure_reference: 'absolute',
      values: [3.7, null, 3.5],
      observable: true,
    },
  ],
  event: {
    ground_truth_class: 'LEAK',
    onset_time: 1,
    end_time: 2,
    true_edges_or_nodes: ['Pipe_G1'],
    label_status: 'AUDITED_SAMPLE_PARQUET',
  },
  model_result: null,
  location_prediction: null,
};

describe('v1 contract validator & loader (fail-closed)', () => {
  it('accepts a valid scenario with null samples, null inference, and null localization', () => {
    const res = validateScenario(validScenario, mockTopology, false);
    expect(res.id).toBe('scen_test');
    expect(res.sensor_channels[0].values[1]).toBeNull();
    expect(res.model_result).toBeNull();
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

  it('rejects empty sensor_channels', () => {
    const broken = { ...validScenario, sensor_channels: [] };
    expect(() => validateScenario(broken, mockTopology, false)).toThrow(IntegrityError);
  });

  it('rejects unsupported decision enum', () => {
    const broken = {
      ...validScenario,
      model_result: {
        experiment_id: 'exp_01',
        artifact_hash: 'abc1234',
        model_version: 'v1',
        predicted_class: 'LEAK',
        decision: 'MAYBE',
        reason_code: 'X',
        reason_summary: 'X',
        score: 0.5,
        score_definition: 'Margin',
        timestamp_scope: 'window',
      },
    };
    expect(() => validateScenario(broken, mockTopology, false)).toThrow(IntegrityError);
  });

  it('rejects location_prediction when localization is unsupported', () => {
    const broken = {
      ...validScenario,
      location_prediction: {
        predicted_edge_or_node: 'Pipe_G1',
        metric_name: 'edge_match',
        error_value: 0,
        error_unit: 'edges',
      },
    };
    expect(() => validateScenario(broken, mockTopology, false)).toThrow(IntegrityError);
  });

  it('rejects catalog with malformed sha256 or empty scenarios', () => {
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
        scenarios: [],
      })
    ).toThrow(IntegrityError);
  });

  it('fails closed on SHA-256 checksum mismatch during scenario fetch', async () => {
    const raw = JSON.stringify(validScenario);
    const realHash = await sha256Hex(raw);
    const wrongHash = realHash.replace(/^./, realHash[0] === 'a' ? 'b' : 'a');

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        text: async () => raw,
      })
    );

    const entry: CatalogScenarioEntry = {
      id: 'scen_test',
      display_name: 'Test',
      family_id: 'fam',
      scenario_class: 'LEAK',
      summary_hint: 'hint',
      data_path: 'data/scenarios/scen_test.json',
      sha256: wrongHash,
      gas_metadata_status: 'test',
      topology_id: 'h2_simnet_center_v1',
      provenance_status: 'VERIFIED_EXPORT',
      split: 'test',
      time_range: [0, 2],
      samples: 3,
      publish_approved: true,
    };

    await expect(loadScenarioVerified(entry, mockTopology, false)).rejects.toThrow(
      /Integrity check failed/
    );
    vi.unstubAllGlobals();
  });
});
