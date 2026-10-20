"""Read-only audit of production code/data; writes audit evidence beside this file."""
import ast
import csv
import hashlib
import importlib.metadata
import json
from collections import Counter
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import numpy as np
from sklearn.metrics import average_precision_score
from src.generator import generate, PHENOTYPES
from src.features import build_feature_matrix, feature_names
from src.fitted import PlattModel, choose_f1_threshold
from src.splits import patient_partition
from src.model import forecast, estimate_ovulation_day
from src.conformal import calibrate_binary, calibrate_ovulation_interval, classification_set, ovulation_interval
from src.safety import abstention_reasons
from src.alerts import apply_alert_budget
from src.twin import simulate_reproductive_axis, simulate_metabolic_axis, coupling_sweep
from src.metabolic import excursion_event
from src.adapters.apple_health import parse_export


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(name, value):
    (OUT / name).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + "\n")


def write_csv(name, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / name).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(clean(v)) if isinstance(v, (list, dict, tuple)) else clean(v)
                             for k, v in row.items()})


def describe(values):
    values = np.asarray(values, dtype=float).ravel()
    finite = values[np.isfinite(values)]
    return {"total": len(values), "missing": int(np.sum(~np.isfinite(values))),
            "observed": len(finite), "min": float(finite.min()) if len(finite) else None,
            "max": float(finite.max()) if len(finite) else None,
            "mean": float(finite.mean()) if len(finite) else None,
            "population_std": float(finite.std()) if len(finite) else None}


def cohort_counts(rows):
    return {"patients": len({r["patient"] for r in rows}), "cycles": len(rows),
            "PMOS_patients": len({r["patient"] for r in rows if r["phenotype"].startswith("PMOS")}),
            "PMOS_cycles": sum(r["phenotype"].startswith("PMOS") for r in rows),
            "positive": sum(r["event"] for r in rows),
            "negative": sum(1-r["event"] for r in rows),
            "absent": sum(r["ovulation_day"] < 0 for r in rows),
            "late_ovulation": sum(r["ovulation_day"] > 21 for r in rows),
            "observed_ovulation": sum(r["ovulation_day"] > 0 for r in rows),
            "temperature": describe(np.concatenate([r["temperature"] for r in rows])),
            "archetypes": {name: {"patients": len({r["patient"] for r in rows if r["phenotype"] == name}),
                                  "cycles": sum(r["phenotype"] == name for r in rows),
                                  "positive": sum(r["event"] for r in rows if r["phenotype"] == name)}
                          for name in PHENOTYPES}}


saved = json.loads((ROOT / "results.json").read_text())
module = ast.parse((ROOT / "scripts/run_eval.py").read_text())
namespace = {"np": np}
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n, ast.FunctionDef)],
                        type_ignores=[]), "scripts/run_eval.py:audit-functions-only", "exec"), namespace)
