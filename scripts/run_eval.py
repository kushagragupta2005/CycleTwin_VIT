"""Prespecified synthetic held-out evaluation with patient-cluster bootstrap CIs."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from src.generator import generate
from src.model import forecast, estimate_ovulation_day
from src.splits import patient_partition

SEEDS, DAYS, TIERS = (97, 101, 103), (10, 14, 18), (0, 1, 2)
def auc(y, s):
    y=np.asarray(y,dtype=int); s=np.asarray(s,dtype=float)
    n1=int(y.sum()); n0=len(y)-n1
    if not n1 or not n0: return None
    _, inv, counts=np.unique(s,return_inverse=True,return_counts=True)
    end=np.cumsum(counts); avg_rank=end-counts/2+0.5
    positive_by_tie=np.bincount(inv,weights=y,minlength=len(counts))
    return float((np.sum(avg_rank*positive_by_tie)-n1*(n1+1)/2)/(n1*n0))
def auprc(y, s):
    order=np.argsort(-np.asarray(s)); y=np.asarray(y)[order]; tp=np.cumsum(y); fp=np.cumsum(1-y)
    if tp[-1] == 0: return None
    precision=tp/np.maximum(tp+fp,1)
    return float(np.sum(precision*y)/tp[-1])
def brier(y,s): return float(np.mean((np.asarray(y)-np.asarray(s))**2))
def sensitivity_budget(y,s,ids):
    y=np.asarray(y); s=np.asarray(s); ids=np.asarray(ids); flags=np.zeros(len(y),bool)
    for pid in np.unique(ids):
        ix=np.where(ids==pid)[0]
        # One alert for each patient-cycle, modeled as one day-specific decision.
        flags[ix[s[ix] >= .5]]=True
    return float(np.sum(flags & (y==1))/max(np.sum(y==1),1)), float(np.sum(flags & (y==0))/max(len(y),1)*100)
def cluster_ci(records, metric, reps=1000, seed=808):
    ids=np.unique([r["patient"] for r in records]); rng=np.random.default_rng(seed); vals=[]
    by={i:[r for r in records if r["patient"]==i] for i in ids}
    for _ in range(reps):
        sample=rng.choice(ids, size=len(ids), replace=True); rows=[r for i in sample for r in by[i]]
        try:
            v=metric(rows)
            if v is not None and np.isfinite(v): vals.append(v)
        except (ValueError, ZeroDivisionError): pass
    return [float(np.quantile(vals,.025)), float(np.quantile(vals,.975))] if vals else [None,None]

results={"scope":"synthetic internal held-out simulation only; not clinical performance", "plan":"docs/eval_plan.md", "seeds":{}}
for seed in SEEDS:
    cycles=generate(seed)
    # Stable patient hash split, with all cycles from a patient held together.
    train=[]; val=[]; test=[]
    for row in cycles:
        partition=patient_partition(row["patient"])
        (test if partition=="test" else val if partition=="validation" else train).append(row)
    seed_result={"patients":{"train":len({x['patient'] for x in train}),"validation":len({x['patient'] for x in val}),"test":len({x['patient'] for x in test})},"metrics":{}}
    for day in DAYS:
        for tier in TIERS:
            rec=[]
            for row in test:
                rec.append({"patient":row["patient"],"y":row["event"],"score":forecast(row,day,tier),"ov":row["ovulation_day"],"ov_est":estimate_ovulation_day(row,day,tier)})
            y=[x["y"] for x in rec]; s=[x["score"] for x in rec]
            sens, fa=sensitivity_budget(y,s,[x["patient"] for x in rec])
            methods={"auroc":lambda z:auc([x['y'] for x in z],[x['score'] for x in z]),
                     "auprc":lambda z:auprc([x['y'] for x in z],[x['score'] for x in z]),
                     "brier":lambda z:brier([x['y'] for x in z],[x['score'] for x in z])}
            alerted=[x for x in rec if x["score"]>=.5 and x["y"]==1]
            lead=float(np.median([35-day for _ in alerted])) if alerted else None
            ovrows=[x for x in rec if x["ov"]>0]
            ovmae=float(np.mean([abs(x["ov"]-x["ov_est"]) for x in ovrows])) if ovrows else None
            out={"n_cycles":len(rec),"event_rate":float(np.mean(y)),"sensitivity_alert_cutoff_0_50":sens,"false_alerts_per_100_cycles":fa,"median_lead_days_vs_day_35":lead,"ovulation_day_mae":ovmae}
            out["ovulation_day_mae_cluster_bootstrap_95ci"]=cluster_ci(ovrows,lambda z:float(np.mean([abs(x["ov"]-x["ov_est"]) for x in z])) if z else None,seed=seed+day+tier+1)
            for name,fn in methods.items():
                out[name]=fn(rec); out[name+"_cluster_bootstrap_95ci"]=cluster_ci(rec,fn,seed=seed+day+tier)
            key=f"day_{day}_tier_{tier}"
            seed_result["metrics"][key]=out
    results["seeds"][str(seed)]=seed_result
Path("results.json").write_text(json.dumps(results,indent=2)+"\n")
lines=["| Forecast day | Tier | AUROC (95% patient-cluster CI) | AUPRC (95% patient-cluster CI) | Ovulation-day MAE | Brier | False alerts/100 cycles |",
       "|---|---:|---:|---:|---:|---:|---:|"]
for seed, sr in results["seeds"].items():
    if seed != str(SEEDS[0]): continue
    for day in DAYS:
        for tier in TIERS:
            m=sr["metrics"][f"day_{day}_tier_{tier}"]
            fmt=lambda x: "n/a" if x is None else f"{x:.3f}"
            ci=lambda name: "n/a" if m[name] is None else f"{m[name]:.3f} ({m[name+'_cluster_bootstrap_95ci'][0]:.3f}–{m[name+'_cluster_bootstrap_95ci'][1]:.3f})"
            ovci=m['ovulation_day_mae_cluster_bootstrap_95ci']
            ovtxt="n/a" if m['ovulation_day_mae'] is None else f"{m['ovulation_day_mae']:.2f} ({ovci[0]:.2f}–{ovci[1]:.2f})"
            lines.append(f"| {day} | {tier} | {ci('auroc')} | {ci('auprc')} | {ovtxt} | {fmt(m['brier'])} | {fmt(m['false_alerts_per_100_cycles'])} |")
table="\n".join(lines)+f"\n\nValues shown for seed {SEEDS[0]}; all three seeds and patient-cluster intervals are in `results.json`. Lead time and sensitivity at the alert cutoff are also in `results.json`."
readme=Path("README.md").read_text()
start=readme.index("<!-- RESULTS:START -->")+len("<!-- RESULTS:START -->")
end=readme.index("<!-- RESULTS:END -->")
Path("README.md").write_text(readme[:start]+"\n\n"+table+"\n"+readme[end:])
print("Wrote results.json (synthetic held-out patients; 1,000 patient-cluster resamples/metric).")
