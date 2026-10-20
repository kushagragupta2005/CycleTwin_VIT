# CycleTwin_VIT

**CycleTwin: synthetic cycle forecasting demo**  
Solo participant: Kushagra Gupta, full-time student, VIT.

> Decision-support research prototype only. Not for diagnosis, contraception or conception planning.

CycleTwin explores prospective per-cycle forecasting of simulated oligo-anovulation, with an ovulation-day estimate and an explicit alert budget. It is not retrospective ovulation confirmation or case/control identification.

## Design thesis and implemented scope

The design thesis is: prospective per-cycle forecasting with an ovulation-day interval, abstention and a one-alert budget; one twin with reproductive and metabolic axes connected through a shared insulin-resistance latent, including reverse luteal-to-glucose coupling; sensor tiers from period logs through wearables, nightly temperature, CGM and EHR; and an Apple Health-native input contract. These are design directions, not differentiation claims. This build implements a simplified coupled twin in the dashboard, synthetic period and wearable tiers, a limited Apple Health XML parser, explicit abstention guards, split-conformal helpers, and a one-alert selection rule. The twin is not calibrated and is not used in the evaluated E1 predictor. Adaptive conformal updates and evaluated CGM forecasts are not implemented. The benchmark fits logistic-regression tier models on train patients, calibrates and chooses thresholds on validation patients, then evaluates held-out patients. Tier 0 uses prior logged cycle lengths; tier 1 adds RHR, HRV, steps and sleep; tier 2 adds nightly temperature.

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

A stochastic generator creates synthetic patients and noisy cycle observations. Fitted logistic-regression classifiers supply the evaluated prospective risk estimate, with Platt calibration and threshold selection on validation patients. A temperature coverline heuristic estimates ovulation day, with a fixed fallback when no rise is visible. The dashboard also runs a simplified reproductive/metabolic simulator coupled through a shared synthetic latent. This is not an EKF or a clinical hormone model and is not used in the benchmark metrics. The dashboard can display synthetic CGM and marginal split-conformal ranges calibrated on a separate synthetic cohort; these are illustrative and are not evaluated in the benchmark results. See [assumptions](docs/assumptions.md) and the [evaluation plan](docs/eval_plan.md).

## Results

<!-- RESULTS:START -->

