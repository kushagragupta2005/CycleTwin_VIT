# CycleTwin — 20-minute recording script

Prepared against the repository on 20 October 2026. This is a script, not a recording. The human presenter must record and check the final video; the brief requires at least 20 minutes. The schedule below totals 20:00, including the on-screen actions and reading holds. Rehearse at a calm pace and retain the holds rather than shortening the recording below the requirement.

## Before recording

- Open the public repository, README results table, results.json, docs/eval_plan.md, docs/assumptions.md, data/ehr.csv and the running Streamlit dashboard.
- From the repository folder, activate the installed environment and run streamlit run app.py. Allow the cohort to finish loading. The demo is deterministic.
- Prepare the sidebar selectors: Tier 2 and patient s223-p0000 for the timeline/CGM; s223-p0026 for abstention; Tier 0 and s223-p0002 for a visible synthetic alert.
- Keep each selected patient ID visible when discussing their chart. Allow each Streamlit interaction to finish before narrating the result.
- The dashboard uses fixed synthetic heuristics. The README and Model & methodology page report the separately fitted benchmark. Never present the dashboard score as the fitted benchmark prediction.
- The three-seed means below are rounded summaries of results.json, not pooled estimates. Use the README for individual seed confidence intervals.

| Forecast day | Tier 0 AUROC / Brier | Tier 1 AUROC / Brier | Tier 2 AUROC / Brier |
|---|---|---|---|
| 10 | 0.838 / 0.163 | 0.838 / 0.163 | 0.838 / 0.163 |
| 14 | 0.838 / 0.163 | 0.838 / 0.163 | 0.850 / 0.157 |
| 18 | 0.838 / 0.163 | 0.839 / 0.163 | 0.906 / 0.119 |

## 00:00–01:15 — Problem framing

**Screen:** README introduction. Spend the final 15 seconds pointing to the target and the research disclaimer.

**Say:** “I am Kushagra Gupta from VIT, and this is CycleTwin, a synthetic cycle-forecasting research prototype. The engineering problem is to make a prospective forecast during an ongoing cycle, show uncertainty and missing data, and limit how often the interface raises an alert.

“The target in this project is deliberately explicit: a simulated cycle receives an E1 label when ovulation is absent or its generated day is later than cycle day 21. We evaluate forecasts at cycle days 10, 14 and 18. Those are simulator settings, not clinical definitions or diagnostic thresholds.

“The prototype is decision-support research. It is not for diagnosis, contraception or conception planning. Every patient shown in this recording is generated. I will demonstrate the working software, the measured benchmark, and the boundaries between them.”

## 01:15–02:30 — What is built today

**Screen:** README “Design thesis and implemented scope”; briefly show the architecture diagram. Hold the diagram for 15 seconds.

**Say:** “The working implementation has three connected demonstrations. First, a reproducible generator supplies cycle histories and simulated sensor observations. Second, a fitted benchmark trains and evaluates tiered logistic-regression models with patient-level separation. Third, a Streamlit interface shows a small synthetic cohort, timelines, abstention rules, illustrative uncertainty ranges, a simplified coupled twin, and an alert log.

“There is also a local Apple Health XML adapter, an EHR-lite simulator check, and architecture and pitch artifacts in both PDF and PowerPoint formats. The XML adapter demonstrates parsing compatibility; the scored dashboard cohort still comes from the generator.

“The simplified twin is a separate demonstration. Its state is not a feature in the reported fitted benchmark. Likewise, the displayed what-if ranges are assumption-based illustrations. I will keep those distinctions visible while moving through the application.”

## 02:30–04:00 — Generator and data

**Screen:** src/generator.py and docs/assumptions.md. Point to the nine archetypes, missing-temperature mechanism and event label; pause 15 seconds for the assumptions.

**Say:** “For each evaluation seed, the generator creates 1,200 synthetic patients with six cycles each. There are three evaluation seeds: 97, 101 and 103. That gives 21,600 generated cycles across all seeds.

“The generator assigns nine archetypes at equal frequency, including regular and variable cycles, PMOS archetypes, and several safety-related scenarios. This equal mixture is not an estimate of disease prevalence. Generated ovulation timing depends on the archetype, a shared insulin-resistance latent and simulated stress. Some cycles are generated without ovulation.