dataset_stats, feature_stats, metrics, subgroup_rows, curves, predictions, refits = {}, [], [], [], [], [], []
all_rows, checks = [], []
for seed_text, seed_result in saved["seeds"].items():
    seed = int(seed_text)
    rows = generate(seed)
    all_rows.extend(rows)
    parts = {name: [r for r in rows if patient_partition(r["patient"]) == name]
             for name in ("train", "validation", "test")}
    dataset_stats[seed_text] = {"all": cohort_counts(rows),
                                **{name: cohort_counts(v) for name, v in parts.items()}}
    for day in (10, 14, 18):
        matrices = {name: build_feature_matrix(v, day, 3) for name, v in parts.items()}
        for part, matrix in matrices.items():
            for i, feature in enumerate(feature_names(3)):
                feature_stats.append({"seed": seed, "day": day, "partition": part, "feature": feature,
                                      **describe(matrix[:, i])})
        y = {name: np.asarray([r["event"] for r in v]) for name, v in parts.items()}
        for tier in (0, 1, 2, 3):
            key = f"day_{day}_tier_{tier}"
            m = seed_result["metrics"][key]
            selected = m["validation_selected_feature_tier"]
            count = len(feature_names(selected))
            model = PlattModel().fit(matrices["train"][:, :count], y["train"],
                                     matrices["validation"][:, :count], y["validation"])
            probability = model.predict_proba(matrices["test"][:, :count])
            threshold = choose_f1_threshold(y["validation"], model.predict_proba(matrices["validation"][:, :count]))
            flag = probability >= threshold
            tp = int(np.sum(flag & (y["test"] == 1)))
            fp = int(np.sum(flag & (y["test"] == 0)))
            tn = int(np.sum(~flag & (y["test"] == 0)))
            fn = int(np.sum(~flag & (y["test"] == 1)))
            n, positives, negatives = len(flag), tp+fn, tn+fp
            ov_rows = [r for r in parts["test"] if r["ovulation_day"] > 0]
            mae = float(np.mean([abs(r["ovulation_day"]-estimate_ovulation_day(r, day, tier)) for r in ov_rows]))
            reproduced = {"auroc": namespace["auc"](y["test"], probability),
                          "auprc": namespace["auprc"](y["test"], probability),
                          "brier": namespace["brier"](y["test"], probability),
                          "ovulation_day_mae": mae, "validation_selected_threshold": threshold,
                          "sensitivity": tp/positives, "ppv": tp/(tp+fp),
                          "false_alerts_per_100_cycles": 100*fp/n, "alert_rate": (tp+fp)/n}
            for field, value in reproduced.items():
                assert np.isclose(value, m[field], rtol=0, atol=1e-12), (seed, key, field, value, m[field])
            checks.append({"seed": seed, "day": day, "tier": tier,
                           "matching_saved_fields": list(reproduced), "absolute_tolerance": 1e-12})
            flat = {"seed": seed, "day": day, "tier": tier,
                    **{k: v for k, v in m.items() if k not in ("per_archetype_false_alarm_rate", "alert_tradeoff_curve")}}
            for field in ("auroc", "auprc", "brier", "ovulation_day_mae"):
                lo, hi = flat.pop(field+"_cluster_bootstrap_95ci")
                flat[field+"_ci_low"], flat[field+"_ci_high"] = lo, hi
            flat.update({"positive_denominator": positives, "negative_denominator": negatives,
                         "ovulation_mae_denominator": len(ov_rows), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
                         "accuracy_audit_derived": (tp+tn)/n, "accuracy_fraction": f"{tp+tn}/{n}",
                         "precision_fraction": f"{tp}/{tp+fp}", "recall_fraction": f"{tp}/{positives}",
                         "specificity_audit_derived": tn/negatives, "specificity_fraction": f"{tn}/{negatives}",
                         "f1_audit_derived": 2*tp/(2*tp+fp+fn), "f1_fraction": f"{2*tp}/{2*tp+fp+fn}",
                         "constant_at_test_prevalence_brier": (positives/n)*(negatives/n),
                         "sklearn_average_precision_audit_comparison": float(average_precision_score(y["test"], probability))})
            metrics.append(flat)
            for name, saved_rate in m["per_archetype_false_alarm_rate"].items():
                ix = np.asarray([r["phenotype"] == name for r in parts["test"]])
                neg = ix & (y["test"] == 0)
                denominator = int(neg.sum()); numerator = int(np.sum(flag & neg))
                value = numerator/denominator if denominator else None
                assert value == saved_rate, (seed, key, name, value, saved_rate)
                subgroup_rows.append({"seed": seed, "day": day, "tier": tier, "archetype": name,
                                      "patients": len({r["patient"] for r in parts["test"] if r["phenotype"] == name}),
                                      "cycles": int(ix.sum()), "negative_cycles": denominator,
                                      "false_positive_cycles": numerator, "false_alarm_rate_saved": saved_rate,
                                      "exact_fraction": f"{numerator}/{denominator}" if denominator else "undefined"})
            for point in m["alert_tradeoff_curve"]:
                f = probability >= point["threshold"]
                ctp = int(np.sum(f & (y["test"] == 1))); cfp = int(np.sum(f & (y["test"] == 0)))
                curves.append({"seed": seed, "day": day, "tier": tier, **point,
                               "tp": ctp, "fp": cfp, "positive_denominator": positives,
                               "negative_denominator": negatives, "cycles": n,
                               "ppv_denominator": ctp+cfp})
            for row, prob, flagged in zip(parts["test"], probability, flag):
                predictions.append({"seed": seed, "day": day, "tier": tier, "patient": row["patient"],
                                    "cycle": row["cycle"], "archetype": row["phenotype"], "event": row["event"],
                                    "ovulation_day_truth": row["ovulation_day"], "probability_audit_refit": float(prob),
                                    "threshold": threshold, "flagged": bool(flagged)})
            refits.append({"seed": seed, "day": day, "tier": tier, "selected_feature_tier": selected,
                           "features": feature_names(selected), "trainable_coefficient_count": count+3,
                           "base_coefficients": model.base.named_steps["lr"].coef_,
                           "base_intercept": model.base.named_steps["lr"].intercept_,
                           "platt_coefficient": model.calibrator.coef_, "platt_intercept": model.calibrator.intercept_,
                           "imputer_training_medians": model.base.named_steps["impute"].statistics_,
                           "scaler_training_means": model.base.named_steps["scale"].mean_,
                           "scaler_training_scales": model.base.named_steps["scale"].scale_})
    print("Verified seed", seed, flush=True)

