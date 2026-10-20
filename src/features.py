"""Leakage-safe engineered features for the synthetic forecasting benchmark."""
from __future__ import annotations

import numpy as np


TIER_NAMES = {0: "calendar", 1: "calendar + wearables", 2: "calendar + wearables + temperature",
              3: "calendar + wearables + temperature + EHR-lite (oracle-adjacent)"}


def attach_prior_cycle_lengths(rows):
    """Copy records with completed history shared by classifier/day-estimator inference."""
    histories, result = {}, []
    for row in sorted(rows, key=lambda r: (r["patient"], r["cycle"])):
        history = histories.setdefault(row["patient"], [])
        result.append(dict(row, prior_cycle_lengths=list(history[-3:])))
        history.append(float(row["cycle_length"]))
    return result


def _prior_cycle_lengths(rows):
    """Return each cycle's mean logged length from preceding cycles only."""
    history = {}
    values = {}
    for row in sorted(rows, key=lambda x: (x["patient"], x["cycle"])):
        prior = history.get(row["patient"], [])
        values[(row["patient"], row["cycle"])] = float(np.mean(prior[-3:])) if prior else np.nan
        history.setdefault(row["patient"], []).append(float(row["cycle_length"]))
    return values


def feature_names(tier: int) -> list[str]:
    names = ["prior_logged_cycle_length"]
    if tier >= 1:
        names += ["mean_rhr_offset", "mean_hrv_offset", "mean_steps", "mean_sleep_hours"]
    if tier >= 2:
        names += ["temperature_change", "temperature_observation_fraction"]
    if tier >= 3:
        names += ["simulator_ir_latent", "simulator_androgen_load", "synthetic_age", "synthetic_bmi", "synthetic_family_history"]
    return names


def build_feature_matrix(rows, day: int, tier: int) -> np.ndarray:
    """Create only information available by `day`; calendar uses previous cycles."""
    prior = _prior_cycle_lengths(rows)
    records = []
    for row in rows:
        values = [prior[(row["patient"], row["cycle"])]]
        if tier >= 1:
            values += [float(np.nanmean(row["rhr"][:day])), float(np.nanmean(row["hrv"][:day])),
                       float(np.nanmean(row["steps"][:day])), float(np.nanmean(row["sleep"][:day]))]
        if tier >= 2:
            temps = row["temperature"][:day]
            observed = temps[np.isfinite(temps)]
            values += [float(np.mean(observed[-4:]) - np.mean(observed[:min(5, len(observed))])) if len(observed) >= 6 else np.nan,
                       float(np.isfinite(temps).mean())]
        if tier >= 3:
            values += [float(row["ir"]), float(row["androgen"]), float(row["age"]),
                       float(row["bmi"]), float(row["family_history"])]
        records.append(values)
    return np.asarray(records, dtype=float)


def record_features(record, day: int, tier: int) -> np.ndarray:
    """Inference uses only explicitly supplied completed-cycle history, never the target."""
    row = dict(record)
    row.setdefault("patient", "inference")
    row.setdefault("cycle", 0)
    row["cycle_length"] = 0.0  # Never require or consume the unknown current-cycle length.
    history = np.asarray(row.get("prior_cycle_lengths", []), dtype=float)
    # Reuse the benchmark's sensor transformations exactly; replace its batch history.
    matrix = build_feature_matrix([row], day, tier)
    matrix[0, 0] = float(np.mean(history[-3:])) if history.size else np.nan
    return matrix
