import type { CatalogV1, MetricsV1, ScenarioPayloadV1, TopologyV1 } from './types';
import { IntegrityError, sha256Hex, validateCatalog, validateScenario } from './validator';

const scenarioCache = new Map<string, ScenarioPayloadV1>();
const topologyCache = new Map<string, TopologyV1>();

async function fetchJsonText(path: string, signal?: AbortSignal): Promise<{ text: string; json: unknown }> {
  const base = import.meta.env.BASE_URL || '/';
  const normalizedBase = base.endsWith('/') ? base : `${base}/`;
  const cleanPath = path.replace(/^\/+/, '');
  const url = `${normalizedBase}${cleanPath}`;
  const res = await fetch(url, { signal });
  if (!res.ok) {
    throw new IntegrityError('FETCH_FAILED', `Failed to load ${url} (HTTP ${res.status}).`);
  }
  const text = await res.text();
  try {
    return { text, json: JSON.parse(text) };
  } catch {
    throw new IntegrityError('INVALID_JSON', `Malformed JSON in ${url}.`);
  }
}

export async function loadCatalog(signal?: AbortSignal): Promise<CatalogV1> {
  const { json } = await fetchJsonText('/data/catalog.json', signal);
  return validateCatalog(json);
}

export async function loadTopology(topologyId: string, signal?: AbortSignal): Promise<TopologyV1> {
  const cached = topologyCache.get(topologyId);
  if (cached) return cached;
  const { json } = await fetchJsonText(`/data/topology/${topologyId}.json`, signal);
  const topo = json as TopologyV1;
  if (!topo || topo.schema_version !== '1.0.0' || topo.topology_id !== topologyId) {
    throw new IntegrityError('TOPOLOGY_INVALID', `Invalid topology payload for ${topologyId}.`);
  }
  topologyCache.set(topologyId, topo);
  return topo;
}

export async function loadScenarioVerified(
  entry: CatalogV1['scenarios'][number],
  topology: TopologyV1,
  localizationSupported: boolean,
  signal?: AbortSignal
): Promise<ScenarioPayloadV1> {
  const cacheKey = `${entry.id}:${entry.sha256}`;
  const cached = scenarioCache.get(cacheKey);
  if (cached) return cached;

  const { text, json } = await fetchJsonText(entry.data_path, signal);
  const actualHash = await sha256Hex(text);
  if (actualHash !== entry.sha256) {
    throw new IntegrityError(
      'CHECKSUM_MISMATCH',
      `Integrity check failed for ${entry.id}: expected ${entry.sha256.slice(0, 12)}…, got ${actualHash.slice(0, 12)}….`
    );
  }

  const validated = validateScenario(json, topology, localizationSupported);
  scenarioCache.set(cacheKey, validated);
  return validated;
}

export async function loadMetricsVerified(
  entry: CatalogV1['metrics_catalog'][number],
  signal?: AbortSignal
): Promise<MetricsV1> {
  const { text, json } = await fetchJsonText(entry.data_path, signal);
  const actualHash = await sha256Hex(text);
  if (actualHash !== entry.sha256) {
    throw new IntegrityError(
      'METRICS_CHECKSUM_MISMATCH',
      `Metrics integrity check failed for ${entry.id}.`
    );
  }
  return json as MetricsV1;
}