dataset_stats["combined_benchmark"] = cohort_counts(all_rows)
raw_stats = {field: describe(np.concatenate([r[field] for r in all_rows]))
             for field in ("temperature", "rhr", "hrv", "steps", "sleep")}
raw_stats.update({field: describe([r[field] for r in all_rows])
                  for field in ("cycle_length", "ovulation_day", "ir", "androgen", "age", "bmi", "family_history")})
with (ROOT / "data/ehr.csv").open() as handle:
    ehr = list(csv.DictReader(handle))
expected = {(str(r["seed"]), r["patient"]): r for r in all_rows}
for r in ehr:
    original = expected[(r["seed"], r["patient"])]
    for csv_key, gen_key in (("simulator_ir_latent","ir"),("simulator_androgen_load","androgen"),
                             ("synthetic_age","age"),("synthetic_bmi","bmi"),("synthetic_family_history","family_history")):
        assert float(r[csv_key]) == original[gen_key]
    assert r["synthetic_archetype"] == original["phenotype"]
dataset_stats["ehr_csv"] = {"rows": len(ehr), "unique_patients": len({r["patient"] for r in ehr}),
                             "missing_cells": sum(v == "" for r in ehr for v in r.values()),
                             "matches_generator": True}

display_generated = generate(223, patients=36, cycles=2)
history, display = {}, []
for row in display_generated:
    prior = history.setdefault(row["patient"], [])
    if row["cycle"] > 0:
        row["prior_cycle_lengths"] = prior[-3:]; display.append(row)
    prior.append(row["cycle_length"])
cal = generate(211, patients=240, cycles=1)
q_cls = calibrate_binary([r["event"] for r in cal], [forecast(r,14,2) for r in cal])
cal_ov = [r for r in cal if r["ovulation_day"] > 0]
q_ov = calibrate_ovulation_interval([r["ovulation_day"] for r in cal_ov],
                                   [estimate_ovulation_day(r,14,2) for r in cal_ov])
