"""Build the machine-readable source of publishable claims from actual artifacts."""
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.personas import make_kushi
from src.generator import generate
from src.splits import patient_partition
from scripts.deliverable_content import compose


def judge_readme(claims, body):
    """Add the submission-facing README opening from already-built claims."""
    tier2 = next(row for row in claims["frozen_summary"] if row["Forecast day"] == 18 and row["Tier"] == 2)
    drift = claims["robustness"]["conditions"]["device_drift_c_per_day=0.01"]
    coverage = claims["conformal_summary"]["day_band_coverage_mean"]
    seeds = len(claims["frozen"]["seeds"])
    headline = f'''# CycleTwin_VIT

**CycleTwin forecasts a generated late or absent ovulation-cycle event from synthetic calendar and wearable-style signals for research; it does not diagnose PMOS.**

> **Synthetic data only. Not for diagnosis, contraception or conception planning.**

[Live demo — replace LIVE_DEMO_URL](LIVE_DEMO_URL) · [Video — replace VIDEO_URL](VIDEO_URL) · [Pitch PDF](deliverables/CycleTwin_pitch_deck.pdf) · [Pitch PPTX](deliverables/CycleTwin_pitch_deck.pptx) · [Architecture PDF](deliverables/CycleTwin_architecture.pdf) · [Architecture PPTX](deliverables/CycleTwin_architecture.pptx) · [Checklist](SUBMISSION_CHECKLIST.md) · [Audit](docs/audit_2026-10-20/CycleTwin_full_audit.md)

## Frozen synthetic snapshot

- Day-18 Tier-2 AUROC: **{tier2['Mean AUROC']:.6f}**.
- Day-18 Tier-2 Brier score: **{tier2['Mean Brier']:.6f}**.
- Held-out generated cycles: **{tier2['Held-out cycles']:,}** across **{seeds}** frozen seeds.

![Historical synthetic cohort capture](docs/screenshots/patient-list.png)

## Where it breaks

- On days 10 and 14, the retained path is mostly calendar history; temperature-derived signals show a clear frozen gain at day 18.
- The heuristic ovulation-day band covered **{coverage:.6f}** of its applicable frozen synthetic cases and failed its coverage check.
- With simulated +0.01°C/day temperature drift, ranking remains **{drift['mean_auroc']:.6f}** but Brier rises to **{drift['mean_brier']:.6f}**, above the frozen base-rate reference.

**Team:** solo participant Kushagra Gupta, full-time student · **College:** Vellore Institute of Technology (VIT) · **Licence:** [MIT](LICENSE) · **AI disclosure:** AI coding assistants helped build the project; no LLM is used in prediction or explanation paths.

---

'''
    body = body.replace("# CycleTwin_VIT\n\n", "", 1)
    body = body.replace("**College: VIT**", "**College: Vellore Institute of Technology (VIT)**")
    body = body.replace("Team leader: Kushagra Gupta.", "Solo participant: Kushagra Gupta, full-time student.")
    body = re.sub(r"\bfirst safe threshold\b", "earliest safe threshold", body, flags=re.IGNORECASE)
    body = re.sub(r"\bfirst prediction\b", "initial prediction", body, flags=re.IGNORECASE)
    body = re.sub(r"\bfirst\b", "initial", body, flags=re.IGNORECASE)
    return headline + body


