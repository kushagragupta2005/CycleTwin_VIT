# CycleTwin_VIT

**CycleTwin: synthetic cycle forecasting demo**  
Solo participant: Kushagra Gupta, full-time student, VIT.

> Decision-support research prototype only. Not for diagnosis, contraception or conception planning.

CycleTwin explores prospective per-cycle forecasting of simulated oligo-anovulation, with an ovulation-day estimate and an explicit alert budget. It is not retrospective ovulation confirmation or case/control identification.

## Design thesis and implemented scope

The design thesis is: prospective per-cycle forecasting with an ovulation-day interval, abstention and a one-alert budget; one twin with reproductive and metabolic axes connected through a shared insulin-resistance latent, including reverse luteal-to-glucose coupling; sensor tiers from period logs through wearables, nightly temperature, CGM and EHR; and an Apple Health-native input contract. These are design directions, not differentiation claims. This build implements a simplified coupled twin in the dashboard, synthetic period and wearable tiers, a limited Apple Health XML parser, explicit abstention guards, split-conformal helpers, and a one-alert selection rule. The twin is not calibrated and is not used in the evaluated E1 predictor. Adaptive conformal updates and evaluated CGM forecasts are not implemented. The benchmark fits logistic-regression tier candidates on train patients, retains richer features only when a patient-cluster bootstrap 95% interval for the validation Brier gain is above zero, Platt-calibrates and selects F1 thresholds on validation, then evaluates held-out patients once. Tier 0 uses the mean of up to the last three logged cycle lengths; tier 1 adds RHR, HRV, steps and sleep; tier 2 adds nightly temperature; tier 3 adds synthetic EHR-lite. Tier 3 is oracle-adjacent because it includes simulator variables used to generate the label, so its numbers are simulator-internal checks only.

This repository uses synthetic data only. It contains no personal exports or clinical dataset. Metrics are internal checks against a simulator and do not establish clinical validity.

