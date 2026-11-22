import sys
from pathlib import Path

# Ensure src/ is in sys.path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Make tests/synthetic_fixtures.py importable (SYNTHETIC test data only).
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))
