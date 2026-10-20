# CycleTwin — three-minute recording script

Human recording required. This short version supplements the 20-minute script; it does not satisfy a brief requiring a minimum 20-minute recording. Use the live synthetic dashboard and the current README. Timings include clicks and brief display holds.

## 00:00–00:25 — Problem

**Screen:** README introduction.

**Say:** “I am Kushagra Gupta from VIT. CycleTwin explores prospective forecasting during a simulated menstrual cycle. Its target is no generated ovulation or generated ovulation after day 21, evaluated at days 10, 14 and 18. Every record is synthetic. This is a research prototype, not for diagnosis, contraception or conception planning.”

## 00:25–01:00 — Generator, fitted models and results

**Screen:** README results table.

**Say:** “Three seeds generate 1,200 patients with six cycles each. Patients are split 70/15/15 into train, validation and test. Logistic regression uses training patients; calibration, tier fallback and alert thresholds use validation patients.

“Tier 0 uses previous logged cycle lengths, Tier 1 adds wearables, and Tier 2 adds temperature. At day 14, their mean AUROCs are 0.838, 0.838 and 0.850, with Brier scores 0.163, 0.163 and 0.157. Day-18 Tier 2 reaches 0.906 and 0.119. These are simulator checks with patient-cluster intervals. EHR-lite is an additional oracle-adjacent tier.”

## 01:00–01:35 — Cohort and patient view

**Screen:** Cohort list → Patient view → Tier 2, s223-p0000.

**Say:** “The cohort list shows completeness bars and explicit status badges. Patient view shows missing temperature nights, logged-period markers, a predicted interval and a varying twin trajectory. The dashboard score is a fixed heuristic; its model card reports a separate fitted benchmark.

“Select s223-p0026 to see the abstain rule and withheld score. Conformal ranges are illustrative, with marginal coverage only. Chart summaries are deterministic calculations from the displayed arrays.”

## 01:35–02:05 — CGM and what-ifs

**Screen:** Return to s223-p0000; show CGM → what-if caveat → Show illustrative range.

**Say:** “The CGM panel shows simulated glucose, a 140 mg/dL reference and counts of simulated meal windows with excursions. It is not an evaluated glucose forecast.

“The what-if panel applies fixed assumption-based multipliers. Its ranges are not clinical intervention effects or treatment recommendations. The simplified reproductive and metabolic twin shares a generated latent and is not used in the fitted benchmark.”

## 02:05–02:30 — Alert log and methodology

**Screen:** Tier 0, s223-p0002 → Add selected synthetic alert to log → Model & methodology.

**Say:** “This eligible synthetic record demonstrates a one-alert-per-cycle log. The dashboard uses a fixed cutoff; benchmark thresholds are selected on validation patients. Model & methodology shows seed-level AUROC, Brier, intervals and sample counts. A clean requirements-only install passed all 13 tests and reproduced every saved benchmark result exactly.”

## 02:30–03:00 — Limitations and close

**Screen:** README scope, evaluation deviations, then public repository.

**Say:** “There is no real clinical cohort, external validation or calibrated patient twin. Early wearables often fall back to calendar history, the EHR tier contains simulator internals, and conformal, abstention and CGM claims remain limited. The Apple XML adapter is a synthetic parsing demonstration. No LLM is in the runtime explanation path. The public repository contains the code, assumptions, tests and results for review.”

