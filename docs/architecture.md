# Implemented architecture

Synthetic inputs and one persisted fitted prediction path

Synthetic static EHR-lite
Oracle-adjacent internals

Synthetic nightly data
Calendar and wearables

Shared feature builder
Training median and scaling

Persisted logistic model
Validation calibration and threshold

Fail-closed safety gate
Withhold personal outputs

Doctor / Kushi dashboard
Probability and exact contributions

Separate illustrative twin
No contribution to fitted score

Bayesian timing posterior
Evaluated separately; not used in score or alerts
Brier 0.098 vs logistic 0.117

One fitted prediction path serves benchmark, cohort, patient and Kushi views. EHR-lite is implemented and oracle-adjacent. XML parsing is separate and does not score imports. The reproductive/metabolic illustration does not affect fitted predictions. All project data is synthetic.