“The observations include logged cycle lengths, resting heart-rate offsets, HRV offsets, steps, sleep and nightly temperature. Temperature receives noise, a small random walk, a generated post-ovulation shift and missing nights. Logged starts also contain timing noise.

“The parameters are documented assumptions. A model can recover a pattern created by these assumptions without being useful on a real cohort. That is why the results are described as internal simulator checks throughout the project.”

## 04:00–05:30 — Splits, fitting and validation

**Screen:** docs/eval_plan.md, src/features.py and src/fitted.py. Leave the split paragraph visible for 15 seconds.

**Say:** “Patients, rather than individual cycles, are assigned to train, validation and test partitions. Each seed has 840 training patients, 180 validation patients and 180 test patients. The test partition therefore contains 1,080 cycles per seed, or 3,240 held-out cycles across the three seeds.

“Keeping all cycles from a patient together prevents the same person's shared simulator characteristics from appearing in both training and test sets. Calendar features use preceding logged cycle lengths only. The first cycle has no prior length and is handled by the model's imputer.

“Logistic regression is fitted on training patients. Platt calibration and the F1 alert threshold use validation patients. A richer tier is retained only when the patient-cluster validation bootstrap interval for its Brier gain over the calendar model is above zero; otherwise the calendar model is used.

“The same validation set supports calibration, tier selection and threshold selection, which is a limitation to remember. Test outcomes do not choose the threshold. The published confidence intervals use patient-cluster bootstrap resampling.”

## 05:30–07:30 — Fitted Tier 0, Tier 1 and Tier 2 results

**Screen:** README results table and AUROC figure. Read individual seed rows alongside the means above. Reserve 25 seconds for the table.

**Say:** “Tier 0 is a fitted calendar model. Its input is the mean of up to the previous three logged cycle lengths. Tier 1 adds resting heart rate, HRV, steps and sleep. Tier 2 adds a temperature-change feature and observed-temperature completeness.

“At day 14, the mean AUROC across the three seeds is 0.838 for Tier 0 and 0.838 for Tier 1. Both have mean Brier score 0.163. Tier 2 has mean AUROC 0.850 and mean Brier 0.157. AUROC describes ranking; a lower Brier score means lower squared error for the probability predictions. Neither number establishes clinical validity.

“At day 18, Tier 2 reaches mean AUROC 0.906 and mean Brier 0.119. Tier 0 remains 0.838 and 0.163, while Tier 1 is 0.839 and 0.163. More of the generator's temperature pattern is observable later in the cycle.

“At day 10, all three reported tiers have the same mean results because the validation procedure selected the calendar fallback. The day-14 Tier 2 candidate is retained for seeds 97 and 103 but falls back for seed 101. Identical rows therefore reflect an explicit selection rule.

“Across all 36 saved seed, day and tier combinations, the lowest AUROC is approximately 0.833. Every saved Brier score is below the corresponding best constant-at-test-prevalence reference. The README also reports sensitivity, PPV, false alerts and ovulation-day error, with seed-level uncertainty. Those secondary measures should be read alongside the thresholds and sample counts.”

## 07:30–08:30 — EHR-lite and the meaning of “static”

**Screen:** data/ehr.csv and the EHR-lite disclosure in docs/assumptions.md. Hold the disclosure for 15 seconds.

**Say:** “The static EHR-lite export has one record per generated patient: 3,600 records across the three evaluation seeds. It exposes the archetype, simulator insulin-resistance latent, androgen load, age, BMI and family-history draw. The fitted Tier 3 candidate adds the five numerical fields to the sensor features.

“The latent and androgen load also influence the generator's labels. Tier 3 is therefore labelled oracle-adjacent and a simulator-internal check. These results are not evidence of real EHR fusion, and the CSV does not contain patient medical records.

“The current dashboard display selector contains Tiers 0, 1 and 2. The EHR-lite candidate belongs to the evaluation harness and results table. This distinction is useful when comparing the interface with the full experimental output.”

## 08:30–09:30 — Reproduction and dependency integrity

**Screen:** requirements.txt, README run instructions and the saved test output. Do not run the full evaluation during the recording; allow 15 seconds to inspect the pinned versions.

**Say:** “The dependencies are now pinned to the versions in the evaluation environment, including scikit-learn 1.6.1, NumPy 2.0.2 and SciPy 1.13.1. Altair is listed explicitly because the dashboard imports it directly.

