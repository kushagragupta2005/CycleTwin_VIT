"""Standard scientific figures from claims; no hand-entered performance values."""
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def run():
    c=json.loads((ROOT/'docs/claims.json').read_text()); r=c['reporting']['frozen'];days=c['configuration']['days']
    output=ROOT/'docs/figures';output.mkdir(exist_ok=True)
    preview=ROOT/'.ppt_build/reporting-previews';preview.mkdir(exist_ok=True,parents=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,ax=plt.subplots(figsize=(8,5));ax.plot([0,1],[0,1],'--',color='#aeb8b4',label='Equal predicted/observed frequency')
    for day,color in zip(days,('#86918c','#a66c13','#0e766e')):
        all_bins=[s[f'day_{day}_tier_2']['all']['reliability_bins'] for s in r.values()]
        xs,ys=[],[]
        for i in range(len(all_bins[0])):
            n=sum(b[i]['n'] for b in all_bins)
            if n:
                xs.append(sum(b[i]['mean_probability']*b[i]['n'] for b in all_bins if b[i]['n'])/n)
                ys.append(sum(b[i]['positive'] for b in all_bins)/n)
        ax.plot(xs,ys,'o-',color=color,label=f'Synthetic day {day}, Tier 2')
    ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean predicted probability in score bin',ylabel='Observed generated-event fraction',title='Synthetic frozen reliability: separate fitted models, pooled bins')
    ax.legend(frameon=False,fontsize=9);fig.tight_layout();fig.savefig(output/'reliability.svg');fig.savefig(preview/'reliability.png',dpi=120);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5))
    for tier,color in [(0,'#86918c'),(2,'#0e766e')]:
        curves=[s[f'day_{max(days)}_tier_{tier}']['all']['decision_curve'] for s in r.values()]
        x=[p['threshold'] for p in curves[0]]
        y=np.mean([[p['net_benefit'] for p in curve] for curve in curves],axis=0)
        ax.plot(x,y,'o-',color=color,label=f'Synthetic Tier {tier}')
    ax.plot(x,np.mean([[p['treat_all'] for p in curve] for curve in curves],axis=0),'--',color='#a66c13',label='Flag all')
    ax.axhline(0,color='#17242b',linewidth=1,label='Flag none')
    ax.set(xlabel='Assumed threshold probability',ylabel='Synthetic net benefit under assumed threshold odds',title='Synthetic frozen decision curves: descriptive, no clinical utility claim')
    ax.legend(frameon=False);fig.tight_layout();fig.savefig(output/'decision_curve.svg');fig.savefig(preview/'decision_curve.png',dpi=120);plt.close(fig)


if __name__=='__main__':run()
