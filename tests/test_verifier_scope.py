"""Regression tests for the v1 verifier's protected-scope check (scope_check.py).

Later independent packages must not invalidate v1, but unauthorized changes to protected files must still be detected:
modifications, deletions, unregistered additions, and authorized files whose content later drifts.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_results/integrated_validation_v1/publication_q1/scripts"))
import scope_check as sc  # noqa: E402

COLS = ["kind", "scope", "path", "baseline_commit", "baseline_sha256", "authorized_sha256", "issue", "rationale", "recorded", "superseded"]


def git(repo, *a):
    return subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def h(b):
    return hashlib.sha256(b).hexdigest()


@pytest.fixture()
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.invalid")
    git(tmp_path, "config", "user.name", "test")
    git(tmp_path, "config", "core.autocrlf", "false")
    (tmp_path / "frozen").mkdir()
    (tmp_path / "frozen/result.csv").write_bytes(b"a,b\n1,2\n")
    (tmp_path / "frozen/config.yaml").write_bytes(b"k: 1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "baseline")
    return tmp_path, git(tmp_path, "rev-parse", "HEAD")


def commit(repo, msg="change"):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


def reg(*rows):
    return pd.DataFrame([dict(zip(COLS, r + ("",) * (len(COLS) - len(r)))) for r in rows], columns=COLS)


def verdicts(repo, base, register):
    df = sc.evaluate(repo, register, "outside_v1", base, spec=["."], exempt=set())
    return dict(zip(df.path, df.verdict))


def test_independent_package_does_not_invalidate(repo):
    r, base = repo
    (r / "pkg_v2").mkdir()
    (r / "pkg_v2/a.csv").write_bytes(b"x\n")
    commit(r)
    assert verdicts(r, base, reg(("ADD_PREFIX", "outside_v1", "pkg_v2/"))) == {"pkg_v2/a.csv": "AUTHORIZED"}


def test_unregistered_addition_is_detected(repo):
    r, base = repo
    (r / "stray.txt").write_bytes(b"x\n")
    commit(r)
    assert verdicts(r, base, reg(("ADD_PREFIX", "outside_v1", "pkg_v2/"))) == {"stray.txt": "UNAUTHORIZED"}


def test_unauthorized_modification_of_protected_file_is_detected(repo):
    r, base = repo
    (r / "frozen/result.csv").write_bytes(b"a,b\n1,3\n")
    commit(r)
    assert verdicts(r, base, reg()) == {"frozen/result.csv": "UNAUTHORIZED"}


def test_authorized_modification_passes_and_later_drift_is_detected(repo):
    r, base = repo
    old = h(b"k: 1\n")
    (r / "frozen/config.yaml").write_bytes(b"k: 1  # documented\n")
    commit(r)
    R = reg(("MODIFY", "outside_v1", "frozen/config.yaml", base, old, h(b"k: 1  # documented\n"), "TEST"))
    assert verdicts(r, base, R) == {"frozen/config.yaml": "AUTHORIZED"}
    (r / "frozen/config.yaml").write_bytes(b"k: 2\n")
    commit(r, "drift")
    assert verdicts(r, base, R) == {"frozen/config.yaml": "UNAUTHORIZED"}


def test_deletion_requires_registration_with_baseline_hash(repo):
    r, base = repo
    (r / "frozen/result.csv").unlink()
    commit(r)
    assert verdicts(r, base, reg()) == {"frozen/result.csv": "UNAUTHORIZED"}
    good = reg(("DELETE", "outside_v1", "frozen/result.csv", base, h(b"a,b\n1,2\n"), "", "TEST"))
    assert verdicts(r, base, good) == {"frozen/result.csv": "AUTHORIZED"}
    wrong = reg(("DELETE", "outside_v1", "frozen/result.csv", base, h(b"other"), "", "TEST"))
    assert verdicts(r, base, wrong) == {"frozen/result.csv": "UNAUTHORIZED"}


def test_superseded_row_no_longer_authorizes(repo):
    r, base = repo
    (r / "frozen/config.yaml").write_bytes(b"k: 9\n")
    commit(r)
    R = reg(("MODIFY", "outside_v1", "frozen/config.yaml", base, h(b"k: 1\n"), h(b"k: 9\n"), "TEST", "", "", "superseded"))
    assert verdicts(r, base, R) == {"frozen/config.yaml": "UNAUTHORIZED"}


def test_uncommitted_change_is_reported(repo):
    r, _ = repo
    (r / "frozen/result.csv").write_bytes(b"tampered\n")
    assert sc.uncommitted(r, ["frozen"], exempt=set()) == ["frozen/result.csv"]


def test_real_repository_register_is_complete():
    """On the committed repository, every change since both baselines is authorized or exempt."""
    register = sc.load_register(ROOT)
    for scope, cfg in sc.SCOPES.items():
        df = sc.evaluate(ROOT, register, scope, cfg["base"])
        assert (df.verdict != "UNAUTHORIZED").all(), df[df.verdict == "UNAUTHORIZED"].to_string()