def sanitize_judge_text(text):
    text = re.sub(r"\bfirst safe threshold\b", "earliest safe threshold", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfirst prediction\b", "initial prediction", text, flags=re.IGNORECASE)
    return re.sub(r"\b(first|novel|groundbreaking|state-of-the-art)\b", "initial", text, flags=re.IGNORECASE)


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
    claims['frozen_summary']=[]
    if claims['frozen'] is not None:
        for key in keys:
            values=[s['metrics'][key] for s in claims['frozen']['seeds'].values()]
            claims['frozen_summary'].append({'Forecast day':int(key.split('_')[1]),'Tier':int(key.rsplit('_',1)[1]),
                'Inputs':values[0]['tier_name'],'Mean AUROC':float(np.mean([v['auroc'] for v in values])),
                'Mean Brier':float(np.mean([v['brier'] for v in values])),
                'Mean day MAE':float(np.mean([v['ovulation_day_mae'] for v in values])),
                'Held-out cycles':sum(v['n_cycles'] for v in values),
                'Seeds retaining candidate':sum(v['validation_selected_feature_tier']==int(key.rsplit('_',1)[1]) for v in values),
                'scope':'frozen-v1 synthetic; not clinical performance'})
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
    frozen_card=ROOT/'models/frozen/model_card.json'
    if frozen_card.exists():
        claims['models'].update(json.loads(frozen_card.read_text())['models'])
        claims['source_sha256']['models/frozen/model_card.json']=hashlib.sha256(frozen_card.read_bytes()).hexdigest()
        claims['source_sha256']['results_final_frozen.json']=hashlib.sha256(frozen.read_bytes()).hexdigest()
    reporting=ROOT/'results_reporting.json'
    claims['reporting']=json.loads(reporting.read_text()) if reporting.exists() else None
    if reporting.exists():
        claims['source_sha256']['results_reporting.json']=hashlib.sha256(reporting.read_bytes()).hexdigest()
        for meta in claims['models'].values():
            dataset='frozen' if str(meta['seed']) in claims['reporting']['frozen'] else 'development'
            key=f"day_{meta['day']}_tier_{meta['requested_tier']}"
            point=claims['reporting'][dataset][str(meta['seed'])][key]['all']
            meta['metrics']['auprc']=point['average_precision']
            meta['metrics']['auprc_cluster_bootstrap_95ci']=point['intervals']['average_precision']['95ci']
            meta['metrics']['auprc_definition']='Standard sklearn average precision; raw legacy value retained separately'
            meta['metrics']['ece']=point['ece']
            meta['metrics']['calibration_diagnostic']=point['calibration_diagnostic']
    alert_policy=ROOT/'results_alert_policy_frozen.json'
    claims['alert_policy']=json.loads(alert_policy.read_text()) if alert_policy.exists() else None
    if alert_policy.exists():
        claims['source_sha256']['results_alert_policy_frozen.json']=hashlib.sha256(alert_policy.read_bytes()).hexdigest()
        claims['alert_policy_summary']={}
        for tier,seed_rows in claims['alert_policy']['tiers'].items():
            values=list(seed_rows.values()); leads=[x for row in values for x in row['lead_time_days_values']]
            alerts=sum(row['alerts'] for row in values); events=sum(row['event_cycles'] for row in values)
            claims['alert_policy_summary'][tier]={
                'n_cycles':sum(row['n_cycles'] for row in values),'alerts':alerts,
                'true_positive_alerts':sum(row['true_positive_alerts'] for row in values),
                'false_alerts':sum(row['false_alerts'] for row in values),'event_cycles':events,
                'missed_events':sum(row['missed_events'] for row in values),
                'alert_precision':sum(row['true_positive_alerts'] for row in values)/alerts if alerts else None,
                'missed_event_rate':sum(row['missed_events'] for row in values)/events if events else None,
                'false_alerts_per_synthetic_patient_year':sum(row['false_alerts'] for row in values)/sum(row['synthetic_exposure_patient_years'] for row in values),
                'lead_time_days_median':float(np.median(leads)) if leads else None,
                'lead_time_n':len(leads)}
    robustness=ROOT/'results_robustness_frozen.json'
    claims['robustness']=json.loads(robustness.read_text()) if robustness.exists() else None
    if robustness.exists():
        claims['source_sha256']['results_robustness_frozen.json']=hashlib.sha256(robustness.read_bytes()).hexdigest()
    bayesian=ROOT/'results_bayesian_twin_frozen.json'
    claims['bayesian_twin']=json.loads(bayesian.read_text()) if bayesian.exists() else None
    if bayesian.exists():
        claims['source_sha256']['results_bayesian_twin_frozen.json']=hashlib.sha256(bayesian.read_bytes()).hexdigest()
    lab_proxy=ROOT/'results_lab_proxy_extension.json'
    claims['lab_proxy']=json.loads(lab_proxy.read_text()) if lab_proxy.exists() else None
    if lab_proxy.exists():
        claims['source_sha256']['results_lab_proxy_extension.json']=hashlib.sha256(lab_proxy.read_bytes()).hexdigest()
    ops=ROOT/'results_ops.json'
    claims['operations']=json.loads(ops.read_text()) if ops.exists() else None
    if ops.exists():
        claims['source_sha256']['results_ops.json']=hashlib.sha256(ops.read_bytes()).hexdigest()
    conformal=ROOT/'results_conformal_frozen.json'
    claims['conformal']=json.loads(conformal.read_text()) if conformal.exists() else None
    if conformal.exists():
        claims['source_sha256']['results_conformal_frozen.json']=hashlib.sha256(conformal.read_bytes()).hexdigest()
        selected=[v['overall'] for k,v in claims['conformal']['results'].items() if k.endswith('day_18_tier_2')]
        claims['conformal_summary']={'classification_coverage_mean':float(np.mean([x['classification_coverage'] for x in selected])),
                                    'day_band_coverage_mean':float(np.mean([x['ovulation_day_band_coverage'] for x in selected])),
                                    'mean_classification_set_size':float(np.mean([x['mean_classification_set_size'] for x in selected])),
                                    'day_band_mean_width':float(np.mean([x['day_band_mean_width'] for x in selected]))}
    submission=ROOT/'docs/submission_status.json'
    claims['submission']=json.loads(submission.read_text()) if submission.exists() else None
    claims['deliverables']=compose(claims)
    claims['deliverables']['readme']=judge_readme(claims, claims['deliverables']['readme'])
    claims['deliverables']['video_scripts']={k:sanitize_judge_text(v) for k,v in claims['deliverables']['video_scripts'].items()}
    claims['deliverables']['runbook']=sanitize_judge_text(claims['deliverables']['runbook'])
    if write:
        (ROOT / "docs/claims.json").write_text(json.dumps(claims, indent=2) + "\n")
    return claims


if __name__ == "__main__":
    x = build(write='--check' not in sys.argv)
    if '--check' in sys.argv:
        if x != json.loads((ROOT/'docs/claims.json').read_text()):
            raise SystemExit('Claims are stale: run python scripts/build_claims.py')
    print(f"Built synthetic claims from {len(x['development']['seeds'])} development seeds; frozen results present: {x['frozen'] is not None}")
