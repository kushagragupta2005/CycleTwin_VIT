"""Train/validation/test synthetic evaluation with fitted, calibrated classifiers."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np

from src.features import TIER_NAMES, build_feature_matrix, feature_names
from src.fitted import PlattModel, choose_f1_threshold
from src.generator import generate
from src.model import estimate_ovulation_day
from src.splits import patient_partition

SEEDS, DAYS, TIERS = (97, 101, 103), (10, 14, 18), (0, 1, 2, 3)


def auc(y, s):
    y, s = np.asarray(y, dtype=int), np.asarray(s, dtype=float)
    n1, n0 = int(y.sum()), len(y) - int(y.sum())
    if not n1 or not n0: return None
    _, inv, counts = np.unique(s, return_inverse=True, return_counts=True)
    ranks = np.cumsum(counts) - counts / 2 + 0.5
    positives = np.bincount(inv, weights=y, minlength=len(counts))
    return float((np.sum(ranks * positives) - n1 * (n1 + 1) / 2) / (n1 * n0))


def auprc(y, s):
    y = np.asarray(y)[np.argsort(-np.asarray(s))]
    tp, fp = np.cumsum(y), np.cumsum(1 - y)
    return float(np.sum((tp / np.maximum(tp + fp, 1)) * y) / tp[-1]) if tp[-1] else None


def brier(y, s): return float(np.mean((np.asarray(y) - np.asarray(s)) ** 2))


def brier_gain_ci(y, candidate, baseline, patient_ids, seed, reps=500):
    """Patient-cluster CI for baseline Brier minus candidate Brier on validation."""
    y = np.asarray(y, dtype=float)
    gain = (y - np.asarray(baseline)) ** 2 - (y - np.asarray(candidate)) ** 2
    ids = np.asarray(patient_ids)
    unique = np.unique(ids)
    grouped = {patient: gain[ids == patient] for patient in unique}
    rng = np.random.default_rng(seed)
    draws = [float(np.mean(np.concatenate([grouped[p] for p in rng.choice(unique, len(unique), replace=True)])))
             for _ in range(reps)]
    return [float(np.quantile(draws, .025)), float(np.quantile(draws, .975))]


def threshold_metrics(records, threshold):
    y = np.asarray([r["y"] for r in records], dtype=int)
    flagged = np.asarray([r["score"] >= threshold for r in records])
    tp, fp = int(np.sum(flagged & (y == 1))), int(np.sum(flagged & (y == 0)))
    fn = int(np.sum(~flagged & (y == 1)))
    return {"sensitivity": float(tp / max(tp + fn, 1)), "ppv": float(tp / max(tp + fp, 1)),
            "false_alerts_per_100_cycles": float(100 * fp / len(records)), "alert_rate": float(np.mean(flagged)),
            "median_lead_days_vs_day_35": float(np.median([35 - r["day"] for r, flag in zip(records, flagged) if flag and r["y"] == 1])) if tp else None}


def per_archetype_false_alarm_rates(records, threshold):
    output = {}
    for archetype in sorted({r["phenotype"] for r in records}):
        rows = [r for r in records if r["phenotype"] == archetype and r["y"] == 0]
        output[archetype] = float(np.mean([r["score"] >= threshold for r in rows])) if rows else None
    return output


def alert_tradeoff_curve(records):
    """Exploratory held-out threshold sweep; never used to choose the deployed threshold."""
    points = []
    for threshold in np.linspace(0.05, 0.95, 11):
        metrics = threshold_metrics(records, float(threshold))
        points.append({"threshold": float(threshold), "false_alerts_per_100_cycles": metrics["false_alerts_per_100_cycles"],
                       "sensitivity": metrics["sensitivity"], "ppv": metrics["ppv"],
                       "median_lead_days_vs_day_35": metrics["median_lead_days_vs_day_35"]})
    return points


def cluster_ci(records, metric, reps=1000, seed=808):
    ids = np.unique([r["patient"] for r in records])
    by_patient = {identifier: [r for r in records if r["patient"] == identifier] for identifier in ids}
    rng, values = np.random.default_rng(seed), []
    for _ in range(reps):
        rows = [r for identifier in rng.choice(ids, size=len(ids), replace=True) for r in by_patient[identifier]]
        value = metric(rows)
        if value is not None and np.isfinite(value): values.append(value)
    return [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def y_values(rows): return np.asarray([row["event"] for row in rows], dtype=int)


results = {"scope": "synthetic internal held-out simulation only; not clinical performance", "plan": "docs/eval_plan.md",
           "model": "sklearn LogisticRegression fitted on train; tier fallback selected by validation Brier, Platt calibration and F1 threshold selection on validation only", "seeds": {}}
for seed in SEEDS:
    partitions = {"train": [], "validation": [], "test": []}
    for row in generate(seed): partitions[patient_partition(row["patient"])].append(row)
    seed_result = {"patients": {name: len({r["patient"] for r in rows}) for name, rows in partitions.items()}, "metrics": {}}
    for day in DAYS:
        for tier in TIERS:
            x_train = build_feature_matrix(partitions["train"], day, tier)
            x_val = build_feature_matrix(partitions["validation"], day, tier)
            x_test = build_feature_matrix(partitions["test"], day, tier)
            fitted = PlattModel().fit(x_train, y_values(partitions["train"]), x_val, y_values(partitions["validation"]))
            selected_tier = tier
            if tier > 0:
                baseline = PlattModel().fit(
                    build_feature_matrix(partitions["train"], day, 0), y_values(partitions["train"]),
                    build_feature_matrix(partitions["validation"], day, 0), y_values(partitions["validation"]))
                y_val = y_values(partitions["validation"])
                candidate_val_probability = fitted.predict_proba(x_val)
                baseline_x_val = build_feature_matrix(partitions["validation"], day, 0)
                baseline_val_probability = baseline.predict_proba(baseline_x_val)
                gain_ci = brier_gain_ci(y_val, candidate_val_probability, baseline_val_probability,
                                        [r["patient"] for r in partitions["validation"]], seed + day + tier)
                if gain_ci[0] <= 0:
                    fitted = baseline
                    x_val = baseline_x_val
                    x_test = build_feature_matrix(partitions["test"], day, 0)
                    selected_tier = 0
            threshold = choose_f1_threshold(y_values(partitions["validation"]), fitted.predict_proba(x_val))
            records = [{"patient": row["patient"], "cycle": row["cycle"], "day": day, "phenotype": row["phenotype"],
                        "y": row["event"], "score": float(score), "ov": row["ovulation_day"],
                        "ov_est": estimate_ovulation_day(row, day, tier)}
                       for row, score in zip(partitions["test"], fitted.predict_proba(x_test))]
            methods = {"auroc": lambda z: auc([r["y"] for r in z], [r["score"] for r in z]),
                       "auprc": lambda z: auprc([r["y"] for r in z], [r["score"] for r in z]),
                       "brier": lambda z: brier([r["y"] for r in z], [r["score"] for r in z])}
            ovulation = [r for r in records if r["ov"] > 0]
            output = {"n_cycles": len(records), "event_rate": float(np.mean([r["y"] for r in records])),
                      "tier_name": TIER_NAMES[tier], "features": feature_names(selected_tier),
                      "validation_selected_feature_tier": selected_tier, "validation_brier_gain_ci": gain_ci if tier else None,
                      "validation_selected_threshold": threshold,
                      "ovulation_day_mae": float(np.mean([abs(r["ov"] - r["ov_est"]) for r in ovulation])),
                      "ovulation_day_mae_cluster_bootstrap_95ci": cluster_ci(ovulation, lambda z: float(np.mean([abs(r["ov"] - r["ov_est"]) for r in z])), seed=seed + day + tier + 1),
                      **threshold_metrics(records, threshold)}
            output["per_archetype_false_alarm_rate"] = per_archetype_false_alarm_rates(records, threshold)
            output["alert_tradeoff_curve"] = alert_tradeoff_curve(records)
            for name, method in methods.items():
                output[name] = method(records)
                output[f"{name}_cluster_bootstrap_95ci"] = cluster_ci(records, method, seed=seed + day + tier)
            seed_result["metrics"][f"day_{day}_tier_{tier}"] = output
    results["seeds"][str(seed)] = seed_result

Path("results.json").write_text(json.dumps(results, indent=2) + "\n")
print("Wrote results.json: fitted on train, calibrated and threshold-selected on validation, evaluated once on held-out patients.")
