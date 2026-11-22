export type ProvenanceStatus = 'VERIFIED_EXPORT' | 'FIXTURE_ONLY';
export type DecisionKind = 'SPECIFIC' | 'AMBIGUOUS' | 'UNRESOLVED';
export type SplitKind = 'train' | 'dev' | 'test' | 'fixture';

export interface SupportedFeatures {
  localization: boolean;
  inference: boolean;
  baseline_comparison: boolean;
  gas_comparison: boolean;
  operating_condition_analysis: boolean;
}

export interface CatalogScenarioEntry {
  id: string;
  display_name: string;
  family_id: string;
  scenario_class: string;
  summary_hint: string;
  data_path: string;
  sha256: string;
  gas_metadata_status: string;
  topology_id: string;
  provenance_status: ProvenanceStatus;
  split: SplitKind;
  time_range: [number, number];
  samples: number;
  publish_approved: boolean;
}

export interface MetricsCatalogEntry {
  id: string;
  title: string;
  data_path: string;
  sha256: string;
}

export interface CatalogV1 {
  schema_version: '1.0.0';
  release_id: string;
  build_utc: string;
  source_repository_commit: string;
  data_release_checksum: string;
  label_set: string[];
  supported_features: SupportedFeatures;
  scenarios: CatalogScenarioEntry[];
  metrics_catalog: MetricsCatalogEntry[];
}

export interface SensorChannel {
  id: string;
  node_or_edge: string;
  variable: 'pressure' | 'mass_flow';
  unit: string;
  pressure_reference: 'absolute' | 'gauge' | null;
  values: (number | null)[];
  observable: boolean;
}

export interface ScenarioEvent {
  ground_truth_class: string;
  onset_time: number | null;
  end_time: number | null;
  true_edges_or_nodes: string[] | null;
  label_status: string;
}

export interface ModelResult {
  experiment_id: string;
  artifact_hash: string;
  model_version: string;
  predicted_class: string | null;
  decision: DecisionKind;
  reason_code: string;
  reason_summary: string;
  score: number | null;
  score_definition: string | null;
  timestamp_scope: string;
}

export interface LocationPrediction {
  predicted_edge_or_node: string;
  metric_name: string;
  error_value: number | null;
  error_unit: string | null;
}

export interface ScenarioPayloadV1 {
  schema_version: '1.0.0';
  id: string;
  provenance_status: ProvenanceStatus;
  topology_id: string;
  time_seconds: number[];
  sensor_channels: SensorChannel[];
  event: ScenarioEvent;
  model_result: ModelResult;
  location_prediction: LocationPrediction | null;
}

export interface TopologyNode {
  id: string;
  label: string;
  kind: 'source' | 'junction' | 'compressor' | 'delivery';
  x: number;
  y: number;
  z: number;
}

export interface TopologyEdge {
  id: string;
  label: string;
  source: string;
  target: string;
  component_group: string;
}

export interface TopologySensor {
  channel_id: string;
  attached_to: string;
  variable: 'pressure' | 'mass_flow';
}

export interface TopologyV1 {
  schema_version: '1.0.0';
  topology_id: string;
  is_schematic: boolean;
  coordinate_note: string;
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  sensors: TopologySensor[];
}

export interface MetricsV1 {
  schema_version: '1.0.0';
  split: string;
  artifact_hash: string;
  cohort_n: number;
  ci_method: string;
  summary: {
    coverage: number;
    selective_risk: number;
    fpar: number;
    leak_recall: number;
  };
  confusion_matrix: {
    labels: string[];
    matrix: number[][];
    supports: number[];
  };
  risk_coverage: {
    coverage: number;
    h2_prism_risk: number;
    baseline_risk: number | null;
  }[];
}
