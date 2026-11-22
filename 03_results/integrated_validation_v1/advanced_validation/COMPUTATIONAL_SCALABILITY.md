# Computational scalability

Tables A14a–c; figure AV-F12; raw data in `benchmarks/`.

## Test setup

- **Hardware:** AMD Ryzen 5 7520U (4 cores / 8 logical CPUs), 7.2 GB RAM, Windows 11.
- **Software:** Python 3.12.1, NumPy 2.3.1. Thread-count environment variables were unset.
- **Measurement:**
  - single process, with one dimension varied at a time;
  - 2 warm-up runs, then 15 timed repetitions for formal D(Y) and 5 for D(x);
  - peak memory measured with tracemalloc, which counts Python allocations only.
- **Data:** formal D(Y) was timed on the real Center captures. D(x) was timed on **synthetic** arrays (128 features), so its numbers are a numerical benchmark only.
- **Exclusions:** rendering and figure time are not part of the latency.

## Results

| Component | Dimension | Range | Median latency | Log–log slope |
|---|---|---|---|---|
| D(Y) decision (6 hypotheses, 151 samples, ±1 s) | channels M | 1 → 13 | 25 → 364 ms | 1.02 |
| | hypotheses H | 1 → 6 | 58 → 341 ms | 0.98 |
| | window samples T | 31 → 151 | 70 → 352 ms | 1.06 |
| | clock shifts S | 1 → 101 | 371–388 ms (flat; early exit at the first separating coordinate or witness) | 0.00 |
| D(x) compute (500 queries, k = 25) | reference size N | 1k → 20k | 0.74 → 6.1 ms per query | 0.70 |
| | neighbours K | 10 → 50 | ≈ 3.0 ms per query | 0.03 |

- **Peak memory:** below 1 MB of Python allocations per D(Y) decision.
- **Measured per-decision cost across all 2,376 experiment decisions** (7 parallel workers, latest run): median 0.41 s, p95 1.11 s, p99 2.05 s, max 3.24 s. Contention between workers inflates the tail. The first run gave a median of 0.45 s, p95 0.78 s, p99 1.25 s and max 6.1 s; wall-clock values differ between runs.
- **One-off setup:** loading and hash-verifying the Center captures takes about 4 s.

## Interpretation

- Over the measured ranges, formal D(Y) latency grows about proportionally with channels, hypotheses and window length. The slopes describe this implementation, not a proven complexity class.
- The adapter confirms candidates in exact rational arithmetic. That is the main cost.
- No latency requirement has been specified for an online monitor, so real-time readiness cannot be claimed.
  - The measured latency is under 1 s per decision for 13 channels and 6 hypotheses.
  - That would fit, for example, a 5 s sampling cadence (HY2RES), but only under such a declared requirement.
