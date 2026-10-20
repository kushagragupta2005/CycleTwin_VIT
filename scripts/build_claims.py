"""Build the machine-readable source of publishable claims from actual artifacts."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.personas import make_kushi


def build():
    results = json.loads((ROOT / "results.json").read_text())
    summary = []
    keys = next(iter(results["seeds"].values()))["metrics"]
    for key in keys:
        values = [s["metrics"][key] for s in results["seeds"].values()]
        day, tier = int(key.split("_")[1]), int(key.rsplit("_", 1)[1])
        summary.append({"Forecast day": day, "Tier": tier, "Inputs": values[0]["tier_name"],
                        "Mean AUROC": float(np.mean([v["auroc"] for v in values])),
                        "Mean Brier": float(np.mean([v["brier"] for v in values])),
                        "Mean day MAE": float(np.mean([v["ovulation_day_mae"] for v in values])),
                        "Held-out cycles": sum(v["n_cycles"] for v in values),
                        "Seeds retaining candidate": sum(v["validation_selected_feature_tier"] == tier for v in values),
                        "scope": "synthetic development; not clinical performance"})
    kushi = make_kushi()
    persona = {k: v for k, v in kushi.items() if k != "cycles"}
    persona["cycles"] = [{"logical_cycle": s["logical_cycle"], "seed": s["seed"],
                         "patient": s["record"]["patient"], "truth_ovulation_day": s["record"]["ovulation_day"],
                         "truth_event": s["record"]["event"], "prior_lengths": s["record"]["prior_cycle_lengths"]}
                        for s in kushi["cycles"]]
    inputs = [ROOT / "results.json", ROOT / "models/model_card.json", ROOT / "docs/context_sources.json"]
    claims = {"scope": "Synthetic project results only; no diagnosis, hormone inference or clinical validity",
              "development": results, "summary": summary, "kushi": persona,
              "context": json.loads((ROOT / "docs/context_sources.json").read_text()),
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    frozen = ROOT / "results_final_frozen.json"
    claims["frozen"] = json.loads(frozen.read_text()) if frozen.exists() else None
    (ROOT / "docs/claims.json").write_text(json.dumps(claims, indent=2) + "\n")
    return claims


if __name__ == "__main__":
    x = build()
    print(f"Built synthetic claims from {len(x['development']['seeds'])} development seeds; frozen results present: {x['frozen'] is not None}")
