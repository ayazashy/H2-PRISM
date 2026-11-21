### V2-T08_r2_class_metrics — R2 descriptive class metrics (all windows, undisputed runs, per topology)

Window-level metrics on dependent windows; labels disputed in 36/57 runs (D1); EXPLORATORY.

| scope | cls | support_windows | support_runs | support_families | support_ancestors | precision | recall | f1 | balanced_accuracy | macro_f1 | classes_present |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_windows | NORMAL | 1995 | 3 | 3 | 1 | 0.1538 | 0.6667 | 0.25 |  |  |  |
| all_windows | LEAK | 21921 | 39 | 30 | 13 | 0.9567 | 0.6667 | 0.7858 |  |  |  |
| all_windows | COMPRESSOR_FAULT | 3984 | 6 | 3 | 2 | 0.9915 | 0.9977 | 0.9946 |  |  |  |
| all_windows | COMPRESSOR_DELAY | 93 | 3 | 3 | 1 | 1 | 0.6667 | 0.8 |  |  |  |
| all_windows | ALL | 27993 | 51 | 39 | 17 |  | 0.7138 |  | 0.7494 | 0.7076 | 4 |
| undisputed_runs_only | NORMAL | 1995 | 3 | 3 | 1 | 1 | 0.6667 | 0.8 |  |  |  |
| undisputed_runs_only | LEAK | 7307 | 13 | 10 | 13 | 0.9169 | 1 | 0.9567 |  |  |  |
| undisputed_runs_only | COMPRESSOR_FAULT | 1328 | 2 | 1 | 2 | 0.9977 | 1 | 0.9989 |  |  |  |
| undisputed_runs_only | COMPRESSOR_DELAY | 31 | 1 | 1 | 1 | 1 | 1 | 1 |  |  |  |
| undisputed_runs_only | ALL | 10661 | 19 | 15 | 17 |  | 0.9376 |  | 0.9167 | 0.9389 | 4 |
| topology=Center | NORMAL | 665 | 1 | 1 | 1 | 0.08332 | 1 | 0.1538 |  |  |  |
| topology=Center | LEAK | 7307 | 13 | 10 | 13 |  | 0 | 0 |  |  |  |
| topology=Center | COMPRESSOR_FAULT | 1328 | 2 | 1 | 2 | 0.977 | 0.9932 | 0.9851 |  |  |  |
| topology=Center | COMPRESSOR_DELAY | 31 | 1 | 1 | 1 |  | 0 | 0 |  |  |  |
| topology=Center | ALL | 9331 | 17 | 13 | 17 |  | 0.2126 |  | 0.4983 | 0.2847 | 4 |
| topology=Downstream | NORMAL | 665 | 1 | 1 | 1 |  | 0 | 0 |  |  |  |
| topology=Downstream | LEAK | 7307 | 13 | 10 | 13 | 0.9169 | 1 | 0.9567 |  |  |  |
| topology=Downstream | COMPRESSOR_FAULT | 1328 | 2 | 1 | 2 | 0.9977 | 1 | 0.9989 |  |  |  |
| topology=Downstream | COMPRESSOR_DELAY | 31 | 1 | 1 | 1 | 1 | 1 | 1 |  |  |  |
| topology=Downstream | ALL | 9331 | 17 | 13 | 17 |  | 0.9287 |  | 0.75 | 0.7389 | 4 |
| topology=Upstream | NORMAL | 665 | 1 | 1 | 1 | 1 | 1 | 1 |  |  |  |
| topology=Upstream | LEAK | 7307 | 13 | 10 | 13 | 1 | 1 | 1 |  |  |  |
| topology=Upstream | COMPRESSOR_FAULT | 1328 | 2 | 1 | 2 | 1 | 1 | 1 |  |  |  |
| topology=Upstream | COMPRESSOR_DELAY | 31 | 1 | 1 | 1 | 1 | 1 | 1 |  |  |  |
| topology=Upstream | ALL | 9331 | 17 | 13 | 17 |  | 1 |  | 1 | 1 | 4 |
