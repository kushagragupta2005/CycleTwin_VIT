"""Build the README results table from results.json without editing numbers by hand."""
import json
from pathlib import Path

results=json.loads(Path("docs/claims.json").read_text())["development"]
lines=["| Seed | Forecast day | Tier | AUROC (95% patient-cluster CI) | AUPRC (95% patient-cluster CI) | Ovulation-day MAE (95% CI) | Brier | Validation threshold | Sensitivity | PPV | False alerts/100 cycles |",
       "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for seed,sr in results["seeds"].items():
    for key,m in sr["metrics"].items():
        day=int(key.split("_")[1]); tier=int(key.split("_")[3])
        fmt=lambda x:"n/a" if x is None else f"{x:.3f}"
        ci=lambda name:"n/a" if m[name] is None else f"{m[name]:.3f} ({m[name+'_cluster_bootstrap_95ci'][0]:.3f}–{m[name+'_cluster_bootstrap_95ci'][1]:.3f})"
        ovci=m["ovulation_day_mae_cluster_bootstrap_95ci"]
        ov="n/a" if m["ovulation_day_mae"] is None else f"{m['ovulation_day_mae']:.2f} ({ovci[0]:.2f}–{ovci[1]:.2f})"
        lines.append(f"| {seed} | {day} | {tier} | {ci('auroc')} | {ci('auprc')} | {ov} | {fmt(m['brier'])} | {fmt(m['validation_selected_threshold'])} | {fmt(m['sensitivity'])} | {fmt(m['ppv'])} | {fmt(m['false_alerts_per_100_cycles'])} |")
table="\n".join(lines)+"\n\nSynthetic development results. These seeds were reused during development and do not represent an untouched final evaluation."
readme=Path("README.md").read_text(); start=readme.index("<!-- RESULTS:START -->")+len("<!-- RESULTS:START -->"); end=readme.index("<!-- RESULTS:END -->")
Path("README.md").write_text(readme[:start]+"\n\n"+table+"\n"+readme[end:])
