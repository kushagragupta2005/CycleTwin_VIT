"""Small stochastic cycle cohort generator. All records are synthetic."""
from __future__ import annotations
import numpy as np

PHENOTYPES = ("healthy_regular", "healthy_variable", "PMOS_A", "PMOS_B", "PMOS_C", "PMOS_D", "thyroid_mimic", "contraception", "early_menarche")

def generate(seed: int, patients: int = 1200, cycles: int = 6):
    rng = np.random.default_rng(seed)
    out = []
    for p in range(patients):
        phenotype = PHENOTYPES[p % len(PHENOTYPES)]
        ir = float(np.clip(rng.normal(0.0, 1.0), -2.5, 2.5))
        androgen = float(rng.normal(0.65 if phenotype.startswith("PMOS") else 0.0, .7))
        age = int(rng.integers(18, 43))
        bmi = float(np.clip(rng.normal(25.5 + 1.8 * max(ir, 0), 4.2), 17.0, 42.0))
        family_history = int(rng.random() < (0.18 + 0.12 * max(ir, 0)))
        base = 16 if phenotype in ("healthy_regular", "PMOS_C", "contraception", "early_menarche") else 22 if phenotype == "healthy_variable" else 26
        for c in range(cycles):
            stress = rng.normal(0, 1)
            late = phenotype in ("PMOS_A", "PMOS_B", "PMOS_D", "thyroid_mimic", "healthy_variable")
            ovday = int(np.clip(rng.normal(base + 6*max(ir, 0)*late + 3*stress*late, 4), 12, 45))
            anov = bool(late and rng.random() < (0.24 + .09*max(ir, 0)))
            if anov: ovday = -1
            length = int(rng.integers(24, 42)) if anov else int(np.clip(ovday + rng.normal(13, 1.8), 22, 55))
            # A minority of logged starts are shifted or represent withdrawal/spotting noise.
            log_shift = int(rng.choice([-2, 0, 0, 0, 1, 3]))
            true_start = np.datetime64("2025-01-01") + np.timedelta64(c*38 + p*400, "D")
            start = true_start + np.timedelta64(log_shift, "D")
            temp = rng.normal(0, .035, 55)
            if ovday > 0:
                temp[ovday:] += .20
            # Occasional noise and missing nights; features are available as noisy daily observations.
            temp += np.cumsum(rng.normal(0, .004, 55))
            missing = rng.random(55) < .12
            temp[missing] = np.nan
            rhr = rng.normal(0, 1, 55); hrv = rng.normal(0, 1, 55)
            if ovday > 0:
                rhr[ovday:] += .35; hrv[ovday:] -= .25
            steps = rng.lognormal(8.5, .25, 55)
            sleep = rng.normal(7, .75, 55)
            out.append(dict(patient=f"s{seed}-p{p:04d}", cycle=c, phenotype=phenotype,
                            day0=str(start), cycle_length=length, ovulation_day=ovday,
                            event=int(anov or ovday > 21), ir=ir, androgen=androgen,
                            age=age, bmi=bmi, family_history=family_history,
                            temperature=temp, rhr=rhr, hrv=hrv, steps=steps, sleep=sleep,
                            period_start=true_start, seed=seed))
    return out

