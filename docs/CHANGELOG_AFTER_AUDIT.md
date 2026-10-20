# Changes after the implementation audit

All performance claims below refer to synthetic data. The immutable pre-change classification fixture is `tests/fixtures/classification_before_audit.json`.

## A1 — persisted fitted models and reproducible inference

- Before: fitted estimators were discarded; the dashboard had no persisted-model inference API.
- After: the evaluator writes each selected pipeline, preprocessing state, calibrated coefficients, validation threshold, source hashes, held-out metrics and held-out prediction rows. `src/inference.py` uses the same feature transformations and exposes exact additive base/calibrated logit contributions.
- Why: inference must be inspectable and reproduce the benchmark. No classifier, threshold-selection, calibration, label or generator change is intended. Classification values are guarded to absolute tolerance 1e-12; ovulation-day estimation is unchanged in this item.
- Model provenance records the Git parent present during training plus hashes of the actual training sources; it does not pretend that a file can contain its own eventual commit hash.
- Verification: unit suite includes persisted-versus-independent-refit checks, a classification regression fixture, and AppTest navigation/guided-step renders. Outcome: all 18 unit/AppTest tests passed; results.json remained byte-identical. Evidence: docs/gate_checks/A1.json and A1_tests.txt.
