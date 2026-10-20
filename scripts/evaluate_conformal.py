"""Evaluate preregistered split-conformal coverage on frozen synthetic test cycles."""
import csv
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.conformal import calibrate_binary, calibrate_ovulation_interval, classification_set, ovulation_interval
from src.features import attach_prior_cycle_lengths
from src.generator import generate
from src.inference import predict
from src.model import estimate_ovulation_day

MODEL_SEEDS=(7001,7003,7007);DAYS=(10,14,18);TIERS=(0,1,2,3)

def calibration_rows(model_seed,tier,day,protocol):
    seed=300000+model_seed*10000+tier*100+day
    rows=attach_prior_cycle_lengths(generate(seed,patients=protocol['patients_per_calibration'],cycles=protocol['cycles_generated']))
    rng=np.random.default_rng(seed+1);selected=[]
    for patient in sorted({r['patient'] for r in rows}):
        options=[r for r in rows if r['patient']==patient];selected.append(options[int(rng.integers(len(options)))])
    return seed,selected

def summarize(rows,q_class,q_day):
    y=np.asarray([r['event'] for r in rows]);p=np.asarray([r['probability'] for r in rows]);sets=[classification_set(prob,q_class) for prob in p]
    ccover=float(np.mean([label in prediction for label,prediction in zip(y,sets)]));sizes=[len(x) for x in sets]
    ov=[r for r in rows if r['ovulation_day']>0]
    dcover=float(np.mean([r['ovulation_day'] in ovulation_interval(r['ovulation_estimate'],q_day) for r in ov])) if ov else None
    return {'n_cycles':len(rows),'classification_coverage':ccover,'mean_classification_set_size':float(np.mean(sizes)),
            'singleton_rate':float(np.mean(np.asarray(sizes)==1)),'empty_set_rate':float(np.mean(np.asarray(sizes)==0)),
            'n_present_ovulation':len(ov),'ovulation_day_band_coverage':dcover,'day_band_mean_width':float(2*np.ceil(q_day))}

def run():
    protocol=json.loads((ROOT/'docs/frozen_protocol.json').read_text())['conformal']
    with (ROOT/'results/predictions_final_frozen.csv').open() as f: stored=list(csv.DictReader(f))
    result={'scope':'Frozen synthetic split-conformal coverage; marginal and generator-specific, not individual or clinical coverage.',
            'protocol':protocol,'results':{}}
    for model_seed in MODEL_SEEDS:
        generated={(r['patient'],r['cycle']):r for r in attach_prior_cycle_lengths(generate(model_seed))}
        for day in DAYS:
            for tier in TIERS:
                calibration_seed,cal=calibration_rows(model_seed,tier,day,protocol)
                outputs=[predict(r,day,tier,seed=model_seed) for r in cal]
                q_class=calibrate_binary([r['event'] for r in cal],[o['prob'] for o in outputs],protocol['alpha'])
                cal_ov=[(r,o) for r,o in zip(cal,outputs) if r['ovulation_day']>0]
                q_day=calibrate_ovulation_interval([r['ovulation_day'] for r,_ in cal_ov],[estimate_ovulation_day(r,day,o['selected_tier']) for r,o in cal_ov],protocol['alpha'])
                test=[]
                for r in stored:
                    if int(r['seed'])!=model_seed or int(r['day'])!=day or int(r['tier'])!=tier: continue
                    original=generated[(r['patient'],int(r['cycle']))]
                    test.append({'event':int(r['event']),'probability':float(r['probability']),'ovulation_day':int(r['ovulation_day']),
                                 'ovulation_estimate':int(r['ovulation_estimate']),'archetype':r['archetype']})
                key=f'seed_{model_seed}_day_{day}_tier_{tier}'
                result['results'][key]={'calibration_seed':calibration_seed,'q_class':q_class,'q_day':q_day,
                                        'overall':summarize(test,q_class,q_day),
                                        'by_archetype':{name:summarize([r for r in test if r['archetype']==name],q_class,q_day) for name in sorted({r['archetype'] for r in test})}}
    (ROOT/'results_conformal_frozen.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':run()
