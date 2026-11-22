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
  status_note?: string;
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
  source_artifact: string;
  topology_id: string;
  decimation_note: string;
  time_seconds: number[];
  sensor_channels: SensorChannel[];
  event: ScenarioEvent;
  model_result: ModelResult | null;
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

export interface ConfusionMatrixScope {
  labels: string[];
  matrix: number[][];
  supports: number[];
  total_windows: number;
}

export interface MatchedCoverageRow {
  method: string;
  target_coverage: number;
  coverage: number;
  selective_risk: number;
  n_specific: number;
  n_eligible: number;
  n_families: number;
  folds_estimable: number;
}

export interface RiskCoveragePoint {
  scope: string;
  method: string;
  coverage_requested: number;
  status: string;
  coverage: number | null;
  selective_risk: number | null;
  n_total: number | null;
  n_specific: number | null;
}

export interface ThreeOutcomeRow {
  class: string;
  scope: string;
  n_windows: number;
  n_runs: number;
  n_families: number;
  n_specific: number;
  n_specific_correct: number;
  n_ambiguity_set: number;
  n_ambiguity_includes_true: number;
  n_unresolved: number;
}

export interface FoldEstimabilityRow {
  fold: number;
  method: string;
  target: number;
  status: string;
  test_max_attainable_coverage: number;
}

export interface MetricsV1 {
  schema_version: '1.0.0';
  run_key: string;
  git_commit: string;
  split: string;
  artifact_hash: string;
  cohort_n: number;
  estimable_n: number;
  ci_method: string;
  rq1_status: string;
  rq1_note: string;
  matched_coverage_06: MatchedCoverageRow[];
  confusion_matrices_by_scope: Record<string, ConfusionMatrixScope>;
  risk_coverage_series: RiskCoveragePoint[];
  three_outcome_by_class: ThreeOutcomeRow[];
  estimability_by_fold: FoldEstimabilityRow[];
  prohibited_claims: string[];
  source_artifacts: string[];
}
