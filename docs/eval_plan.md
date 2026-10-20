# Evaluation plan

## Scope and freeze

This document describes the current development protocol. The audit established repeated use of the older seeds during development, so they must not be presented as an untouched final evaluation. All results are synthetic-only and describe recovery within the generator, not clinical performance. Never compare these metrics with real-world published accuracy.

## Data and splits

Generate 1,200 synthetic patients with six cycles each from each of three fixed generator seeds: 97, 101, and 103. Split patients, never cycles: 70% train, 15% validation, 15% held-out test, using a deterministic patient index per seed. Keep every cycle for a patient in one partition. The patient-separated test partition was inspected across development revisions. A new frozen evaluation uses a separate predeclared protocol.

## Primary target and metrics

E1 is a synthetic current-cycle event: no ovulation or ovulation after cycle day 21. At cycle days 10, 14, and 18 report AUROC, AUPRC, Brier score, sensitivity at no more than one alert per patient-cycle, false alerts per 100 patient-cycles, and median lead days versus day 35. Report ovulation-day MAE only among cycles with simulated ovulation. Include calibration plots and subgroup metrics where sample size permits.

## Baselines and tiers

Fit one sklearn logistic-regression model for every seed, forecast day and tier on train patients. Fit Platt calibration on validation patients only. Select the alert threshold by validation-set F1 only, then report the patient-separated development partition. Report each result by data tier: tier 0 calendar history from preceding logged cycle lengths; tier 1 adds resting heart rate, HRV, steps and sleep; tier 2 adds nightly temperature; tier 3 adds EHR-lite. Tier 3 contains simulator values that help set the label, so it is reported only as an oracle-adjacent, simulator-internal check. No CGM forecast is claimed.

## Uncertainty and interpretation

For each reported G1 metric, compute patient-cluster bootstrap 95% intervals with 1,000 resamples within each held-out seed. Bootstrap resampling unit is patient, retaining all sampled patient cycles. These development results do not themselves establish abstention, conformal, or risk-coverage performance. No threshold is selected against test outcomes in the explicit current pipeline; repeated development use of the older seeds still limits holdout claims.

## Thresholds and limitations

Each fitted tier/day gets a threshold selected on its validation set only. The one-alert limit is a design constraint. These are not clinical thresholds. Any failure list, subgroup summary, or synthetic result must be labelled as such. The simulator's labels and features share assumptions, so apparent performance can overstate real-world usefulness.

## Protocol amendment before final evaluation

An early evaluation run using seeds 17, 29, and 43 revealed that the original ovulation-day distribution made nearly all generated cycles positive for E1. That run informed a generator-unit correction, so those patients are development data and their scores are not reported as held-out results. Before the final evaluation, the generator and score settings were frozen and unused generator seeds 97, 101, and 103 were reserved. Those seeds were subsequently reused during further development, as documented by the audit. Their current results are development evidence.

## G1 reporting deviations

The frozen plan requested additional coverline and boosted-tree baselines; the current benchmark implements fitted calendar and logistic sensor-tier models only. The results include PPV, per-archetype false-alarm rates at the validation-selected threshold, and an exploratory held-out lead-time-versus-false-alarm threshold sweep. The G2 dashboard's risk-coverage diagnostic runs on a separate small synthetic display cohort and is not part of held-out evaluation.

## Completed frozen follow-ups

`frozen-v1` records the subsequent one-time reserved-seed run. Stored predictions support standard average precision, reliability/ECE/calibration diagnostics, decision curves, all requested subgroups, a causal sequential alert policy, robustness sweeps, local operations measurement and a train-only timing-posterior check. Separate independent calibration patients were used to measure conformal coverage: the classification set is near its synthetic target, while the heuristic ovulation-day band fails coverage and must remain illustrative. All follow-ups remain synthetic and do not change the saved frozen prediction file, threshold, or clinical limitations.
