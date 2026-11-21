"""Regression test for L20: two windowing implementations coexist without changing either.

h2prism.windows is the frozen Center/F3 module (bytes of h2prism-center-baseline-v1, restored by 6eddd4a).
h2prism.simnet_windows is the H2-SimNet Stage-2 module from 9fa470c, restored byte-for-byte under its own name, and the
Stage-2 runner (formerly h2prism/experiments.py, shadowed by the h2prism.experiments package) is h2prism.simnet_experiments, so
evaluation.py and simnet_experiments.py import again. Neither windows file may drift; their public APIs stay disjoint.
"""
import ast
import hashlib
import importlib
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src/h2prism"
FROZEN_WINDOWS_SHA256 = "c4660efb2631b85f3748ee64463692e5a5eafde9c334c12211de541939797a66"      # 6fee8a0 / 6eddd4a
STAGE2_WINDOWS_SHA256 = "25784162932ecee33fc7dd98339c2360a82c1885db2107096d82ad2e06dd1012"      # 9fa470c windows.py


def lf_sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_both_window_modules_are_unchanged():
    assert lf_sha(SRC / "windows.py") == FROZEN_WINDOWS_SHA256
    assert lf_sha(SRC / "simnet_windows.py") == STAGE2_WINDOWS_SHA256


def test_both_apis_import_and_are_disjoint():
    frozen, stage2 = importlib.import_module("h2prism.windows"), importlib.import_module("h2prism.simnet_windows")
    assert {"WindowConfig", "generate_windows", "check_window_manifest"} <= set(dir(frozen))
    assert {"SENSOR_CHANNELS", "TARGET_CLASSES", "map_target_class", "build_window_dataset"} <= set(dir(stage2))
    def defined(path):          # top-level public names defined (not imported) in the module source
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    names |= {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
        return {n for n in names if not n.startswith("_")}
    assert not defined(SRC / "windows.py") & defined(SRC / "simnet_windows.py")


def test_stage2_pipeline_modules_import():
    importlib.import_module("h2prism.evaluation")
    importlib.import_module("h2prism.simnet_experiments")
