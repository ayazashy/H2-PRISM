# Reproduce the publication package

From the MHC worktree with Python 3.12 and the official MHC v1.2 archive available locally:

```powershell
python -m pip install -r study_b/requirements.txt
python study_b/verify_publication.py "<path-to-official-MHC-v1.2.zip>"
python study_b/test_benchmark.py
python study_b/publish.py
```

The verifier checks the source, opens the eligible workbooks, independently recomputes persistence with a separate eligibility loop, and reconciles reported run means. Publication generation uses committed CSV/JSON evidence to regenerate Tables 1 and 2 and Figures 1 and 3. Table 3 is the reviewed claims register. Figure 2 is preserved as the original publication trace. The original fitting command remains available in the frozen implementation. It was not executed during acceptance.

Relevant regression tests:

```powershell
python -m pytest -q tests/test_experimental_data.py tests/test_real_data_interfaces.py tests/test_splits.py tests/test_metrics.py
```

Source citation and CC BY 4.0 attribution appear in [SOURCE.md](SOURCE.md).
