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
