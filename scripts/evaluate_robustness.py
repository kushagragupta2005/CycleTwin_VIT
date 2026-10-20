"""Predeclared synthetic perturbation sweeps on frozen Tier-2 models; no fitting."""
import csv
import copy
import json
from pathlib import Path
import sys

import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.features import attach_prior_cycle_lengths
from src.generator import generate
from src.inference import predict
from src.safety import abstain, synthetic_safety_record

DAY=18; TIER=2; MODEL_SEEDS=(7001,7003,7007); SHIFT_SEEDS=(9101,9103,9107)


def perturb(record, kind, value, rng):
    row=copy.deepcopy(record); temp=np.asarray(row['temperature'],dtype=float).copy()
    if kind=='additional_missing_fraction':
        observed=np.flatnonzero(np.isfinite(temp[:DAY])); take=int(round(len(observed)*value))
        if take: temp[rng.choice(observed,size=take,replace=False)]=np.nan
    elif kind=='noise_multiplier':
        observed=np.flatnonzero(np.isfinite(temp[:DAY])); temp[observed]+=rng.normal(0,.035*(value-1),len(observed))
    elif kind=='constant_device_bias_c': temp[:DAY]+=value
    elif kind=='device_drift_c_per_day': temp[:DAY]+=value*np.arange(DAY)
    elif kind=='ovulation_base_shift_days':
        old=int(row['ovulation_day'])
        if old > 0:
            new=min(45,old+int(value)); row['ovulation_day']=new; row['event']=int(new>21)
            temp[old:]-=.20;temp[new:]+=.20
    row['temperature']=temp
    return row


def evaluate(records, model_seed, kind, value, rng_seed):
    rng=np.random.default_rng(rng_seed); rows=[perturb(r,kind,value,rng) for r in records]
    y=np.asarray([r['event'] for r in rows]); p=np.asarray([predict(r,DAY,TIER,seed=model_seed)['prob'] for r in rows])
    withheld=np.mean([abstain(synthetic_safety_record(r,DAY)) for r in rows])
    return {'n_cycles':len(rows),'positive_cycles':int(y.sum()),'auroc':float(roc_auc_score(y,p)),
            'brier':float(brier_score_loss(y,p)),'safety_withhold_rate':float(withheld)}


def run():
    protocol=json.loads((ROOT/'docs/frozen_protocol.json').read_text())['robustness']
    with (ROOT/'results/predictions_final_frozen.csv').open() as f: stored=list(csv.DictReader(f))
    result={'scope':'Synthetic, post-freeze robustness extension; frozen predictor artifacts and thresholds unchanged.',
            'day':DAY,'tier':TIER,'protocol':protocol,'conditions':{}}
    base_indexes={}
    for seed in MODEL_SEEDS:
        base_indexes[seed]={r['patient'].split('-p')[-1] for r in stored if int(r['seed'])==seed and int(r['day'])==DAY and int(r['tier'])==TIER}
    conditions=[('additional_missing_fraction',x) for x in protocol['missing_fraction']]
    conditions += [('noise_multiplier',x) for x in protocol['noise_multiplier']]
    conditions += [('constant_device_bias_c',x) for x in protocol['constant_device_bias_c']]
    conditions += [('device_drift_c_per_day',x) for x in protocol['device_drift_c_per_day']]
    conditions += [('ovulation_base_shift_days',x) for x in protocol['generator_ovulation_base_shift_days']]
    csv_rows=[]
    for kind,value in conditions:
        per_seed=[]
        for index,model_seed in enumerate(MODEL_SEEDS):
            source_seed=SHIFT_SEEDS[index] if kind=='ovulation_base_shift_days' else model_seed
            generated=attach_prior_cycle_lengths(generate(source_seed))
            selected=[r for r in generated if r['patient'].split('-p')[-1] in base_indexes[model_seed]]
            metrics=evaluate(selected,model_seed,kind,value,100000+model_seed+int((value+2)*1000))
            metrics.update(model_seed=model_seed,source_seed=source_seed)
            per_seed.append(metrics);csv_rows.append({'condition':kind,'value':value,**metrics})
        result['conditions'][f'{kind}={value}']={'condition':kind,'value':value,'per_seed':per_seed,
            'mean_auroc':float(np.mean([x['auroc'] for x in per_seed])),
            'mean_brier':float(np.mean([x['brier'] for x in per_seed])),
            'mean_safety_withhold_rate':float(np.mean([x['safety_withhold_rate'] for x in per_seed]))}
    (ROOT/'results_robustness_frozen.json').write_text(json.dumps(result,indent=2)+'\n')
    with (ROOT/'results/robustness_frozen.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)


if __name__=='__main__':run()
