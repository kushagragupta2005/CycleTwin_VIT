# TRIPOD+AI reporting notes

Adapted for a synthetic engineering prototype; not a clinical prediction study.

- Title/abstract: identifies synthetic forecasting prototype.
- Data source: fully synthetic generator; no real cohort.
- Participants: synthetic patients; patient-level split documented in `docs/eval_plan.md`.
- Outcome: simulated anovulation or ovulation after day 21.
- Predictors: synthetic period logs and wearable summaries.
- Missing data: simulator-generated; current baseline uses available feature defaults. Dashboard wear completeness is shown for generated records.
- Model: simple fixed score, no fitted clinical model.
- Validation: internal patient-held-out simulation only, with three generator seeds and patient-cluster intervals.
- Performance: generated in `results.json`; do not interpret as clinical performance.
- Fairness: no clinical subgroup fairness conclusions; any dashboard diagnostic is simulator-specific.
- Open science: source, settings, assumptions and synthetic generator are included.
- Limitations: labels and observations arise from a simplified simulator; dashboard abstention and conformal helpers have no reported coverage evaluation; no external or prospective validation.
