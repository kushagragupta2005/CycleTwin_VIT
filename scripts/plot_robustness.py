"""Plot frozen synthetic robustness sweep from its generated report."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]

def run():
    report=json.loads((ROOT/'results_robustness_frozen.json').read_text());out=ROOT/'docs/figures';out.mkdir(exist_ok=True)
    groups=[('additional_missing_fraction','Additional missing fraction'),('noise_multiplier','Noise multiplier'),('constant_device_bias_c','Constant temperature bias (°C)'),('device_drift_c_per_day','Temperature drift (°C/day)'),('ovulation_base_shift_days','Generated ovulation shift (days)')]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,len(groups),figsize=(18,3.6),sharey=True)
    for ax,(kind,label) in zip(axes,groups):
        rows=[r for r in report['conditions'].values() if r['condition']==kind]
        rows.sort(key=lambda r:r['value']);x=[r['value'] for r in rows]
        ax.plot(x,[r['mean_auroc'] for r in rows],'o-',color='#0e766e',label='AUROC')
        ax.plot(x,[r['mean_brier'] for r in rows],'o-',color='#a66c13',label='Brier')
        ax.set_title(label,fontsize=9);ax.set_xlabel('Sweep value');ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Mean synthetic metric');axes[0].legend(frameon=False,fontsize=8);fig.suptitle('Frozen Tier-2 synthetic robustness sweeps; no retraining or threshold retuning',fontsize=12);fig.tight_layout()
    fig.savefig(out/'robustness.svg');plt.close(fig)
if __name__=='__main__':run()
