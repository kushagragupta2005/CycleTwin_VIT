# CycleTwin_VIT

**CycleTwin: synthetic cycle forecasting demo**  
Solo participant: Kushagra Gupta, full-time student, VIT.

> Decision-support research prototype only. Not for diagnosis, contraception or conception planning.

CycleTwin explores prospective per-cycle forecasting of simulated oligo-anovulation, with an ovulation-day estimate and an explicit alert budget. It is not retrospective ovulation confirmation or case/control identification.

## Design thesis and implemented scope

The design thesis is: prospective per-cycle forecasting with an ovulation-day interval, abstention and a one-alert budget; one twin with reproductive and metabolic axes connected through a shared insulin-resistance latent, including reverse luteal-to-glucose coupling; sensor tiers from period logs through wearables, nightly temperature, CGM and EHR; and an Apple Health-native input contract. These are design directions, not claims of novelty. This build implements synthetic period and wearable tiers plus a small Apple Health XML parser. It does not implement a coupled twin, CGM/EHR tiers, conformal intervals, abstention or a one-alert-per-cycle history policy. Alert metrics are reported at a fixed illustrative cutoff. Tier 0 has only a neutral score because prior-cycle history is not wired into the evaluator; tier 1 currently uses resting-heart-rate offsets only; tier 2 adds nightly temperature.

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

A stochastic generator creates synthetic patients and noisy cycle observations. A fixed score provides a prospective risk estimate; a temperature coverline heuristic estimates ovulation day, with a fixed fallback when no rise is visible. This is not an EKF or a clinical hormone model. The current build has no glucose axis, conformal intervals, abstention logic, or real-world validation. Those features are not evaluated. See [assumptions](docs/assumptions.md) and the frozen [evaluation plan](docs/eval_plan.md).

## Results

<!-- RESULTS:START -->

| Forecast day | Tier | AUROC (95% patient-cluster CI) | AUPRC (95% patient-cluster CI) | Ovulation-day MAE | Brier | False alerts/100 cycles |
|---|---:|---:|---:|---:|---:|---:|
| 10 | 0 | 0.500 (0.500–0.500) | 0.469 (0.431–0.600) | 5.90 (5.51–6.30) | 0.253 | 0.000 |
| 10 | 1 | 0.494 (0.459–0.529) | 0.503 (0.438–0.572) | 5.90 (5.51–6.33) | 0.252 | 0.556 |
| 10 | 2 | 0.514 (0.478–0.547) | 0.519 (0.459–0.590) | 5.90 (5.53–6.33) | 0.311 | 0.000 |
| 14 | 0 | 0.500 (0.500–0.500) | 0.469 (0.426–0.600) | 6.69 (6.31–7.08) | 0.253 | 0.000 |
| 14 | 1 | 0.477 (0.443–0.510) | 0.493 (0.430–0.558) | 6.69 (6.29–7.09) | 0.252 | 0.093 |
| 14 | 2 | 0.637 (0.603–0.671) | 0.598 (0.532–0.659) | 6.69 (6.29–7.08) | 0.306 | 0.000 |
| 18 | 0 | 0.500 (0.500–0.500) | 0.469 (0.425–0.594) | 8.68 (8.06–9.27) | 0.253 | 0.000 |
| 18 | 1 | 0.415 (0.381–0.449) | 0.445 (0.379–0.517) | 8.68 (8.09–9.27) | 0.254 | 0.185 |
| 18 | 2 | 0.815 (0.784–0.846) | 0.738 (0.684–0.796) | 5.27 (4.95–5.60) | 0.296 | 0.000 |

Values shown for seed 97; all three seeds and patient-cluster intervals are in `results.json`. Lead time and sensitivity at the alert cutoff are also in `results.json`.
<!-- RESULTS:END -->

## Data and privacy

Synthetic data only. The Apple Health adapter is a schema-compatibility smoke test, n=1 synthetic export, and clinically validates nothing. A personal export must be a consenting adult's own file, processed locally, never committed, and never used for training, tuning, or thresholds. The demo processes locally and stores only nightly aggregates. See [privacy notes](docs/privacy.md).

## Architecture and reporting

See [architecture](docs/architecture.md), [related work](docs/related_work.md), and [TRIPOD+AI notes](docs/tripod_ai.md).

## Pitch artifacts

- [Architecture diagram (PPTX)](deliverables/CycleTwin_VIT_architecture.pptx) · [PDF](deliverables/CycleTwin_VIT_architecture.pdf)
- [Pitch deck (PPTX)](deliverables/CycleTwin_VIT_pitch_deck_v3.pptx) · [PDF](deliverables/CycleTwin_VIT_pitch_deck_v3.pdf)
- [Jury Q&A](docs/jury_qa.md)

AI coding assistants helped build this project. All generated metrics describe synthetic data only.
