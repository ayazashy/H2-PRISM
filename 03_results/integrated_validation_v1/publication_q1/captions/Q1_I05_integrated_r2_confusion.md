# Q1_I05 — R2 classification by topology

**Scientific question.** Where does the registered classifier err?

**Caption.** Window-count confusion matrices of the registered R2 classifier per held-out topology (shading: row share). Center LEAK → NORMAL (7,307 windows) and Downstream NORMAL → LEAK (662) are the dominant errors; both trace to the source-folder attribution defect (D1 pending). Upstream is error-free. Windows are serially dependent; independent units are scenario families and ancestors (Q1_I06).

**Interpretation limit.** Simulated topologies; inspected outer test; counts of dependent windows.

**Source data.**
- `03_results/primary_protocol/PRIMARY/confusion_matrix.csv`

**Code.** `scripts/fig_integrated.py::plot_integrated_r2_confusion` · Files: `figures/Q1_I05_integrated_r2_confusion.png`, `figures/Q1_I05_integrated_r2_confusion.svg`
