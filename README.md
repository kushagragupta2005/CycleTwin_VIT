# CycleTwin_VIT

**CycleTwin: synthetic cycle forecasting demo**  
Solo participant: Kushagra Gupta, full-time student, VIT.

> Decision-support research prototype only. Not for diagnosis, contraception or conception planning.

CycleTwin explores prospective per-cycle forecasting of simulated oligo-anovulation, with an ovulation-day estimate and an explicit alert budget. It is not retrospective ovulation confirmation or case/control identification.

## Design thesis and implemented scope

The design thesis is: prospective per-cycle forecasting with an ovulation-day interval, abstention and a one-alert budget; one twin with reproductive and metabolic axes connected through a shared insulin-resistance latent, including reverse luteal-to-glucose coupling; sensor tiers from period logs through wearables, nightly temperature, CGM and EHR; and an Apple Health-native input contract. These are design directions, not differentiation claims. This build implements a simplified coupled twin in the dashboard, synthetic period and wearable tiers, a limited Apple Health XML parser, explicit abstention guards, split-conformal helpers, and a one-alert selection rule. The twin is not calibrated and is not used in the G1 E1 predictor. EHR, adaptive conformal updates and evaluated CGM forecasts are not implemented. Tier 0 has a neutral score because prior-cycle history is not wired into the evaluator; tier 1 uses resting-heart-rate offsets only; tier 2 adds nightly temperature.

This repository uses synthetic data only. It contains no personal exports or clinical dataset. Metrics are internal checks against a simulator and do not establish clinical validity.

