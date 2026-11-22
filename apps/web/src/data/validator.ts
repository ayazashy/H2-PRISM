import type { CatalogV1, ScenarioPayloadV1, TopologyV1 } from './types';

export class IntegrityError extends Error {
  public readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = 'IntegrityError';
    this.code = code;
  }
}

const VALID_DECISIONS = new Set(['SPECIFIC', 'AMBIGUOUS', 'UNRESOLVED']);

export async function sha256Hex(rawText: string): Promise<string> {
  const bytes = new TextEncoder().encode(rawText);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export function validateCatalog(data: unknown): CatalogV1 {
  if (!data || typeof data !== 'object') {
    throw new IntegrityError('CATALOG_INVALID', 'Catalog payload is not an object.');
  }
  const c = data as Partial<CatalogV1>;
  if (c.schema_version !== '1.0.0') {
    throw new IntegrityError('SCHEMA_VERSION_MISMATCH', `Unsupported catalog schema_version: ${String(c.schema_version)}`);
  }
  if (!c.supported_features || typeof c.supported_features !== 'object') {
    throw new IntegrityError('MISSING_FEATURES', 'Catalog missing supported_features.');
  }
  if (!Array.isArray(c.scenarios) || c.scenarios.length === 0) {
    throw new IntegrityError('EMPTY_CATALOG', 'Catalog contains zero scenarios.');
  }
  const seenIds = new Set<string>();
  for (const s of c.scenarios) {
    if (!s.id || seenIds.has(s.id)) {
      throw new IntegrityError('DUPLICATE_SCENARIO_ID', `Invalid or duplicate scenario id: ${String(s.id)}`);
    }
    seenIds.add(s.id);
    if (!/^[a-f0-9]{64}$/.test(s.sha256)) {
      throw new IntegrityError('INVALID_CHECKSUM', `Scenario ${s.id} has malformed sha256.`);
    }
  }
  return c as CatalogV1;
}

export function validateScenario(
  data: unknown,
  topology: TopologyV1,
  localizationSupported: boolean
): ScenarioPayloadV1 {
  if (!data || typeof data !== 'object') {
    throw new IntegrityError('SCENARIO_INVALID', 'Scenario payload is not an object.');
  }
  const s = data as Partial<ScenarioPayloadV1>;
  if (s.schema_version !== '1.0.0') {
    throw new IntegrityError('SCHEMA_VERSION_MISMATCH', `Unsupported scenario schema_version: ${String(s.schema_version)}`);
  }
  if (s.topology_id !== topology.topology_id) {
    throw new IntegrityError('TOPOLOGY_MISMATCH', `Scenario topology ${String(s.topology_id)} !== ${topology.topology_id}`);
  }
  if (!Array.isArray(s.time_seconds) || s.time_seconds.length < 2) {
    throw new IntegrityError('TIME_ARRAY_INVALID', 'time_seconds must contain at least 2 samples.');
  }

  // Strictly increasing finite timestamps
  for (let i = 0; i < s.time_seconds.length; i++) {
    const t = s.time_seconds[i];
    if (typeof t !== 'number' || !Number.isFinite(t)) {
      throw new IntegrityError('NON_FINITE_TIME', `Non-finite timestamp at index ${i}.`);
    }
    if (i > 0 && t <= s.time_seconds[i - 1]) {
      throw new IntegrityError('NON_MONOTONIC_TIME', `time_seconds not strictly increasing at index ${i}.`);
    }
  }

  if (!Array.isArray(s.sensor_channels) || s.sensor_channels.length === 0) {
    throw new IntegrityError('EMPTY_SENSORS', 'Scenario has no sensor_channels.');
  }

  const validTargets = new Set([
    ...topology.nodes.map((n) => n.id),
    ...topology.edges.map((e) => e.id),
  ]);
  const seenChannels = new Set<string>();

  for (const ch of s.sensor_channels) {
    if (!ch.id || seenChannels.has(ch.id)) {
      throw new IntegrityError('DUPLICATE_CHANNEL', `Duplicate or empty channel id: ${String(ch.id)}`);
    }
    seenChannels.add(ch.id);

    if (!validTargets.has(ch.node_or_edge)) {
      throw new IntegrityError('UNKNOWN_TOPOLOGY_TARGET', `Channel ${ch.id} references unknown node/edge ${ch.node_or_edge}.`);
    }
    if (ch.variable === 'pressure' && ch.pressure_reference !== 'absolute' && ch.pressure_reference !== 'gauge') {
      throw new IntegrityError('MISSING_PRESSURE_REF', `Pressure channel ${ch.id} must declare absolute or gauge.`);
    }
    if (!Array.isArray(ch.values) || ch.values.length !== s.time_seconds.length) {
      throw new IntegrityError(
        'VECTOR_LENGTH_MISMATCH',
        `Channel ${ch.id} length (${ch.values?.length}) !== time_seconds (${s.time_seconds.length}).`
      );
    }
    for (let i = 0; i < ch.values.length; i++) {
      const v = ch.values[i];
      if (v !== null && (typeof v !== 'number' || !Number.isFinite(v))) {
        throw new IntegrityError('INVALID_SAMPLE', `Channel ${ch.id} has non-finite sample at index ${i}.`);
      }
    }
  }

  if (!s.model_result || !VALID_DECISIONS.has(s.model_result.decision)) {
    throw new IntegrityError('INVALID_DECISION', `Unsupported decision: ${String(s.model_result?.decision)}`);
  }

  // Event onset bounds check
  const tMin = s.time_seconds[0];
  const tMax = s.time_seconds[s.time_seconds.length - 1];
  if (s.event?.onset_time !== null && s.event?.onset_time !== undefined) {
    if (s.event.onset_time < tMin || s.event.onset_time > tMax) {
      throw new IntegrityError('ONSET_OUT_OF_RANGE', `Event onset_time ${s.event.onset_time} outside [${tMin}, ${tMax}].`);
    }
  }

  // Localization guardrail
  if (!localizationSupported && s.location_prediction !== null) {
    throw new IntegrityError('DISALLOWED_LOCALIZATION', 'location_prediction present while localization is unsupported.');
  }
  if (s.location_prediction !== null && s.location_prediction !== undefined) {
    if (!validTargets.has(s.location_prediction.predicted_edge_or_node)) {
      throw new IntegrityError(
        'INVALID_PREDICTED_LOCATION',
        `Predicted location ${s.location_prediction.predicted_edge_or_node} not in approved topology.`
      );
    }
  }

  return s as ScenarioPayloadV1;
}
