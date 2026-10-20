"""Insert exact audit artifacts into the audit report; never edit production data."""
import csv
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
REPORT = HERE / 'CycleTwin_full_audit.md'

def read(name):
    return json.loads((HERE / name).read_text())

def table(headers, rows):
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(cell, row)) + ' |' for row in rows])

with (HERE / 'all_metrics.csv').open() as f:
    metrics = list(csv.DictReader(f))
datasets, ranges = read('dataset_statistics.json'), read('raw_input_ranges.json')
examples = read('illustrative_examples.json')

raw = table(['Raw field', 'Total values', 'Missing', 'Minimum', 'Maximum', 'Mean', 'Population SD'],
            [[key] + [value[k] for k in ('total', 'missing', 'min', 'max', 'mean', 'population_std')]
             for key, value in ranges.items()])
raw += '\n\nStatic patient fields in this table are repeated across six cycles; their 21,600 entries are not 21,600 independent people. The ovulation-day mean includes the −1 absence sentinel and has no clinical interpretation.'

inventory = []
for key, label in [('97', 'Benchmark seed 97'), ('101', 'Benchmark seed 101'), ('103', 'Benchmark seed 103'),
                   ('combined_benchmark', 'Benchmark combined'), ('display_generated', 'Display seed 223 generated'),
                   ('display_visible', 'Display seed 223 shown'), ('calibration', 'Conformal seed 211')]:
    x = datasets[key]['all'] if key in ('97', '101', '103') else datasets[key]
    inventory.append([label] + [x[k] for k in ('patients', 'cycles', 'PMOS_patients', 'PMOS_cycles',
                                               'positive', 'negative', 'absent', 'late_ovulation')])
inventory = table(['Dataset (all synthetic)', 'People', 'Cycles', 'PMOS people', 'PMOS cycles',
                   'Positive cycles', 'Negative cycles', 'Absent', 'Ovulation >21'], inventory)
inventory += '\n\nEHR-lite: data/ehr.csv, 3,600 derivative patient rows, eight columns, zero missing cells; no new participants. Apple fixture: data/synthetic_apple_export.xml, seed 17, one generated healthy_regular participant/cycle, 281 XML records, 36 parsed date buckets; not a forecast dataset. The extra date comes from overnight sleep stages.'

splits = table(['Seed', 'Partition', 'People', 'Cycles', 'PMOS people/cycles', 'Positive', 'Negative',
                'Absent', 'Late', 'Ovulatory (MAE denominator)', 'Temperature missing/total'],
               [[seed, part, x['patients'], x['cycles'], f"{x['PMOS_patients']}/{x['PMOS_cycles']}",
                 x['positive'], x['negative'], x['absent'], x['late_ovulation'], x['observed_ovulation'],
                 f"{x['temperature']['missing']}/{x['temperature']['total']}"]
                for seed in ('97', '101', '103') for part in ('train', 'validation', 'test')
                for x in [datasets[seed][part]]])
archetypes = table(['Archetype', 'People', 'Cycles', 'Positive cycles', 'Negative cycles'],
                  [[key, x['patients'], x['cycles'], x['positive'], x['cycles']-x['positive']]
                   for key, x in datasets['combined_benchmark']['archetypes'].items()])
archetypes += '\n\nWithin PMOS-labelled cycles: 6,614 positive and 2,980 negative of 9,594. Within non-PMOS-labelled cycles: 4,408 positive and 7,598 negative of 12,006. These categories are simulator assignments, not diagnosed populations.'

aggregates = []
for day in (10, 14, 18):
    for tier in range(4):
        rows = [r for r in metrics if int(r['day']) == day and int(r['tier']) == tier]
        a = {'day': day, 'tier': tier, 'n_cycles': sum(int(r['n_cycles']) for r in rows)}
        for key in ('auroc', 'auprc', 'brier', 'ovulation_day_mae'):
            a['mean_' + key] = float(np.mean([float(r[key]) for r in rows]))
        for key in ('tp', 'fp', 'tn', 'fn'):
            a[key] = sum(int(r[key]) for r in rows)
        tp, fp, tn, fn = [a[k] for k in ('tp', 'fp', 'tn', 'fn')]
        a.update(accuracy=(tp+tn)/(tp+fp+tn+fn), precision=tp/(tp+fp), recall=tp/(tp+fn),
                 specificity=tn/(tn+fp), f1=2*tp/(2*tp+fp+fn),
                 feature_tiers=[int(r['validation_selected_feature_tier']) for r in rows])
        aggregates.append(a)
(HERE / 'aggregate_metrics.json').write_text(json.dumps(aggregates, indent=2) + '\n')
aggregate = table(['Day', 'Requested tier', 'Mean AUROC', 'Mean custom AUPRC', 'Mean Brier',
                   'Mean day-MAE', 'Feature tiers selected (97,101,103)'],
                  [[a[k] for k in ('day', 'tier', 'mean_auroc', 'mean_auprc', 'mean_brier',
                                   'mean_ovulation_day_mae', 'feature_tiers')] for a in aggregates])
aggregate += '\n\nEach row covers 3,240 cycle predictions from 540 people: 1,663 positive and 1,577 negative cycles. Day-MAE uses 2,772 ovulatory cycles, but the mean above weights seeds equally rather than pooling MAE by those denominators. The same cycles recur across forecast days and tiers; do not multiply the participant count by the number of configurations.\n\n'
aggregate += table(['Day', 'Tier', 'TP', 'FP', 'TN', 'FN', 'Pooled accuracy', 'Pooled precision',
                    'Pooled recall', 'Pooled specificity', 'Pooled F1'],
                   [[a[k] for k in ('day', 'tier', 'tp', 'fp', 'tn', 'fn', 'accuracy', 'precision',
                                    'recall', 'specificity', 'f1')] for a in aggregates])