## Run

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make all
make demo-apple
```

`make all` generates synthetic patients, runs the prespecified patient-held-out evaluation, and writes `results.json`. `make demo-apple` writes a synthetic Apple Health-shaped XML export, parses it locally, and displays a small Streamlit dashboard.

Dependency versions are pinned to the evaluation environment: Python 3.9.6, NumPy 2.0.2, scikit-learn 1.6.1 and SciPy 1.13.1, with explicit pandas, Streamlit, Altair, joblib and threadpoolctl requirements. On 20 October 2026, a fresh virtual environment installed only from `requirements.txt` passed both fitted-pipeline tests and all 13 unit tests without additional package installation. A complete benchmark rerun in that environment reproduced every field of the committed `results.json` exactly (36 seed/day/tier results). After activating the environment, run `python -m unittest discover -s tests -v`; `make all` regenerates the benchmark and figures.

## Model and scope

A stochastic generator creates synthetic patients and noisy cycle observations. Fitted logistic-regression classifiers supply the evaluated prospective risk estimate, with Platt calibration and threshold selection on validation patients. A temperature coverline heuristic estimates ovulation day, with a fixed fallback when no rise is visible. The dashboard also runs a simplified reproductive/metabolic simulator coupled through a shared synthetic latent. This is not an EKF or a clinical hormone model and is not used in the benchmark metrics. The dashboard can display synthetic CGM and marginal split-conformal ranges calibrated on a separate synthetic cohort; these are illustrative and are not evaluated in the benchmark results. See [assumptions](docs/assumptions.md) and the [evaluation plan](docs/eval_plan.md).

## Results

<!-- RESULTS:START -->

| Seed | Forecast day | Tier | AUROC (95% patient-cluster CI) | AUPRC (95% patient-cluster CI) | Ovulation-day MAE (95% CI) | Brier | Validation threshold | Sensitivity | PPV | False alerts/100 cycles |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 97 | 10 | 0 | 0.843 (0.813–0.871) | 0.858 (0.818–0.893) | 6.17 (5.80–6.59) | 0.161 | 0.480 | 0.836 | 0.743 | 15.185 |
| 97 | 10 | 1 | 0.843 (0.812–0.870) | 0.858 (0.816–0.895) | 6.17 (5.79–6.59) | 0.161 | 0.480 | 0.836 | 0.743 | 15.185 |
| 97 | 10 | 2 | 0.843 (0.815–0.868) | 0.858 (0.818–0.891) | 6.17 (5.81–6.59) | 0.161 | 0.480 | 0.836 | 0.743 | 15.185 |
| 97 | 10 | 3 | 0.843 (0.812–0.869) | 0.858 (0.816–0.891) | 6.17 (5.80–6.56) | 0.161 | 0.480 | 0.836 | 0.743 | 15.185 |
| 97 | 14 | 0 | 0.843 (0.816–0.870) | 0.858 (0.821–0.894) | 6.79 (6.43–7.13) | 0.161 | 0.480 | 0.836 | 0.743 | 15.185 |
| 97 | 14 | 1 | 0.843 (0.813–0.872) | 0.858 (0.815–0.891) | 6.79 (6.40–7.14) | 0.161 | 0.480 | 0.836 | 0.743 | 15.185 |
| 97 | 14 | 2 | 0.862 (0.833–0.886) | 0.863 (0.818–0.896) | 6.79 (6.41–7.15) | 0.150 | 0.404 | 0.863 | 0.764 | 13.981 |
| 97 | 14 | 3 | 0.843 (0.815–0.871) | 0.858 (0.821–0.892) | 6.79 (6.41–7.15) | 0.161 | 0.480 | 0.836 | 0.743 | 15.185 |
| 97 | 18 | 0 | 0.843 (0.814–0.871) | 0.858 (0.816–0.892) | 8.58 (7.96–9.13) | 0.161 | 0.480 | 0.836 | 0.743 | 15.185 |
| 97 | 18 | 1 | 0.843 (0.812–0.871) | 0.858 (0.819–0.893) | 8.58 (8.00–9.16) | 0.161 | 0.480 | 0.836 | 0.743 | 15.185 |
| 97 | 18 | 2 | 0.909 (0.886–0.929) | 0.888 (0.851–0.921) | 5.14 (4.85–5.45) | 0.116 | 0.312 | 0.949 | 0.796 | 12.778 |
| 97 | 18 | 3 | 0.909 (0.885–0.930) | 0.889 (0.848–0.923) | 5.14 (4.86–5.45) | 0.116 | 0.339 | 0.935 | 0.796 | 12.593 |
| 101 | 10 | 0 | 0.837 (0.805–0.867) | 0.830 (0.781–0.871) | 5.85 (5.49–6.24) | 0.164 | 0.472 | 0.834 | 0.729 | 15.741 |
| 101 | 10 | 1 | 0.837 (0.804–0.865) | 0.830 (0.780–0.866) | 5.85 (5.46–6.26) | 0.164 | 0.472 | 0.834 | 0.729 | 15.741 |
| 101 | 10 | 2 | 0.837 (0.805–0.864) | 0.830 (0.780–0.868) | 5.85 (5.48–6.27) | 0.164 | 0.472 | 0.834 | 0.729 | 15.741 |
| 101 | 10 | 3 | 0.837 (0.805–0.866) | 0.830 (0.784–0.870) | 5.85 (5.47–6.30) | 0.164 | 0.472 | 0.834 | 0.729 | 15.741 |
| 101 | 14 | 0 | 0.837 (0.805–0.865) | 0.830 (0.781–0.871) | 6.62 (6.26–6.99) | 0.164 | 0.472 | 0.834 | 0.729 | 15.741 |
| 101 | 14 | 1 | 0.837 (0.806–0.864) | 0.830 (0.780–0.868) | 6.62 (6.26–6.98) | 0.164 | 0.472 | 0.834 | 0.729 | 15.741 |
| 101 | 14 | 2 | 0.837 (0.806–0.865) | 0.830 (0.783–0.869) | 6.62 (6.26–6.97) | 0.164 | 0.472 | 0.834 | 0.729 | 15.741 |
| 101 | 14 | 3 | 0.837 (0.803–0.866) | 0.830 (0.780–0.870) | 6.62 (6.26–6.97) | 0.164 | 0.472 | 0.834 | 0.729 | 15.741 |
| 101 | 18 | 0 | 0.837 (0.805–0.864) | 0.830 (0.785–0.870) | 8.64 (8.08–9.15) | 0.164 | 0.472 | 0.834 | 0.729 | 15.741 |
| 101 | 18 | 1 | 0.840 (0.810–0.866) | 0.832 (0.788–0.868) | 8.64 (8.09–9.24) | 0.163 | 0.446 | 0.828 | 0.747 | 14.259 |
| 101 | 18 | 2 | 0.900 (0.875–0.921) | 0.878 (0.842–0.911) | 5.50 (5.19–5.82) | 0.124 | 0.425 | 0.918 | 0.785 | 12.778 |
| 101 | 18 | 3 | 0.904 (0.883–0.925) | 0.888 (0.852–0.918) | 5.50 (5.21–5.85) | 0.123 | 0.414 | 0.920 | 0.783 | 12.963 |
| 103 | 10 | 0 | 0.833 (0.801–0.862) | 0.818 (0.767–0.858) | 5.59 (5.28–5.92) | 0.164 | 0.359 | 0.905 | 0.692 | 20.370 |
| 103 | 10 | 1 | 0.833 (0.802–0.861) | 0.818 (0.771–0.858) | 5.59 (5.26–5.90) | 0.164 | 0.359 | 0.905 | 0.692 | 20.370 |
| 103 | 10 | 2 | 0.833 (0.799–0.863) | 0.818 (0.770–0.857) | 5.59 (5.28–5.92) | 0.164 | 0.359 | 0.905 | 0.692 | 20.370 |
| 103 | 10 | 3 | 0.833 (0.800–0.864) | 0.818 (0.774–0.859) | 5.59 (5.27–5.90) | 0.164 | 0.359 | 0.905 | 0.692 | 20.370 |
| 103 | 14 | 0 | 0.833 (0.800–0.861) | 0.818 (0.774–0.857) | 6.33 (5.99–6.69) | 0.164 | 0.359 | 0.905 | 0.692 | 20.370 |
| 103 | 14 | 1 | 0.833 (0.801–0.862) | 0.818 (0.770–0.858) | 6.33 (5.96–6.70) | 0.164 | 0.359 | 0.905 | 0.692 | 20.370 |
| 103 | 14 | 2 | 0.852 (0.822–0.878) | 0.830 (0.788–0.870) | 6.33 (5.98–6.66) | 0.156 | 0.394 | 0.856 | 0.748 | 14.630 |
| 103 | 14 | 3 | 0.850 (0.820–0.877) | 0.829 (0.785–0.868) | 6.33 (5.96–6.72) | 0.157 | 0.412 | 0.846 | 0.758 | 13.704 |
| 103 | 18 | 0 | 0.833 (0.802–0.863) | 0.818 (0.773–0.856) | 8.50 (7.91–9.13) | 0.164 | 0.359 | 0.905 | 0.692 | 20.370 |
| 103 | 18 | 1 | 0.833 (0.800–0.862) | 0.818 (0.770–0.859) | 8.50 (7.87–9.10) | 0.164 | 0.359 | 0.905 | 0.692 | 20.370 |
| 103 | 18 | 2 | 0.907 (0.883–0.926) | 0.874 (0.835–0.908) | 5.16 (4.85–5.46) | 0.118 | 0.395 | 0.912 | 0.797 | 11.759 |
| 103 | 18 | 3 | 0.906 (0.882–0.927) | 0.875 (0.837–0.910) | 5.16 (4.88–5.45) | 0.118 | 0.461 | 0.879 | 0.808 | 10.556 |

All three fresh generator seeds are shown. Models are fitted on train patients, Platt-calibrated and threshold-selected on validation patients, then evaluated once on held-out patients. Sensor tiers fall back to the calendar model when their validation Brier gain is not distinguishable from zero by a patient-cluster bootstrap interval; `results.json` records the selected feature tier for each seed/day/tier.
<!-- RESULTS:END -->

![Patient-cluster bootstrap AUROC intervals by sensor tier and forecast day](assets/auroc_by_tier.svg)

![Mean false alerts per 100 patient-cycles by sensor tier and forecast day](assets/false_alerts_by_tier.svg)

![Day-14 lead-time versus false-alert trade-off by tier](assets/lead_time_false_alarm_tradeoff.svg)

## Dashboard screenshots

![Synthetic patient list](docs/screenshots/patient-list.png)

![Patient timeline](docs/screenshots/patient-timeline.png)

![Abstention banner](docs/screenshots/abstain-banner.png)

![Illustrative what-if panel](docs/screenshots/what-if-panel.png)

![Synthetic alert log](docs/screenshots/alert-log.png)

Demo video: [20-minute recording script](docs/video_script_20min.md) and [three-minute recording script](docs/video_script_3min.md) are prepared. The actual recording remains outstanding and must be made by the human presenter; the brief asks for a minimum 20-minute video.

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

Stack: Python, NumPy, scikit-learn, Streamlit, and the Python standard library. Code is released under the MIT License.
