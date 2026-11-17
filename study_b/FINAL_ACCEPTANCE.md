# Scientific acceptance

**ACCEPTED WITH LIMITATIONS**

Study B is scientifically complete within its declared experimental scope.

The verification reads the official ZIP, checks source size and hashes, and reopens the eight eligible workbooks to check channel units, timestamps, the frozen split, and eligible counts. Persistence MAE and RMSE were recalculated directly from aligned observations. Saved Ridge per-run metrics reconcile to the published run means. Ridge predictions were transient in the original code, so their observation-level errors and the origin of their squared-error reductions cannot be independently recovered without replay. The original fit and evaluation were left untouched. [Read-only verifier](verify_publication.py) · [Frozen implementation](benchmark.py) · [Source manifest](source_manifest.json)

The forecast uses only the current P-2 and MFC-3 values. Persistence copies them. The standardized ridge correction uses the same inputs and is fitted exclusively to development changes. Eligibility checks use the later row only to establish whether the observed target can be scored. Every pair lies within a workbook and must pass both the raw Seconds counter and wall-clock checks. The accepted test intervals span 0.992–1.008 s. The split is by recording group, with two held-out recording dates and three held-out workbooks. Shared equipment and unknown cross-day histories limit independence. [Protocol](PROTOCOL.md) · [Split manifest](split_manifest.csv) · [Results](RESULTS.md)

The prior Figure 2 exports are the only saved prediction traces. They were retained byte-for-byte, including their original slate persistence style. Figures 1 and 3 were redesigned from verified metadata and the saved metrics. The package uses captions to communicate timing, coverage and interpretation. No numerical correction to the benchmark was required.

The focused suite passed all three tests. The relevant repository suite passed 30 tests and skipped five. Graphic QA inspected the rendered PNGs and checked SVG parseability, PDF signatures, PNG resolution, and byte identity of Figure 2.