“A fresh environment installed only from requirements passed both fitted-pipeline tests and all 13 unit tests. A complete rerun then reproduced every field of the committed results JSON exactly. That checks reproducibility within this software environment; it is not external validation.

“After activating the environment, make all runs the generator export, evaluation, README-table update and figure generation. Make demo-apple creates a synthetic XML fixture and starts the dashboard. The repository is public so a reviewer can inspect both the implementation and its stated assumptions.”

## 09:30–10:45 — Cohort list

**Screen:** Dashboard → Cohort list, Tier 2. Change the sort order once. Scroll to the risk–coverage diagnostic and pause for 15 seconds.

**Say:** “This is the display cohort: 36 generated patients, each shown with their second cycle so that previous-cycle history is available. The sidebar separates navigation, data input, display settings and the demo information.

“The list includes the synthetic archetype, fixed demo score, selected tier, an inline completeness bar and a status badge. A neutral not-flagged badge is not reassurance about a real patient's health. Amber clinician-review badges correspond to explicit abstention rules.

“The caption beside the scores distinguishes the fixed heuristic from the separately fitted benchmark's AUROC and Brier score. Sorting changes the presentation of this synthetic cohort.

“The risk–coverage diagnostic is calculated on these display records. It is not part of the held-out benchmark. Its short summary reports the numerical ranges in the plotted arrays. It is generated with a deterministic template, with no language-model call.”

## 10:45–12:15 — Patient view and temperature

**Screen:** Dashboard → Patient view; select s223-p0000, Tier 2. Point to the ID, temperature chart, missing markers, interval and model-card caption. Leave the chart visible for 20 seconds.

**Say:** “The patient identifier at the top confirms which synthetic record is selected. The temperature trace shows generated offsets, a predicted ovulation interval, a logged-period-start marker and explicit missing-night markers. The caption states that missing values are not interpolated.

“Under the chart, the summary compares the mean observed offset on days 1–5 with days 21–28 and counts missing nights. Those values come directly from this displayed array. The sentence describes a numerical change and does not attach clinical meaning to it.

“The synthetic ovulation-day estimate is a temperature coverline heuristic with a fallback. It can disagree with the generated event and should not be described as confirmed ovulation.

“These 28-day timelines are retrospective views of generated records, while the evaluated forecast features are truncated at days 10, 14 or 18. The full displayed trace is not evidence that a day-14 predictor had access to later nights.

“Open the model card to see the separate fitted benchmark's seed-level results. The interface explicitly says those benchmark values do not calibrate the fixed demo score for this individual display record.”

## 12:15–13:30 — Abstention and conformal illustration

**Screen:** Select s223-p0026. Show the abstain banner, withheld score, rule text and conformal caption. Open the patient caveats. Pause for 15 seconds.

**Say:** “This generated early-menarche scenario triggers the dashboard's age or early-post-menarche rule. The banner identifies the reason and the risk panels withhold the displayed score. The safety flags in this screen are demo rules; they are not a validated clinical triage policy.

“The interval and label-set helpers illustrate split conformal calibration on a separate generated calibration cohort, seed 211. The caption describes marginal coverage only. It does not promise that this particular patient's true event is inside the interval.

“Conformal coverage, subgroup coverage and abstention performance are not reported as evaluated outcomes in the main benchmark. The dashboard can illustrate these mechanisms while the reporting remains explicit about what has and has not been measured.

“The glossary explains abstain, tier and conformal interval in plain language so a reviewer can follow the interface without having read the implementation.”

## 13:30–14:45 — Twin trajectory and CGM

**Screen:** Return to s223-p0000. Scroll between the follicle trajectory and CGM. Open the CGM caveat and hold for 15 seconds.

**Say:** “The twin panel plots a day-by-day simulated follicle state against cycle day, with a dashed threshold. The ovulation-day state printed above it is a scalar event produced by that simulation. It is separate from the line's trajectory and from the dashboard's coverline estimate.

“The reproductive and metabolic demonstrations share a synthetic insulin-resistance latent. The chart summary reports the trajectory's range and the day of its maximum. This twin is uncalibrated and does not affect the fitted benchmark metrics.

“For this patient, the dashboard also shows simulated glucose. The underlying stream has 15-minute samples; the plotted line is thinned to every eighth sample. The 140 mg/dL line and meal-window count describe the generated stream. The excursion metric uses the full data within 120 minutes after simulated meals. There is no evaluated CGM prediction result or clinical glycaemic-risk claim.”

