"""Read generated claims, never hand-maintained benchmark numbers."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_claims():
    return json.loads((ROOT / "docs/claims.json").read_text())
