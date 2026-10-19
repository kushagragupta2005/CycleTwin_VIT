# Evaluation plan

## Scope and freeze

This plan is committed before running evaluation on the held-out test patients. All results are synthetic-only and describe recovery within the generator, not clinical performance. Never compare these metrics with real-world published accuracy.

## Data and splits

Generate 1,200 synthetic patients with six cycles each from each of three fixed generator seeds: 97, 101, and 103. Split patients, never cycles: 70% train, 15% validation, 15% held-out test, using a deterministic patient index per seed. Keep every cycle for a patient in one partition. The test partition is evaluated once after development settings are frozen.

## Primary target and metrics

E1 is a synthetic current-cycle event: no ovulation or ovulation after cycle day 21. At cycle days 10, 14, and 18 report AUROC, AUPRC, Brier score, sensitivity at no more than one alert per patient-cycle, false alerts per 100 patient-cycles, and median lead days versus day 35. Report ovulation-day MAE only among cycles with simulated ovulation. Include calibration plots and subgroup metrics where sample size permits.

## Baselines and tiers

Compare calendar history, period-log-only, temperature-only, and a combined wearable score. Report each result by data tier: tier 0 period logs; tier 1 adds resting heart rate, HRV, steps and sleep; tier 2 adds nightly temperature. No CGM or EHR model is claimed in this initial evaluation.

## Uncertainty and interpretation

For each metric, compute patient-cluster bootstrap 95% intervals with 1,000 resamples within each held-out seed, then report seed-specific estimates and their aggregate. Bootstrap resampling unit is patient, retaining all sampled patient cycles. Abstention, adaptive conformal coverage, and risk-coverage curves are not implemented in this phase and must be marked not evaluated. No threshold will be tuned against test outcomes.

## Thresholds and limitations

The alert score threshold is fixed at 0.50 for the demo. The one-alert limit is a design constraint. These are not clinical thresholds. Any failure list, subgroup summary, or synthetic result must be labelled as such. The simulator's labels and features share assumptions, so apparent performance can overstate real-world usefulness.

## Protocol amendment before final evaluation

An early evaluation run using seeds 17, 29, and 43 revealed that the original ovulation-day distribution made nearly all generated cycles positive for E1. That run informed a generator-unit correction, so those patients are development data and their scores are not reported as held-out results. Before the final evaluation, the generator and score settings were frozen and unused generator seeds 97, 101, and 103 were reserved. Only those fresh seeds are used for the reported test metrics. This amendment is committed before the fresh test run.
