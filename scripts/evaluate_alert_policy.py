"""Evaluate the frozen causal, one-alert policy from saved scores only."""
import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.alerts import apply_sequential_alert_policy
from src.generator import generate
from src.safety import synthetic_safety_record, abstain


def policy_metrics(rows, generated):
    selected=apply_sequential_alert_policy(rows)
    cycles={key:record for key,record in generated.items() if key in {(r['patient'],int(r['cycle'])) for r in rows}}
    alerts={(r['patient'],int(r['cycle'])):r for r in selected if r['alert']}
    events={key:int(record['event']) for key,record in cycles.items()}
    tp=[key for key in alerts if events[key]]
    false=[key for key in alerts if not events[key]]
    event_count=sum(events.values()); missed=sum(1 for key,event in events.items() if event and key not in alerts)
    present_leads=[cycles[key]['ovulation_day']-alert['day'] for key,alert in alerts.items()
                   if events[key] and cycles[key]['ovulation_day'] > 0]
    exposed_years=sum(record['cycle_length'] for record in cycles.values())/365.25
    safety_withheld=sum(1 for r in selected if r['abstain'])
    return {
        'n_cycles':len(cycles),'event_cycles':event_count,'alerts':len(alerts),'true_positive_alerts':len(tp),
        'false_alerts':len(false),'alert_precision':len(tp)/len(alerts) if alerts else None,
        'missed_events':missed,'missed_event_rate':missed/event_count if event_count else None,
        'false_alerts_per_synthetic_patient_year':len(false)/exposed_years if exposed_years else None,
        'synthetic_exposure_patient_years':exposed_years,'safety_withheld_snapshots':safety_withheld,
        'true_positive_present_ovulation_alerts':len(present_leads),
        'lead_time_days_mean':float(np.mean(present_leads)) if present_leads else None,
        'lead_time_days_median':float(np.median(present_leads)) if present_leads else None,
        'lead_time_days_values':present_leads,
    }, selected


def run():
    protocol=json.loads((ROOT/'docs/frozen_protocol.json').read_text())['sequential_policy']
    with (ROOT/'results/predictions_final_frozen.csv').open() as handle: stored=list(csv.DictReader(handle))
    result={'scope':'Frozen synthetic stored predictions only; no retraining, retuning, or clinical rate claim.',
            'policy':protocol,'tiers':{}}
    output_rows=[]
    for tier in range(4):
        result['tiers'][str(tier)]={}
        for seed in (7001,7003,7007):
            generated={(r['patient'],r['cycle']):r for r in generate(seed)}
            rows=[]
            for r in stored:
                if int(r['seed']) != seed or int(r['tier']) != tier or int(r['day']) not in protocol['days']: continue
                record=generated[(r['patient'],int(r['cycle']))]
                rows.append({'patient':r['patient'],'cycle':int(r['cycle']),'day':int(r['day']),
                             'risk':float(r['probability']),'threshold':float(r['threshold']),
                             'abstain':abstain(synthetic_safety_record(record,int(r['day']))),
                             'event':int(r['event']),'ovulation_day':int(r['ovulation_day'])})
            summary, selected=policy_metrics(rows,generated)
            result['tiers'][str(tier)][str(seed)]=summary
            for row in selected:
                output_rows.append({'tier':tier,'seed':seed,**row})
    (ROOT/'results_alert_policy_frozen.json').write_text(json.dumps(result,indent=2)+'\n')
    fields=['tier','seed','patient','cycle','day','risk','threshold','abstain','event','ovulation_day','alert']
    with (ROOT/'results/alert_policy_frozen_rows.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(output_rows)


if __name__=='__main__': run()
