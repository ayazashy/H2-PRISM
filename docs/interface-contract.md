# H2-PRISM Interface Contract (v1.0.0)

## Ownership & Freeze Rules
- **Schemas**: `contracts/schema/v1/*.schema.json`
- **Data Producer (`tools/data_pipeline/`)**: Exports `public/data/catalog.json`, `public/data/topology/*.json`, `public/data/scenarios/*.json`, and `public/data/metrics.json` with SHA-256 checksums.
- **UI Consumer (`apps/web/`)**: Validates every fetched artifact at runtime (structure + SHA-256 + invariants). Fails closed on any mismatch.

## Hard Invariants
1. `time_seconds` is strictly increasing; every `sensor_channels[].values` length equals `time_seconds.length`.
2. Missing samples remain `null` (never interpolated).
3. `pressure` channels declare `unit` and `pressure_reference` (`"absolute"` or `"gauge"`).
4. `model_result.decision` is strictly `"SPECIFIC" | "AMBIGUOUS" | "UNRESOLVED"`.
5. `location_prediction` is `null` unless `supported_features.localization === true` and predicted/true edges exist in `topology`.
6. `is_schematic: true` forces an explicit **"Schematic · Not to Physical Scale"** label in 2D and 3D views.
7. `provenance_status === "FIXTURE_ONLY"` must display a visible fixture banner; the word `LIVE` is forbidden.
