"""Predeclared synthetic stories selected without ever consulting model output."""
from functools import lru_cache
import numpy as np
from src.features import attach_prior_cycle_lengths
from src.generator import generate

KUSHI_SEEDS = (2107, 2108, 2109)
KUSHI_PROFILE = {"name": "Kushi", "age": 21, "bmi": 27.0, "family_history": 1,
                 "study_year": 3, "course": "B.Tech", "usual_reported_cycle_range": [38, 45],
                 "story": "Hostel life, exam-season sleep debt, mother with type 2 diabetes, smartwatch wearer.",
                 "scope": "Fictional synthetic persona - not a real patient - not performance evidence."}
SELECTION_RULE = ("Fixed seed, PMOS_A, seventh generated cycle with ground-truth ovulation day in [30,38]; "
                  "median of six preceding generated lengths in the fictional usual range [38,45]; "
                  "choose the lowest patient index. No prediction is consulted.")


@lru_cache(maxsize=4)
def make_kushi(seed=2107):
    raw = generate(seed, patients=120, cycles=9)
    candidates = []
    for row in raw:
        if row["phenotype"] != "PMOS_A" or row["cycle"] != 6 or not 30 <= row["ovulation_day"] <= 38:
            continue
        history = [r["cycle_length"] for r in raw if r["patient"] == row["patient"] and r["cycle"] < 6]
        if 38 <= float(np.median(history)) <= 45:
            candidates.append((row, history))
    if not candidates:
        raise ValueError("Declared Kushi ground-truth rule has no match; do not search by prediction")
    chosen, history = min(candidates, key=lambda pair: pair[0]["patient"])
    index = int(chosen["patient"].rsplit("p", 1)[1])
    cycles = []
    for logical_cycle, scenario_seed in zip((7, 8, 9), (seed, 2108, 2109)):
        rows = attach_prior_cycle_lengths(generate(scenario_seed, patients=index+1, cycles=9))
        row = next(r for r in rows if r["patient"].endswith(f"p{index:04d}") and r["cycle"] == logical_cycle-1)
        row = dict(row, age=KUSHI_PROFILE["age"], bmi=KUSHI_PROFILE["bmi"], family_history=KUSHI_PROFILE["family_history"])
        cycles.append({"logical_cycle": logical_cycle, "seed": scenario_seed, "record": row})
    return {"profile": dict(KUSHI_PROFILE), "selection_rule": SELECTION_RULE,
            "selected_patient_index": index, "six_past_lengths": history, "cycles": cycles,
            "scenario_disclosure": "Later seeds are independent synthetic scenario replays, not a validated longitudinal patient. "
                                   "The fictional usual range is narrative; generated history is displayed unchanged, including outliers."}
