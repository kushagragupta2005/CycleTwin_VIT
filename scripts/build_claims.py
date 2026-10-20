"""Build the machine-readable source of publishable claims from actual artifacts."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.personas import make_kushi
from src.generator import generate
from src.splits import patient_partition
from scripts.deliverable_content import compose


def build(write=True):
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
    claims['configuration']={'days':sorted({int(k.split('_')[1]) for k in keys}),
                             'tiers':sorted({int(k.rsplit('_',1)[1]) for k in keys}),
                             'event_cutoff_day':21,'confidence_level':0.95,'short_video_minutes':3,
                             'inference_seed':97,'display_seed':223,'classification_tolerance':1e-12,
                             'limitations_minutes':3,'guardrail_observed_nights':8,'guardrail_window_nights':14}
    all_rows=[r for seed in results['seeds'] for r in generate(int(seed))]
    example=next(iter(results['seeds'].values()))['patients']
    claims['dataset']={'people':len({r['patient'] for r in all_rows}),'cycles':len(all_rows),
                       'positive_cycles':sum(r['event'] for r in all_rows),
                       'per_seed_train_people':example['train'],'per_seed_validation_people':example['validation'],
                       'per_seed_test_people':example['test']}
    claims['runtime_requirements']=[line.strip() for line in (ROOT/'requirements.txt').read_text().splitlines() if line.strip() and not line.startswith('#')]
    claims['models']=json.loads((ROOT/'models/model_card.json').read_text())['models']
    submission=ROOT/'docs/submission_status.json'
    claims['submission']=json.loads(submission.read_text()) if submission.exists() else None
    claims['deliverables']=compose(claims)
    if write:
        (ROOT / "docs/claims.json").write_text(json.dumps(claims, indent=2) + "\n")
    return claims


if __name__ == "__main__":
    x = build(write='--check' not in sys.argv)
    if '--check' in sys.argv:
        if x != json.loads((ROOT/'docs/claims.json').read_text()):
            raise SystemExit('Claims are stale: run python scripts/build_claims.py')
    print(f"Built synthetic claims from {len(x['development']['seeds'])} development seeds; frozen results present: {x['frozen'] is not None}")
