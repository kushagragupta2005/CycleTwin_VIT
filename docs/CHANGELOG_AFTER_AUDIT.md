# Changes after the implementation audit

All performance claims below refer to synthetic data. The immutable pre-change classification fixture is `tests/fixtures/classification_before_audit.json`.

## A1 — persisted fitted models and reproducible inference

- Before: fitted estimators were discarded; the dashboard had no persisted-model inference API.
- After: the evaluator writes each selected pipeline, preprocessing state, calibrated coefficients, validation threshold, source hashes, held-out metrics and held-out prediction rows. `src/inference.py` uses the same feature transformations and exposes exact additive base/calibrated logit contributions.
- Why: inference must be inspectable and reproduce the benchmark. No classifier, threshold-selection, calibration, label or generator change is intended. Classification values are guarded to absolute tolerance 1e-12; ovulation-day estimation is unchanged in this item.
- Model provenance records the Git parent present during training plus hashes of the actual training sources; it does not pretend that a file can contain its own eventual commit hash.
- Verification: unit suite includes persisted-versus-independent-refit checks, a classification regression fixture, and AppTest navigation/guided-step renders. Outcome: all 18 unit/AppTest tests passed; results.json remained byte-identical. Evidence: docs/gate_checks/A1.json and A1_tests.txt.

## A2 — connect the dashboard to the persisted classifier

- Before: patient/cohort/alert paths used hand-set sigmoid formulas and a universal demo cutoff; model cards described unrelated fitted results.
- After: those paths call src/inference.py with the predeclared seed-97 pipeline and its own validation threshold. Cards show that model's metrics, retained feature tier and a calendar-fallback badge. Exact fitted contributions replace raw-value ranking. EHR-lite is available with the oracle-adjacent label.
- Why: every live score must match the model whose evidence is shown. Classification results are unchanged. Conformal displays remain explicitly illustrative pending their dedicated evaluation item.
- Verification: all 19 unit/AppTest tests passed, including dashboard/API equality and persisted-model/independent-refit equality at 1e-12.

## A3 — correct day estimates and enforce withholding

- Before: calendar day estimates lacked completed history, UI always used temperature-tier timing, safety defaults were permissive, withheld scores leaked in other panels, uploaded XML used a shared retained path, and the CGM chart label described underlying rather than plotted sampling.
- After: shared completed history reaches the evaluator and inference; day estimates use the retained feature tier; calibration illustrations match the fitted tier/snapshot and use independent second-cycle records. Missing/invalid safety inputs abstain, including missing alert eligibility. An abstaining view exposes no personal probability, interval, feature explanation, sandbox output or alert. Actual generated ages replace the arbitrary safety-age override.
- Uploaded XML uses a unique temporary file deleted on success or failure. CGM labels use the computed plotting interval, temperature lines break at missing nights, and the period marker is explicitly assumed. Fixed score multipliers are removed; the assumption sandbox edits invented historical input and reruns fitted inference without claiming an intervention effect.
- Intentional numerical change: only ovulation-day MAE/interval endpoints change in results.json. The complete before/after seed-mean MAE table is generated in docs/gate_checks/A3_metric_changes.json. The retained feature tier also determines the separate day heuristic. All classification values remain within 1e-12 of the audit fixture.
- Verification: all 24 unit/AppTest tests passed, including complete UI withholding, correct Tier-0 calendar timing, fail-closed gates and temporary-file cleanup.