| Seed | Forecast day | Tier | AUROC (95% patient-cluster CI) | AUPRC (95% patient-cluster CI) | Ovulation-day MAE (95% CI) | Brier | Validation threshold | Sensitivity | PPV | False alerts/100 cycles |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 97 | 10 | 0 | 0.841 (0.813–0.867) | 0.828 (0.787–0.866) | 5.90 (5.51–6.30) | 0.161 | 0.425 | 0.888 | 0.720 | 17.500 |
| 97 | 10 | 1 | 0.841 (0.811–0.868) | 0.828 (0.781–0.867) | 5.90 (5.51–6.33) | 0.162 | 0.425 | 0.888 | 0.720 | 17.500 |
| 97 | 10 | 2 | 0.842 (0.814–0.866) | 0.829 (0.786–0.867) | 5.90 (5.53–6.33) | 0.162 | 0.456 | 0.883 | 0.728 | 16.667 |
| 97 | 14 | 0 | 0.841 (0.813–0.867) | 0.828 (0.786–0.867) | 6.69 (6.31–7.08) | 0.161 | 0.425 | 0.888 | 0.720 | 17.500 |
| 97 | 14 | 1 | 0.842 (0.812–0.868) | 0.829 (0.781–0.867) | 6.69 (6.29–7.09) | 0.161 | 0.413 | 0.888 | 0.719 | 17.593 |
| 97 | 14 | 2 | 0.854 (0.825–0.879) | 0.836 (0.790–0.874) | 6.69 (6.29–7.08) | 0.155 | 0.412 | 0.857 | 0.729 | 16.111 |
| 97 | 18 | 0 | 0.841 (0.812–0.867) | 0.828 (0.787–0.866) | 8.68 (8.06–9.27) | 0.161 | 0.425 | 0.888 | 0.720 | 17.500 |
| 97 | 18 | 1 | 0.847 (0.818–0.873) | 0.833 (0.792–0.871) | 8.68 (8.09–9.27) | 0.159 | 0.383 | 0.903 | 0.716 | 18.148 |
| 97 | 18 | 2 | 0.898 (0.873–0.922) | 0.867 (0.827–0.904) | 5.27 (4.95–5.60) | 0.122 | 0.385 | 0.934 | 0.779 | 13.426 |
| 101 | 10 | 0 | 0.848 (0.820–0.875) | 0.854 (0.813–0.890) | 5.98 (5.62–6.40) | 0.157 | 0.392 | 0.880 | 0.736 | 16.481 |
| 101 | 10 | 1 | 0.847 (0.821–0.871) | 0.855 (0.813–0.890) | 5.98 (5.60–6.43) | 0.157 | 0.477 | 0.816 | 0.755 | 13.889 |
| 101 | 10 | 2 | 0.846 (0.818–0.872) | 0.854 (0.810–0.889) | 5.98 (5.61–6.38) | 0.158 | 0.404 | 0.874 | 0.741 | 16.019 |
| 101 | 14 | 0 | 0.848 (0.820–0.873) | 0.854 (0.810–0.890) | 6.73 (6.32–7.08) | 0.157 | 0.392 | 0.880 | 0.736 | 16.481 |
| 101 | 14 | 1 | 0.848 (0.819–0.873) | 0.856 (0.816–0.889) | 6.73 (6.36–7.07) | 0.157 | 0.375 | 0.890 | 0.734 | 16.852 |
| 101 | 14 | 2 | 0.865 (0.836–0.888) | 0.870 (0.830–0.901) | 6.73 (6.35–7.10) | 0.149 | 0.396 | 0.869 | 0.759 | 14.444 |
| 101 | 18 | 0 | 0.848 (0.820–0.871) | 0.854 (0.813–0.891) | 8.71 (8.13–9.26) | 0.157 | 0.392 | 0.880 | 0.736 | 16.481 |
| 101 | 18 | 1 | 0.856 (0.828–0.881) | 0.861 (0.818–0.895) | 8.71 (8.09–9.31) | 0.154 | 0.410 | 0.858 | 0.760 | 14.167 |
| 101 | 18 | 2 | 0.923 (0.902–0.942) | 0.915 (0.880–0.942) | 5.41 (5.08–5.74) | 0.108 | 0.424 | 0.919 | 0.817 | 10.741 |
| 103 | 10 | 0 | 0.853 (0.821–0.880) | 0.843 (0.801–0.881) | 6.12 (5.69–6.54) | 0.155 | 0.444 | 0.891 | 0.734 | 16.481 |
| 103 | 10 | 1 | 0.852 (0.820–0.877) | 0.842 (0.795–0.880) | 6.12 (5.70–6.53) | 0.155 | 0.426 | 0.899 | 0.733 | 16.759 |
| 103 | 10 | 2 | 0.854 (0.822–0.880) | 0.844 (0.794–0.880) | 6.12 (5.74–6.53) | 0.155 | 0.501 | 0.817 | 0.768 | 12.593 |
| 103 | 14 | 0 | 0.853 (0.824–0.881) | 0.843 (0.796–0.882) | 6.99 (6.62–7.37) | 0.155 | 0.444 | 0.891 | 0.734 | 16.481 |
| 103 | 14 | 1 | 0.854 (0.822–0.883) | 0.843 (0.798–0.882) | 6.99 (6.61–7.39) | 0.155 | 0.389 | 0.918 | 0.723 | 17.963 |
| 103 | 14 | 2 | 0.869 (0.837–0.899) | 0.855 (0.814–0.893) | 6.99 (6.62–7.34) | 0.146 | 0.411 | 0.900 | 0.756 | 14.815 |
| 103 | 18 | 0 | 0.853 (0.823–0.881) | 0.843 (0.797–0.884) | 8.91 (8.29–9.47) | 0.155 | 0.444 | 0.891 | 0.734 | 16.481 |
| 103 | 18 | 1 | 0.856 (0.826–0.882) | 0.845 (0.799–0.880) | 8.91 (8.32–9.51) | 0.154 | 0.352 | 0.924 | 0.712 | 19.074 |
| 103 | 18 | 2 | 0.920 (0.898–0.940) | 0.897 (0.863–0.929) | 5.37 (5.04–5.71) | 0.109 | 0.330 | 0.962 | 0.770 | 14.722 |

All three fresh generator seeds are shown. Models are fitted on train patients, Platt-calibrated and threshold-selected on validation patients, then evaluated once on held-out patients.
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
