# CycleTwin_VIT

**CycleTwin: synthetic cycle forecasting demo**  
Solo participant: Kushagra Gupta, full-time student, VIT.

> Decision-support research prototype only. Not for diagnosis, contraception or conception planning.

CycleTwin explores prospective per-cycle forecasting of simulated oligo-anovulation, with an ovulation-day estimate and an explicit alert budget. It is not retrospective ovulation confirmation or case/control identification. The design thesis is one twin with reproductive and metabolic axes, connected through a shared insulin-resistance latent; that coupling is an assumption. The input contract is compatible with a small set of Apple Health export fields.

This repository uses synthetic data only. It contains no personal exports or clinical dataset. Metrics are internal checks against a simulator and do not establish clinical validity.

## Run

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make all
make demo-apple
```

`make all` generates synthetic patients, runs the prespecified patient-held-out evaluation, and writes `results.json`. `make demo-apple` writes a synthetic Apple Health-shaped XML export, parses it locally, and displays a small Streamlit dashboard.

## Model and scope

A stochastic generator creates synthetic patients and noisy cycle observations. A simple temperature/period-log score provides a prospective risk estimate; a deliberately simplified cycle twin estimates an ovulation window. The current build has no clinical hormone model, no glucose axis, no conformal intervals, no abstention logic, and no real-world validation. Those features are not evaluated. See [assumptions](docs/assumptions.md) and the frozen [evaluation plan](docs/eval_plan.md).

## Results

<!-- RESULTS:START -->
Run `make all` to generate the synthetic-only results table from `results.json`.
<!-- RESULTS:END -->

## Data and privacy

Synthetic data only. The Apple Health adapter is a schema-compatibility smoke test, n=1 synthetic export, and clinically validates nothing. A personal export must be a consenting adult's own file, processed locally, never committed, and never used for training, tuning, or thresholds. The project is local-first and stores only nightly aggregates in its demo. See [privacy notes](docs/privacy.md).

## Architecture and reporting

See [architecture](docs/architecture.md), [related work](docs/related_work.md), and [TRIPOD+AI notes](docs/tripod_ai.md). Architecture diagram and pitch deck are planned as G5 artifacts.

AI coding assistants helped build this project. All generated metrics describe synthetic data only.
