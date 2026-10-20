"""Evaluate the preregistered Bayesian timing-posterior check without changing the logistic score."""
import csv
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.bayesian_twin import fit, posterior
from src.features import attach_prior_cycle_lengths
from src.generator import generate
from src.splits import patient_partition

DAY=18;TIER=2;SEEDS=(7001,7003,7007)

def cluster_delta_ci(rows, reps, rng_seed):
    by={patient:np.asarray(values) for patient,values in rows.items()};patients=np.asarray(list(by));rng=np.random.default_rng(rng_seed);draws=[]
    for _ in range(reps):
        values=np.concatenate([by[p] for p in rng.choice(patients,len(patients),replace=True)])
        draws.append(float(values.mean()))
    return [float(np.quantile(draws,.025)),float(np.quantile(draws,.975))]

def run():
    protocol=json.loads((ROOT/'docs/frozen_protocol.json').read_text())['bayesian_twin']
    with (ROOT/'results/predictions_final_frozen.csv').open() as f: stored=list(csv.DictReader(f))
    result={'scope':'Synthetic train-only Bayesian timing posterior compared with frozen logistic score; it does not change deployed inference.',
            'protocol':protocol,'day':DAY,'tier':TIER,'seeds':{}}
    all_by_patient={}
    outdir=ROOT/'models/twin';outdir.mkdir(exist_ok=True)
    for seed in SEEDS:
        records=attach_prior_cycle_lengths(generate(seed));train=[r for r in records if patient_partition(r['patient'])=='train']
        model=fit(train,DAY);(outdir/f'bayesian_seed_{seed}_day_{DAY}.json').write_text(json.dumps(model,indent=2)+'\n')
        logistic={(r['patient'],int(r['cycle'])):float(r['probability']) for r in stored if int(r['seed'])==seed and int(r['day'])==DAY and int(r['tier'])==TIER}
        test=[r for r in records if (r['patient'],r['cycle']) in logistic]
        delta_by={};twin=[];log=[];y=[]
        for row in test:
            key=(row['patient'],row['cycle']);prob=posterior(model,row)['event_probability'];label=int(row['event']);base=logistic[key]
            twin.append(prob);log.append(base);y.append(label);delta_by.setdefault(row['patient'],[]).append((label-prob)**2-(label-base)**2)
        delta=float(
            np.mean((np.asarray(y) - np.asarray(twin)) ** 2)
            - np.mean((np.asarray(y) - np.asarray(log)) ** 2)
        )
        ci=cluster_delta_ci(delta_by,1000,seed+DAY)
        result['seeds'][str(seed)]={'n_cycles':len(test),'twin_brier':float(np.mean((np.asarray(y)-np.asarray(twin))**2)),
                                    'logistic_brier':float(np.mean((np.asarray(y)-np.asarray(log))**2)),
                                    'twin_minus_logistic_brier':delta,'patient_cluster_95ci':ci}
        all_by_patient.update({f'{seed}:{patient}':values for patient,values in delta_by.items()})
    means={key:float(np.mean([v[key] for v in result['seeds'].values()])) for key in ('twin_brier','logistic_brier','twin_minus_logistic_brier')}
    pooled_ci=cluster_delta_ci(all_by_patient,1000,42018)
    # Pooled patient bootstrap leaves model-specific patients together.
    result['mean_across_seeds']=means
    result['pooled_patient_cluster_95ci']=pooled_ci
    result['promotion']='integrate only if pooled upper patient-cluster bound is <= margin; this implementation remains a separate interpretation layer.'
    result['status']='noninferior synthetic check; still separate interpretation layer' if pooled_ci[1] <= protocol['noninferiority_brier_margin'] else 'not promoted; separate interpretation layer'
    (ROOT/'results_bayesian_twin_frozen.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':run()
