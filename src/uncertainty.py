"""Independent synthetic calibration illustrations, matched to fitted tier and snapshot.

Frozen synthetic coverage is reported separately. Day bands are conditional on
ovulation being present; absence has no numerical ovulation day.
"""
from functools import lru_cache
from src.conformal import calibrate_binary, calibrate_ovulation_interval, classification_set, ovulation_interval
from src.features import attach_prior_cycle_lengths
from src.generator import generate
from src.inference import predict
from src.model import estimate_ovulation_day

CALIBRATION_SEED = 211


@lru_cache(maxsize=1)
def calibration_records():
    return [r for r in attach_prior_cycle_lengths(generate(CALIBRATION_SEED, patients=240, cycles=2)) if r["cycle"] == 1]


@lru_cache(maxsize=48)
def calibration_for(day, tier, seed=97):
    rows = calibration_records()
    outputs = [predict(r, day, tier, seed=seed) for r in rows]
    q_cls = calibrate_binary([r["event"] for r in rows], [o["prob"] for o in outputs])
    observed = [(r, o) for r, o in zip(rows, outputs) if r["ovulation_day"] > 0]
    q_day = calibrate_ovulation_interval([r["ovulation_day"] for r, _ in observed],
               [estimate_ovulation_day(r, day, o["selected_tier"]) for r, o in observed])
    return {"q_class": q_cls, "q_day": q_day, "n_class": len(rows), "n_day": len(observed),
            "seed": CALIBRATION_SEED, "alpha": 0.10,
            "scope": "synthetic marginal display illustration; matched frozen coverage is reported separately"}


def uncertainty(record, day, tier, output):
    if output.get("abstain"):
        return {"estimate": None, "interval": None, "class_set": None}
    cal = calibration_for(day, tier, output["seed"])
    estimate = estimate_ovulation_day(record, day, output["selected_tier"])
    return {"estimate": estimate, "interval": ovulation_interval(estimate, cal["q_day"]),
            "class_set": classification_set(output["prob"], cal["q_class"]), "calibration": cal,
            "condition": "day band conditional on an ovulatory cycle; no day exists for absent ovulation"}