## Run

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make all
make demo-apple
```

`make all` generates synthetic patients, runs the prespecified patient-held-out evaluation, and writes `results.json`. `make demo-apple` writes a synthetic Apple Health-shaped XML export, parses it locally, and displays a small Streamlit dashboard.

## Model and scope

A stochastic generator creates synthetic patients and noisy cycle observations. A fixed score provides the evaluated prospective risk estimate; a temperature coverline heuristic estimates ovulation day, with a fixed fallback when no rise is visible. The dashboard also runs a simplified reproductive/metabolic simulator coupled through a shared synthetic latent. This is not an EKF or a clinical hormone model and is not used in the G1 metrics. The dashboard can display synthetic CGM and marginal split-conformal ranges calibrated on a separate synthetic cohort; these are illustrative and are not evaluated in the G1 results. See [assumptions](docs/assumptions.md) and the [evaluation plan](docs/eval_plan.md).

## Results

<!-- RESULTS:START -->

| Seed | Forecast day | Tier | AUROC (95% patient-cluster CI) | AUPRC (95% patient-cluster CI) | Ovulation-day MAE (95% CI) | Brier | False alerts/100 cycles |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 97 | 10 | 0 | 0.500 (0.500–0.500) | 0.469 (0.431–0.600) | 5.90 (5.51–6.30) | 0.253 | 0.000 |
| 97 | 10 | 1 | 0.494 (0.459–0.529) | 0.503 (0.438–0.572) | 5.90 (5.51–6.33) | 0.252 | 0.556 |
| 97 | 10 | 2 | 0.514 (0.478–0.547) | 0.519 (0.459–0.590) | 5.90 (5.53–6.33) | 0.311 | 0.000 |
| 97 | 14 | 0 | 0.500 (0.500–0.500) | 0.469 (0.426–0.600) | 6.69 (6.31–7.08) | 0.253 | 0.000 |
| 97 | 14 | 1 | 0.477 (0.443–0.510) | 0.493 (0.430–0.558) | 6.69 (6.29–7.09) | 0.252 | 0.093 |
| 97 | 14 | 2 | 0.637 (0.603–0.671) | 0.598 (0.532–0.659) | 6.69 (6.29–7.08) | 0.306 | 0.000 |
| 97 | 18 | 0 | 0.500 (0.500–0.500) | 0.469 (0.425–0.594) | 8.68 (8.06–9.27) | 0.253 | 0.000 |
| 97 | 18 | 1 | 0.415 (0.381–0.449) | 0.445 (0.379–0.517) | 8.68 (8.09–9.27) | 0.254 | 0.185 |
| 97 | 18 | 2 | 0.815 (0.784–0.846) | 0.738 (0.684–0.796) | 5.27 (4.95–5.60) | 0.296 | 0.000 |
| 101 | 10 | 0 | 0.500 (0.500–0.500) | 0.510 (0.439–0.614) | 5.98 (5.62–6.40) | 0.254 | 0.000 |
| 101 | 10 | 1 | 0.502 (0.467–0.537) | 0.535 (0.468–0.600) | 5.98 (5.60–6.43) | 0.253 | 0.370 |
| 101 | 10 | 2 | 0.526 (0.495–0.560) | 0.547 (0.478–0.612) | 5.98 (5.61–6.38) | 0.318 | 0.000 |
| 101 | 14 | 0 | 0.500 (0.500–0.500) | 0.510 (0.440–0.614) | 6.73 (6.32–7.08) | 0.254 | 0.000 |
| 101 | 14 | 1 | 0.487 (0.454–0.521) | 0.530 (0.463–0.594) | 6.73 (6.36–7.07) | 0.253 | 0.000 |
| 101 | 14 | 2 | 0.638 (0.606–0.668) | 0.604 (0.537–0.672) | 6.73 (6.35–7.10) | 0.316 | 0.000 |
| 101 | 18 | 0 | 0.500 (0.500–0.500) | 0.510 (0.441–0.614) | 8.71 (8.13–9.26) | 0.254 | 0.000 |
| 101 | 18 | 1 | 0.431 (0.396–0.465) | 0.477 (0.419–0.541) | 8.71 (8.09–9.31) | 0.255 | 0.093 |
| 101 | 18 | 2 | 0.830 (0.802–0.857) | 0.769 (0.715–0.817) | 5.41 (5.08–5.74) | 0.305 | 0.000 |
| 103 | 10 | 0 | 0.500 (0.500–0.500) | 0.489 (0.434–0.610) | 6.12 (5.69–6.54) | 0.253 | 0.000 |
| 103 | 10 | 1 | 0.462 (0.428–0.493) | 0.486 (0.420–0.553) | 6.12 (5.70–6.53) | 0.254 | 0.648 |
| 103 | 10 | 2 | 0.491 (0.453–0.527) | 0.504 (0.425–0.581) | 6.12 (5.74–6.53) | 0.314 | 0.000 |
| 103 | 14 | 0 | 0.500 (0.500–0.500) | 0.489 (0.428–0.606) | 6.99 (6.62–7.37) | 0.253 | 0.000 |
| 103 | 14 | 1 | 0.448 (0.414–0.482) | 0.488 (0.422–0.554) | 6.99 (6.61–7.39) | 0.253 | 0.000 |
| 103 | 14 | 2 | 0.663 (0.633–0.697) | 0.615 (0.545–0.679) | 6.99 (6.62–7.34) | 0.309 | 0.000 |
| 103 | 18 | 0 | 0.500 (0.500–0.500) | 0.489 (0.436–0.606) | 8.91 (8.29–9.47) | 0.253 | 0.000 |
| 103 | 18 | 1 | 0.405 (0.372–0.438) | 0.459 (0.391–0.530) | 8.91 (8.32–9.51) | 0.254 | 0.093 |
| 103 | 18 | 2 | 0.840 (0.814–0.864) | 0.789 (0.738–0.836) | 5.37 (5.04–5.71) | 0.298 | 0.000 |

All three fresh generator seeds are shown. Lead time and sensitivity at the alert cutoff are in `results.json`.
<!-- RESULTS:END -->

![Patient-cluster bootstrap AUROC intervals by sensor tier and forecast day](assets/auroc_by_tier.svg)

![Mean false alerts per 100 patient-cycles by sensor tier and forecast day](assets/false_alerts_by_tier.svg)

These figures aggregate the three fresh synthetic seeds; error bars span the lowest to highest seed-specific patient-cluster 95% interval. They are internal simulator checks, not clinical performance estimates.

## Data and privacy

Synthetic data only. The Apple Health adapter is a schema-compatibility smoke test, n=1 synthetic export, and clinically validates nothing. A personal export must be a consenting adult's own file, processed locally, never committed, and never used for training, tuning, or thresholds. The demo processes locally and stores only nightly aggregates. See [privacy notes](docs/privacy.md).

## Architecture and reporting

See [architecture](docs/architecture.md), [related work](docs/related_work.md), and [TRIPOD+AI notes](docs/tripod_ai.md).

## Pitch artifacts

- [Architecture diagram (PPTX)](deliverables/CycleTwin_VIT_architecture_v4.pptx) · [PDF](deliverables/CycleTwin_VIT_architecture_v4.pdf)
- [Pitch deck (PPTX)](deliverables/CycleTwin_VIT_pitch_deck_v8.pptx) · [PDF](deliverables/CycleTwin_VIT_pitch_deck_v8.pdf)
- [Jury Q&A](docs/jury_qa.md)

AI coding assistants helped build this project. All generated metrics describe synthetic data only.

Stack: Python, NumPy, Streamlit, and the Python standard library. Code is released under the MIT License.
