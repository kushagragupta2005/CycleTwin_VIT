"""Add diagnostic reporting from stored predictions; never fit/update a predictor."""
import csv
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.generator import generate
from src.reporting import metrics,reliability,calibration_diagnostic,decision_curve
from src.safety import abstain,synthetic_safety_record


def run():
    protocol=json.loads((ROOT/'docs/frozen_protocol.json').read_text())['reporting_followups']
    result={'scope':'Synthetic reporting only; no predictor or threshold is changed',
            'method':'Standard threshold-grouped sklearn average precision replaces custom rank-by-rank AUPRC in reporting; frozen raw result remains immutable.',
            'development':{},'frozen':{}}
    csv_rows=[]
    for dataset,filename in [('development','predictions_heldout.csv'),('frozen','predictions_final_frozen.csv')]:
        with (ROOT/'results'/filename).open() as handle: records=list(csv.DictReader(handle))
        for seed in sorted({int(r['seed']) for r in records}):
            generated={(r['patient'],r['cycle']):r for r in generate(seed)}
            result[dataset][str(seed)]={}
            for day in (10,14,18):
                for tier in (0,1,2,3):
                    group=[r for r in records if int(r['seed'])==seed and int(r['day'])==day and int(r['tier'])==tier]
                    subsets={'all':group,'PMOS-only':[r for r in group if r['archetype'].startswith('PMOS')],
                             'safety-gate-passing':[r for r in group if not abstain(synthetic_safety_record(generated[(r['patient'],int(r['cycle']))],day))]}
                    subsets.update({name:[r for r in group if r['archetype']==name] for name in sorted({r['archetype'] for r in group})})
                    output={}
                    for name,rows in subsets.items():
                        if not rows:
                            output[name]={'n':0,'reason':'No rows'};continue
                        y=np.array([int(r['event']) for r in rows]);p=np.array([float(r['probability']) for r in rows])
                        threshold=float(rows[0]['threshold']);patients=[r['patient'] for r in rows]
                        m=metrics(y,p,threshold,patients,protocol['patient_bootstrap_reps'],seed+day+tier)
                        bins,ece=reliability(y,p,protocol['reliability_equal_width_bins'])
                        m.update(ece=ece,reliability_bins=bins,calibration_diagnostic=calibration_diagnostic(y,p),
                                 decision_curve=decision_curve(y,p,protocol['decision_curve_thresholds']))
                        output[name]=m
                        flat={k:v for k,v in m.items() if not isinstance(v,(dict,list))}
                        for metric,interval in m['intervals'].items():
                            if interval['95ci']:
                                flat[metric+'_ci_low'],flat[metric+'_ci_high']=interval['95ci']
                            flat[metric+'_valid_bootstrap_reps']=interval['valid_resamples']
                        csv_rows.append({'dataset':dataset,'seed':seed,'day':day,'tier':tier,'subset':name,**flat})
                    result[dataset][str(seed)][f'day_{day}_tier_{tier}']=output
                    print('Reported synthetic',dataset,seed,day,tier,flush=True)
    path=ROOT/'results_reporting.json';path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    with (ROOT/'results/reporting_subgroups.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(dict.fromkeys(k for row in csv_rows for k in row)))
        writer.writeheader();writer.writerows(csv_rows)
    # This is the intentional metric-definition correction, not a predictor change.
    development=json.loads((ROOT/'results.json').read_text())
    for seed,sr in development['seeds'].items():
        for key,m in sr['metrics'].items():
            point=result['development'][seed][key]['all']
            m.setdefault('legacy_custom_auprc',m['auprc'])
            m.setdefault('legacy_custom_auprc_cluster_bootstrap_95ci',m['auprc_cluster_bootstrap_95ci'])
            m['auprc']=point['average_precision'];m['auprc_cluster_bootstrap_95ci']=point['intervals']['average_precision']['95ci']
            m['auprc_definition']='sklearn average_precision_score; threshold-grouped ties'
    (ROOT/'results.json').write_text(json.dumps(development,indent=2)+'\n')


if __name__=='__main__':run()