## 14:45–15:45 — Illustrative what-ifs

**Screen:** What-if panel → open caveat → select Daily walk → Show illustrative range. Hold the resulting text for 15 seconds.

**Say:** “The what-if panel is visually separated from the risk panels. It offers labelled scenarios such as regular sleep, a daily walk, and a lower-GI food swap.

“When I press Show illustrative range, the software applies fixed assumption-based multipliers to the demo score. The displayed sentence explicitly says this is not a treatment recommendation. It is not a refitted causal model, a measured intervention effect or a rerun of a validated twin.

“This is a communication demonstration of how a future interface might expose scenarios. A real counterfactual feature would need an appropriate causal model, meaningful intervention definitions and separate evaluation. None of those clinical effects is established by these numbers.”

## 15:45–16:45 — One-alert log

**Screen:** Select Tier 0 and s223-p0002. Wait for the score to update, then press Add selected synthetic alert to log. Press again to show duplicate protection. Hold the log for 15 seconds.

**Say:** “For a visible alert example, I switch to Tier 0 and synthetic patient s223-p0002. This record's previous logged cycle length is 42 days, and its fixed calendar demo score is approximately 71 percent.

“The dashboard's alert rule uses a fixed 0.50 cutoff and permits at most one selected alert per patient-cycle across the displayed forecast days. The fitted benchmark uses validation-selected thresholds instead, as listed in the README.

“The first click adds the eligible synthetic alert. A second click does not add another entry for the same patient-cycle. This log lives in the Streamlit session; it is not a deployed notification system or a clinical record. The log caveat also states that explanations are templated and no LLM is in the loop.”

## 16:45–18:00 — Model & methodology page

**Screen:** Navigate to Model & methodology; show Tier 2, then Tier 0. Open the benchmark caveat and pause for 15 seconds.

**Say:** “This page gathers the fitted benchmark context in one place. It shows mean AUROC and Brier values for the selected tier at day 14, plus a table of seed-level AUROC, its patient-cluster confidence interval, Brier score and held-out cycle count.

“The method is generator, tiered feature extraction, fitted model, validation decisions and held-out evaluation. The scope statements distinguish this benchmark from the dashboard's heuristic and the separate simulator.

“Changing the display tier changes which benchmark rows the page summarizes. It does not train a model from uploaded data. The application has no clinical training workflow.

“The README includes the complete day-10, day-14 and day-18 table, PPV and false alerts. The evaluation plan records omissions including additional baselines, dropout sweeps and subgroup coverage. That documentation is necessary context for the selected headline numbers.”

## 18:00–20:00 — Limitations and close

**Screen:** README scope and docs/eval_plan.md reporting deviations. End on the public repository URL. Use the final 25 seconds to hold the scope statement and repository link; confirm the recording reaches at least 20 minutes.

**Say:** “The largest limitation is that every evaluated record and every displayed patient is synthetic. The generator's own rules influence both the features and labels, and its equal archetype mixture is not a real population. We have no external cohort, prospective clinical evaluation or clinician-validated operating threshold.

“Early wearable signals are weak in this generator, which is visible in the calendar fallbacks. The stronger late-cycle temperature result can reflect the signal that the generator itself inserts. A high simulator AUROC therefore does not establish medical usefulness.

“There are further limits in the current product demonstration. The twin is not calibrated and is not connected to the reported predictor. The what-if ranges use fixed multipliers. The conformal and abstention mechanisms are illustrative rather than validated benchmark endpoints. CGM is displayed but not evaluated as a forecasting task. The XML adapter is a synthetic compatibility check, and uploaded XML does not turn the demonstration into a clinical predictor.

“The EHR-lite tier includes simulator-internal parameters, so it remains explicitly oracle-adjacent. The benchmark's validation patients are used for several model decisions. More rigorous future work would need a prospectively specified target, permissioned data, clinician co-design, external validation and a revised evaluation plan before additional claims.

“What is reproducible today is the software experiment: pinned dependencies, fitted models with patient-level holdout, documented synthetic results, and a transparent interface with safety and scope labels. The repository also contains the source, tests, architecture and pitch artifacts.

“Thank you. CycleTwin is a research prototype for inspecting a forecasting workflow and its limits. The public repository contains the evidence needed to review what this version actually implements.”

