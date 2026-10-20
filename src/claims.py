"""Read generated claims, never hand-maintained benchmark numbers."""
import json
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=2)
def _read(path, modified):
    return json.loads(Path(path).read_text())


def load_claims():
    path=ROOT / 'docs/claims.json'
    return _read(str(path),path.stat().st_mtime_ns)