def ci(row, name):
    return f"{row[name]} [{row[name + '_ci_low']}, {row[name + '_ci_high']}]"

saved = '#### Saved discrimination/probability metrics (point [95% patient-bootstrap interval])\n\n'
saved += table(['Seed', 'Day', 'Tier', 'Feature tier used', 'AUROC [CI]', 'Custom AUPRC [CI]', 'Brier [CI]'],
               [[r['seed'], r['day'], r['tier'], r['validation_selected_feature_tier']]
                + [ci(r, key) for key in ('auroc', 'auprc', 'brier')] for r in metrics])

decision = '#### Exact confusion counts and audit-derived operating-point metrics\n\n'
decision += 'Every configuration below has 1,080 held-out cycles from 180 patients. Accuracy, specificity and F1 were derived in this audit, not separately logged in the original evaluator. Precision and sensitivity reproduce saved PPV/recall.\n\n'
decision += table(['Seed', 'Day', 'Tier', 'TP/FP/TN/FN', 'Accuracy (fraction)', 'Precision (fraction)',
                   'Sensitivity (fraction)', 'Specificity (fraction)', 'F1 (fraction)'],
                  [[r['seed'], r['day'], r['tier'], '/'.join(r[k] for k in ('tp', 'fp', 'tn', 'fn')),
                    f"{r['accuracy_audit_derived']} ({r['accuracy_fraction']})",
                    f"{r['ppv']} ({r['precision_fraction']})", f"{r['sensitivity']} ({r['recall_fraction']})",
                    f"{r['specificity_audit_derived']} ({r['specificity_fraction']})",
                    f"{r['f1_audit_derived']} ({r['f1_fraction']})"] for r in metrics])
decision += '\n\n#### Saved operating threshold, flag rates and nominal day-35 distance\n\n'
decision += table(['Seed', 'Day', 'Tier', 'Validation threshold', 'False flags/100 all cycles',
                   'Flag rate (flagged/1080)', 'Nominal lead vs day35', 'Positive/negative counts'],
                  [[r['seed'], r['day'], r['tier'], r['validation_selected_threshold'],
                    r['false_alerts_per_100_cycles'], f"{r['alert_rate']} ({int(r['tp'])+int(r['fp'])}/1080)",
                    r['median_lead_days_vs_day_35'], f"{r['positive_denominator']}/{r['negative_denominator']}"]
                   for r in metrics])

ovulation = '#### Saved day-error metrics and validation candidate-selection evidence\n\n'
ovulation += 'The requested tier drives the day helper even when classification falls back to Tier 0. This table therefore does not describe a learned day-regression model. Gain intervals are validation baseline Brier minus candidate Brier, not held-out intervals. An empty Tier 0 entry means not applicable.\n\n'
ovulation += table(['Seed', 'Day', 'Tier', 'Day MAE [95% CI]', 'Ovulatory denominator',
                    'Validation Brier-gain [95% CI]', 'Selected feature tier'],
                   [[r['seed'], r['day'], r['tier'], ci(r, 'ovulation_day_mae'),
                     r['ovulation_mae_denominator'], r['validation_brier_gain_ci'],
                     r['validation_selected_feature_tier']] for r in metrics])
ovulation += '\n\n#### Reference constant and standard AP comparison\n\n'
ovulation += 'The reference constant below is fitted post hoc to test prevalence, p×(1−p), solely as an audit reference. It is not a trained deployment baseline. Standard AP here is an audit comparison, not the originally reported custom AUPRC.\n\n'
ovulation += table(['Seed', 'Day', 'Tier', 'Test event rate', 'Test-prevalence constant Brier',
                    'sklearn average precision'],
                   [[r[k] for k in ('seed', 'day', 'tier', 'event_rate',
                                    'constant_at_test_prevalence_brier',
                                    'sklearn_average_precision_audit_comparison')] for r in metrics])

example = table(['Patient', 'Tier', 'Heuristic score', 'Withheld', 'UI day estimate',
                  'Helper day if selected tier used', 'Generator truth day/event', 'UI class set / day band'],
                 [[x['patient'], x['tier'], x['score_heuristic'], x['abstain'], x['ovulation_estimate_shown'],
                   x['ovulation_estimate_if_selected_tier_used'],
                   f"{x['generator_truth_ovulation_day']}/{x['generator_truth_event']}",
                   f"{x['conformal_labels']} / {x['interval_shown']}"] for x in examples])
x = next(x for x in examples if x['patient'].endswith('p0002') and x['tier'] == 0)
example += '\n\nFor p0002 the exact available day-14 sensor means are: RHR offset ' + str(x['rhr_days_1_14_mean']) + ', HRV offset ' + str(x['hrv_days_1_14_mean']) + ', steps ' + str(x['steps_days_1_14_mean']) + ', sleep hours ' + str(x['sleep_days_1_14_mean']) + '. The full 14-entry raw temperature array, including nulls at missing nights, is in illustrative_examples.json. Tier 0 uses none of these sensor means.'

replacements = {'RAW_RANGES': raw, 'DATASET_TABLE': inventory, 'SPLIT_TABLE': splits,
                'ARCHETYPE_TABLE': archetypes, 'AGGREGATE_TABLE': aggregate,
                'SAVED_METRIC_TABLE': saved, 'DECISION_TABLE': decision,
                'OVULATION_TABLE': ovulation, 'EXAMPLE_TABLE': example}
text = REPORT.read_text()
for key, value in replacements.items():
    marker = '<!-- ' + key + ' -->'
    if marker not in text:
        raise RuntimeError('Missing table placeholder: ' + key)
    text = text.replace(marker, value)
REPORT.write_text(text)
print('Inserted', len(replacements), 'tables/sections; configurations:', len(metrics))
