"""Post-freeze simulated lab-like extension, deliberately separate from the frozen primary endpoint."""
import json
from pathlib import Path
import sys
import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.features import attach_prior_cycle_lengths, build_feature_matrix
from src.fitted import PlattModel, choose_f1_threshold
from src.generator import generate
from src.lab_proxy import assay_like_features
from src.splits import patient_partition

DAY=18;CV=.15;SEEDS=(7001,7003,7007)

def matrix(rows, seed):
    return np.column_stack([build_feature_matrix(rows,DAY,2),np.asarray([assay_like_features(r,seed,CV) for r in rows])])

def run():
    frozen=json.loads((ROOT/'results_final_frozen.json').read_text())
    result={'scope':'Post-freeze synthetic extension. Assay-like indices are simulated from label-generating internal latents and are neither hormone measurements nor clinical EHR.',
            'day':DAY,'assay_cv':CV,'features':['Tier-2 wearable features','simulated_ir_assay_like_index','simulated_androgen_assay_like_index'],
            'seeds':{},'original_tier3_upper_bound_reference':{}}
    for seed in SEEDS:
        rows=attach_prior_cycle_lengths(generate(seed));parts={name:[r for r in rows if patient_partition(r['patient'])==name] for name in ('train','validation','test')}
        fit=PlattModel().fit(matrix(parts['train'],seed),[r['event'] for r in parts['train']],matrix(parts['validation'],seed),[r['event'] for r in parts['validation']])
        threshold=choose_f1_threshold([r['event'] for r in parts['validation']],fit.predict_proba(matrix(parts['validation'],seed)))
        y=np.asarray([r['event'] for r in parts['test']]);p=fit.predict_proba(matrix(parts['test'],seed));flag=p>=threshold
        tp=int(np.sum(flag & (y==1)));fp=int(np.sum(flag & (y==0)));fn=int(np.sum(~flag & (y==1)))
        result['seeds'][str(seed)]={'n_cycles':len(y),'positive_cycles':int(y.sum()),'auroc':float(roc_auc_score(y,p)),
                                    'average_precision':float(average_precision_score(y,p)),'brier':float(brier_score_loss(y,p)),
                                    'validation_f1_threshold':float(threshold),'sensitivity':tp/(tp+fn),'ppv':tp/(tp+fp) if tp+fp else None}
        result['original_tier3_upper_bound_reference'][str(seed)]=frozen['seeds'][str(seed)]['metrics']['day_18_tier_3']
    result['means']={key:float(np.mean([x[key] for x in result['seeds'].values()])) for key in ('auroc','average_precision','brier','sensitivity','ppv')}
    result['original_tier3_upper_bound_means']={key:float(np.mean([x[key] for x in result['original_tier3_upper_bound_reference'].values()])) for key in ('auroc','auprc','brier')}
    (ROOT/'results_lab_proxy_extension.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':run()