dataset_stats["display_generated"] = cohort_counts(display_generated)
dataset_stats["display_visible"] = cohort_counts(display)
dataset_stats["calibration"] = cohort_counts(cal)
examples, demo_rows = [], []
for r in display:
    wear = float(np.isfinite(r["temperature"][:14]).mean())
    age = 17 if r["phenotype"] == "early_menarche" else 29
    flags = {"age": age, "early_post_menarche": r["phenotype"] == "early_menarche",
             "tsh_abnormal": r["phenotype"] == "thyroid_mimic", "hormonal_contraception": r["phenotype"] == "contraception",
             "wear_completeness": wear}
    reasons = abstention_reasons(flags)
    ix = int(r["patient"].split("p")[-1])
    for tier in (0,1,2):
        score = forecast(r,14,tier)
        row = {"patient": r["patient"], "cycle": r["cycle"], "tier": tier, "archetype": r["phenotype"],
               "actual_generated_age": r["age"], "dashboard_safety_age": age, "wear": wear,
               "prior_cycle_lengths": r["prior_cycle_lengths"], "score_heuristic": score,
               "abstain": bool(reasons), "reasons": reasons, "ovulation_estimate_shown": estimate_ovulation_day(r,14,2),
               "ovulation_estimate_if_selected_tier_used": estimate_ovulation_day(r,14,tier),
               "conformal_labels": classification_set(score,q_cls),
               "interval_shown": ovulation_interval(estimate_ovulation_day(r,14,2),q_ov),
               "generator_truth_event": r["event"], "generator_truth_ovulation_day": r["ovulation_day"]}
        demo_rows.append(row)
        if r["patient"].endswith(("p0000","p0002","p0026")):
            row = dict(row)
            row.update({"rhr_days_1_14_mean": float(np.mean(r["rhr"][:14])),
                        "hrv_days_1_14_mean": float(np.mean(r["hrv"][:14])),
                        "steps_days_1_14_mean": float(np.mean(r["steps"][:14])),
                        "sleep_days_1_14_mean": float(np.mean(r["sleep"][:14])),
                        "temperature_days_1_14": clean(r["temperature"][:14])})
            twin = simulate_reproductive_axis(r["ir"],r["androgen"],seed=4000+ix)
            row.update({"twin_ovulation_day": twin["ovulation_day"], "twin_follicle_days_1_35":twin["follicle"][:35],
                        "coupling_sweep":coupling_sweep(r["ir"],r["androgen"])})
            if ix % 4 == 0:
                metabolic = simulate_metabolic_axis(r["ir"],twin["ovulation_day"],seed=3000+ix)
                events = [excursion_event(metabolic["glucose_mg_dl"],m) for m in metabolic["meal_indices"]]
                row["cgm"] = {"full_samples": len(metabolic["glucose_mg_dl"]), "display_samples":len(metabolic["glucose_mg_dl"][::8]),
                              "step_minutes": metabolic["step_minutes"], "meal_windows":len(events),
                              "excursion_windows":sum(events), "excursion_fraction":sum(events)/len(events),
                              "glucose_range":describe(metabolic["glucose_mg_dl"])}
            row["what_if_score_ranges"] = {name:[score*a,score*b] for name,(a,b) in {
                "Regular sleep":(.8,.98),"Daily walk":(.75,.98),"Lower-GI food swap":(.8,1),
                "Lower evening stress":(.8,1),"Illustrative weight change":(.75,.98)}.items()}
            examples.append(row)
demo_stats = {"q_classification":q_cls,"q_ovulation_days":q_ov,"calibration_cycles":len(cal),
              "calibration_observed_ovulation_cycles":len(cal_ov),
              "abstained":sum(r["abstain"] for r in demo_rows if r["tier"]==2),
              "reason_counts":dict(Counter(reason for r in demo_rows if r["tier"]==2 for reason in r["reasons"]))}
