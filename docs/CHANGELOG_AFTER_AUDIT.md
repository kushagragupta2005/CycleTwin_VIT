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

## A4 — Meet Kushi narrative and source-driven claims foundation

- Before: no persona narrative or clinician-oriented guided story existed.
- After: the top-level Meet Kushi tab has profile, two input streams, all evaluated snapshots, exact fitted evidence, a clinician research view, live safety toggles, all declared scenario outcomes and evidence links. Every view retains the fictional/synthetic/not-performance-evidence banner. Missing future robustness/frozen/Bayesian work is explicitly labelled pending.
- Selection: fixed seed 2107, PMOS_A, seventh cycle ground-truth day 30–38, median preceding-history length within the fictional 38–45 range, then lowest index. Later scenario seeds 2108/2109 are always shown without model-based selection. Age 21, BMI 27 and family-history 1 are declared fictional overrides. Actual six-cycle history is displayed unchanged, including the outlier outside the fictional usual range; later seeds are independent replays, not a coherent observed longitudinal patient.
- Sources: published India context is taken from the cited primary JAMA Network Open study and is separated from synthetic model performance. scripts/build_claims.py now builds docs/claims.json from evaluation/model/persona/source artifacts.
- Classification metrics are unchanged. All 26 unit/AppTest tests passed, including every chapter, later scenarios, no-prediction persona selection and all safety toggles.

## A5 — regenerate deliverables from generated claims

- Before: stale pitch/architecture files contained obsolete fixed-score metrics and missing-EHR claims; README and scripts mixed historical and current numerical descriptions.
- After: scripts/build_claims.py generates all published benchmark/context/persona claims and authored deliverable text. README, video scripts, architecture PDF/PPTX and pitch PDF/PPTX come from that object. The application reads generated model metadata/metrics from the same claims file; interactive probabilities and raw-array descriptions are computed from the current synthetic record, never hand-entered. Overview uses a predeclared sensor tier rather than selecting a model by test Brier.
- The new editable architecture shows implemented EHR-lite and one persisted classifier path, with the illustrative twin separate. Current presentation files replace stale versions in deliverables; Git and the historical audit retain earlier evidence. Old seeds are explicitly development evidence.
- CI rebuilds claims and checks exact README/script text, every expected PPTX/PDF slide text and metric token, plus rejection of unknown/stale metric strings and unexpected old deliverable files. PDF verification is a separately pinned development dependency.
- Classification metrics are unchanged. All 29 unit/AppTest tests passed. Native package/layout checks passed, every native slide was visually inspected, and final PDF architecture/table/body pages were rendered and inspected. PDF text checks cover every page. No PowerPoint application compatibility test is claimed.

## A6 — official-rule compliance and human recording handoff

- Checked the official challenge page and mapped phase-one rules to actual files and public reachability in SUBMISSION_CHECKLIST.md. The repository root already matches the user-supplied CycleTwin_VIT team/college naming. Anonymous HTTP checks returned 200 for README, licence, model card and every final PDF/PPTX.
- Generated a minute-by-minute recording runbook from claims, using Kushi as the narrative spine and reserving the final limitation segment. Existing short/long scripts and the new runbook are source-checked by CI.
- All technical checklist items pass. Human-only items remain explicit: the user deferred video recording/upload/link; eligibility/registered roster confirmation and the leader's private contact fields/final Unstop submission require the human. No recording, upload, registration verification or platform submission is claimed.
- All 31 unit/AppTest tests passed. A5's published CI passed; its receipt is saved. Classification metrics are unchanged.