for tier in (0,1,2):
    rs = [r for r in demo_rows if r["tier"]==tier]
    available = sorted([r for r in rs if not r["abstain"]],key=lambda r:max(r["score_heuristic"],1-r["score_heuristic"]),reverse=True)
    cover, error, counts = [], [], []
    for fraction in np.linspace(.1,1,10):
        count=max(1,int(len(available)*fraction));chosen=available[:count]
        counts.append(count);cover.append(count/len(rs))
        error.append(float(np.mean([(r["score_heuristic"]>=.5)!=bool(r["generator_truth_event"]) for r in chosen])))
    preds=[{"patient":r["patient"],"cycle":r["cycle"],"day":day,"risk":forecast(r,day,tier),
            "abstain":next(x["abstain"] for x in rs if x["patient"]==r["patient"])}
           for r in display for day in (10,14,18)]
    budget=apply_alert_budget(preds)
    demo_stats[str(tier)]={"risk_coverage_counts":counts,"risk_coverage":cover,"selective_error":error,
                          "above_cutoff_before_abstention":sum(r["score_heuristic"]>=.5 for r in rs),
                          "day14_eligible_above_cutoff":sum(r["score_heuristic"]>=.5 and not r["abstain"] for r in rs),
                          "budgeted_alerts":sum(r["alert"] for r in budget),
                          "score_range":describe([r["score_heuristic"] for r in rs])}

xml_path = ROOT / "apple_health_export/export.xml"
if xml_path.exists():
    tree = ET.parse(xml_path)
    records = tree.findall("Record")
    parsed = parse_export(xml_path)
    dataset_stats["apple_fixture"]={"records":len(records),"record_types":dict(Counter(r.attrib["type"] for r in records)),
        "parsed_dates":len(parsed["daily"]),"cycle_starts":parsed["cycle_starts"],
        "missing_quantity_values":sum(not np.isfinite(float(r.attrib.get("value",0))) for r in records if r.attrib["type"].startswith("HKQuantity")),
        "parsed_daily":parsed}

history_results = []
for ref in ("e43ea93","3d0c852","dd37506","f282e75","d6314fb"):
    value=json.loads(subprocess.check_output(["git","show",ref+":results.json"],cwd=ROOT))
    write_json("historical_"+ref+"_results.json",value)
    history_results.append({"commit":ref,"seeds":list(value.get("seeds",{})),
                            "seed97_day14_tier2":value.get("seeds",{}).get("97",{}).get("metrics",{}).get("day_14_tier_2")})
slide_text = {}
for path in (ROOT/"deliverables").glob("*.pptx"):
    with zipfile.ZipFile(path) as z:
        slides={}
        for name in z.namelist():
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                tree=ET.fromstring(z.read(name))
                slides[name]=" | ".join(el.text or "" for el in tree.iter() if el.tag.endswith("}t"))
        slide_text[path.name]=slides
environment={"python":platform.python_version(),"platform":platform.platform(),
             "packages":{p:importlib.metadata.version(p) for p in ("numpy","scikit-learn","pandas","streamlit","altair","scipy","joblib","threadpoolctl")},
             "audited_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
             "source_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [ROOT/"app.py",ROOT/"results.json",ROOT/"data/ehr.csv",*sorted((ROOT/"src").rglob("*.py"))]},
             "saved_model_files":[str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".venv" not in p.parts and ".git" not in p.parts and p.suffix in (".pkl",".joblib",".onnx",".pt",".h5")],
             "latency_benchmark":"not present; not measured by this audit",
             "memory_benchmark":"not present; not measured by this audit"}
write_json("dataset_statistics.json",dataset_stats)
write_json("raw_input_ranges.json",raw_stats)
write_json("dashboard_statistics.json",demo_stats)
write_json("illustrative_examples.json",examples)
write_json("audit_refitted_parameters.json",refits)
write_json("reproduction_checks.json",checks)
write_json("environment_and_provenance.json",environment)
write_json("evaluation_history.json",history_results)
write_json("presentation_text.json",slide_text)
write_csv("all_metrics.csv",metrics)
write_csv("subgroup_false_alarm_rates.csv",subgroup_rows)
write_csv("threshold_tradeoff_points.csv",curves)
write_csv("feature_ranges_and_missingness.csv",feature_stats)
write_csv("audit_refitted_heldout_predictions.csv",predictions)
write_csv("dashboard_records.csv",demo_rows)
print("AUDIT COMPLETE",{"metrics":len(metrics),"subgroups":len(subgroup_rows),"tradeoff_points":len(curves),
                       "predictions":len(predictions),"verified_fields":sum(len(c["matching_saved_fields"]) for c in checks)})
