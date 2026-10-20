# CycleTwin: complete implementation and evidence audit

Audited source commit: 76b4a8f8a69fa526e9825669fb600810af2b08f8. Audit date: 20 October 2026, IST. Production code, results and presentation files were inspected directly. The audit regenerated current datasets, refitted the selected benchmark pipelines, checked saved metrics and subgroup rates, extracted PDF/PPTX text, and ran unit and AppTest checks. Application/model/generator/evaluation code and the published results were not changed.

**Central finding:** CycleTwin is a reproducible synthetic research experiment plus an interactive demonstration. It predicts a generated late/absent-ovulation label; it does not diagnose PMOS, infer measured hormone concentrations, or provide a clinically validated forecast. The dashboard's patient scores are fixed heuristics, not the fitted models used in the published benchmark.

## Evidence files and numerical conventions

- [all_metrics.csv](all_metrics.csv): all 36 current seed/day/tier records, saved statistics and confidence bounds, plus explicitly named audit-derived confusion counts, accuracy, specificity and F1.
- [subgroup_false_alarm_rates.csv](subgroup_false_alarm_rates.csv): all 324 saved archetype false-positive rates, with exact negative-cycle denominators and false-positive numerators.
- [threshold_tradeoff_points.csv](threshold_tradeoff_points.csv): all 396 saved descriptive threshold-sweep points, with denominators.
- [dataset_statistics.json](dataset_statistics.json): counts, class balance, archetype composition and temperature missingness for every current main cohort and split; EHR and XML checks.
- [raw_input_ranges.json](raw_input_ranges.json) and [feature_ranges_and_missingness.csv](feature_ranges_and_missingness.csv): actual generated ranges and missingness; feature CSV contains each seed/day/split/feature combination.
- [audit_refitted_heldout_predictions.csv](audit_refitted_heldout_predictions.csv): 38,880 independently reconstructed prediction records. These are audit refits, not previously saved clinical predictions.
- [audit_refitted_parameters.json](audit_refitted_parameters.json): coefficients, intercepts, imputer medians and scaler values from the audit refits, clearly separate from nonexistent deployed model artifacts.
- [reproduction_checks.json](reproduction_checks.json): checks against 324 saved scalar values. All 36 configurations matched at absolute tolerance 1e-12.
- [dashboard_records.csv](dashboard_records.csv), [dashboard_statistics.json](dashboard_statistics.json), [illustrative_examples.json](illustrative_examples.json) and [ui_audit_checks.json](ui_audit_checks.json): exact display-cohort behavior and reproduced UI gaps.
- historical_*_results.json, [evaluation_history.json](evaluation_history.json), [presentation_text.json](presentation_text.json) and [pdf_text.json](pdf_text.json): historical results and extracted slide text, including stale claims.
- [environment_and_provenance.json](environment_and_provenance.json): audited commit, source hashes and actual installed versions.
- [unit_test_log.txt](unit_test_log.txt), [apptest_log.txt](apptest_log.txt) and [ci_log.txt](ci_log.txt): execution evidence. CI: https://github.com/kushagragupta2005/CycleTwin_VIT/actions/runs/39385249386.

CSV/JSON values retain full floating-point precision. Fractions carry exact integer denominators. Where a table below uses a mean across seeds, it is a descriptive arithmetic mean, not a pooled AUROC or a new confidence interval. Audit-derived metrics were not reported as separate endpoints in the original results.json.

## 1. Purpose, intended user and actual scope

The engineering question is: can a software pipeline flag a generated cycle that will have no ovulation, or generated ovulation after day 21, while showing uncertainty, missing data and explicit safety rules? It evaluates snapshots at cycle days 10, 14 and 18.

The intended future context is cycle monitoring and clinician decision-support research, potentially involving people already diagnosed with PMOS. The current evaluated population is a mixture of synthetic archetypes, not a cohort restricted to confirmed PMOS. Its actual users today are the developer, competition judges and researchers inspecting the experiment.

PMOS status is an assigned simulator archetype, not the model's prediction target. The model never outputs a PMOS diagnosis. Its positive label is not proof of PMOS; non-PMOS archetypes can be positive, and PMOS_C often has a negative cycle label.

There are no measured LH, FSH, estradiol, progesterone, testosterone or fasting insulin inputs. The glossary mentions HOMA-IR, but the code does not calculate HOMA-IR. The insulin-resistance latent and androgen load are generated internal variables, not hormone test results. Predicting synthetic labels without hormone measurements is possible because the generator creates the signal–label relationships. That does not establish clinical forecasting without hormones.

Evidence: [src/generator.py:5–46](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/generator.py:5>), [src/features.py:22–49](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/features.py:22>), [scripts/run_eval.py:15](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/scripts/run_eval.py:15>) and [app.py:251–282](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/app.py:251>).

For medical context only, ASRM describes basal-body-temperature patterns as an often unreliable indicator of ovarian function and discusses appropriately timed progesterone testing and urinary LH as separate tools. That does not validate CycleTwin or make a simulated wrist-temperature series equivalent to hormonal confirmation. [ASRM committee opinion](https://www.asrm.org/practice-guidance/practice-committee-documents/fertility-evaluation-of-infertile-women-a-committee-opinion-2021/).

## 2. Every input, its source and what it means

### Predictive inputs

No patient health field is manually entered in the current dashboard. The legacy forecast() function reads the temperature key before branching on tier, so even its calendar-only call currently requires that array to exist as an implementation dependency; the Tier 0 score does not use its values. The fitted Tier 0 feature builder has no such sensor dependency. These inputs are generated dictionaries. Tier choice determines which features the fitted benchmark uses. A higher tier is optional as an experimental configuration; the dictionary keys required by that tier are not optional at the API level. Missing numerical values can be imputed, but absent dictionary keys are not validated into a usable patient record.

| Raw field → fitted feature | Unit | Source and collection in this build | Required when | Role in this simulator |
|---|---|---|---|---|
| cycle_length → prior_logged_cycle_length | days | Generated completed-cycle lengths; average of up to three preceding cycles | All fitted tiers | Captures persistent archetype/latent differences across cycles. Current-cycle length is excluded from the feature value. |
| rhr → mean_rhr_offset | Synthetic offset units; not absolute bpm | Daily Gaussian draws, with a generated post-ovulation offset; average prefix up to forecast day | Fitted Tier 1+ | May reveal an inserted post-event pattern. |
| hrv → mean_hrv_offset | Synthetic offset units; not absolute milliseconds | Daily Gaussian draws and generated post-ovulation offset; prefix mean | Fitted Tier 1+ | Same engineering role as RHR; early signal is weak. |
| steps → mean_steps | Synthetic steps/day, floating-point values | Log-normal daily draws; prefix mean | Fitted Tier 1+ | A noise feature in this generator; steps do not cause its labels. |
| sleep → mean_sleep_hours | hours/night | Gaussian daily draws; prefix mean | Fitted Tier 1+ | Another largely uninformative early feature in this generator. |
| temperature → temperature_change | °C offset from an artificial baseline | Generated noise/random walk/post-ovulation shift; mean of last four observed values minus mean of up to five early observed values | Fitted Tier 2+ | Captures the signal explicitly inserted after generated ovulation. Requires at least six observed values; otherwise feature is NaN. |
| temperature → temperature_observation_fraction | fraction, 0–1 | Finite observed nights divided by forecast-day prefix length | Fitted Tier 2+ | Encodes missingness; it is not itself evidence of physiology. |
| ir → simulator_ir_latent | dimensionless | Clipped normal draw, not a lab result | Fitted Tier 3; also twins | An internal variable that helps generate labels; oracle-adjacent. |
| androgen → simulator_androgen_load | arbitrary simulator units | Normal draw; no assay or concentration unit | Fitted Tier 3; also reproductive twin | A generated correlate of assigned archetype; it enters the separate twin, but does not directly enter the generator's event/timing equation. The tier remains oracle-adjacent because it also includes IR. |
| age → synthetic_age | years | Uniform integer draw | Fitted Tier 3 | Included as a candidate covariate. It does not directly enter the event-generating timing equation. |
| bmi → synthetic_bmi | BMI-labelled units, conventionally kg/m² | Clipped normal draw correlated with positive IR latent; no height or weight is measured | Fitted Tier 3 | An indirect generated correlate of IR. |
| family_history → synthetic_family_history | binary 0/1 | Bernoulli draw with probability related to IR | Fitted Tier 3 | An indirect generated correlate, not a collected family history. |

These rows correspond to 12 engineered features; temperature supplies two features from one raw stream. Input dimensions are 1, 5, 7 and 12 for candidate Tiers 0, 1, 2 and 3.

| Raw field | Total values | Missing | Minimum | Maximum | Mean | Population SD |
| --- | --- | --- | --- | --- | --- | --- |
| temperature | 1188000 | 142749 | -0.1954542504592965 | 0.43193269303569515 | 0.10433527310108658 | 0.10793464121753181 |
| rhr | 1188000 | 0 | -4.906883251709055 | 4.717195951940833 | 0.18265927427422407 | 1.014581033152973 |
| hrv | 1188000 | 0 | -5.131530910098629 | 4.749302367833341 | -0.12938730141372073 | 1.0066972079072791 |
| steps | 1188000 | 0 | 1550.0419770025492 | 16219.371744409678 | 5070.051613208433 | 1288.6778044047844 |
| sleep | 1188000 | 0 | 3.4120313301735505 | 10.736776119601158 | 6.999767907020404 | 0.7494498139405467 |
| cycle_length | 21600 | 0 | 22.0 | 55.0 | 33.45902777777778 | 7.144843192118993 |
| ovulation_day | 21600 | 0 | -1.0 | 45.0 | 17.761111111111113 | 10.390476705755107 |
| ir | 21600 | 0 | -2.5 | 2.5 | -0.002140778695050577 | 1.000192506580722 |
| androgen | 21600 | 0 | -2.343515565726666 | 3.0671437895104643 | 0.29148087209686174 | 0.7693224482639771 |
| age | 21600 | 0 | 18.0 | 42.0 | 29.82138888888889 | 7.185791401856003 |
| bmi | 21600 | 0 | 17.0 | 42.0 | 26.268553498596184 | 4.262852423358255 |
| family_history | 21600 | 0 | 0.0 | 1.0 | 0.22083333333333333 | 0.4148083560178389 |

Static patient fields in this table are repeated across six cycles; their 21,600 entries are not 21,600 independent people. The ovulation-day mean includes the −1 absence sentinel and has no clinical interpretation.

These are observed ranges in the current benchmark, not safe clinical operating ranges. RHR/HRV and androgen normal distributions are theoretically unbounded. Sleep is also not clipped. IR is clipped to −2.5…2.5, age is 18…42, BMI is clipped to 17…42, and family history is binary.

### Other generator fields and hidden state

- patient, cycle and seed identify records and select splits; they are not classifier columns.
- phenotype selects one of nine generator archetypes. It sets timing/probability assumptions and dashboard safety examples. It is exported to EHR CSV but is not a fitted Tier 3 column.
- day0 is a shifted logged date; period_start is the artificial true date. These dates are not fitted features.
- ovulation_day is the generator's answer, with −1 representing absence; event is the binary training/evaluation label. Neither is a predictor column.
- stress is a temporary standard-normal draw used to generate timing for selected archetypes. It is not saved in the record, sensed, user-entered, or used as a model feature.
- Current-cycle cycle_length is a generated outcome-like value. It enters only the history of later cycle indices in the classifier feature builder. See the temporal-consistency limitation below.

Evidence: [src/generator.py:7–46](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/generator.py:7>) and [src/features.py:11–49](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/features.py:11>).

### Apple Health-shaped input: supported fields, units and processing

| XML field/type | Expected/generated unit | Reader operation | Connected to predictions? |
|---|---|---|---|
| AppleSleepingWristTemperature | degC; degF/°F converted to Celsius | Last recognized quantity for each start-date key | No |
| RestingHeartRate | count/min | Reads value as float; no general unit conversion | No |
| HeartRateVariabilitySDNN | ms | Reads value as float | No |
| StepCount | count | Reads value as float; repeated records overwrite rather than sum | No |
| SleepAnalysis Core/Deep/REM/Awake/Asleep | hours computed from startDate/endDate | Adds duration per stage to the record's start-date bucket | No |
| MenstrualFlow with MenstrualCycleStart metadata | category plus true/false metadata | Collects unique cycle-start dates | No |
| startDate/endDate, type, value, unit | timestamps/text/numerical values | Needed to parse supported record types; malformed values are not comprehensively handled | No |

The synthetic XML fixture converts generated offsets to artificial absolute values: temperature = 36.4 + offset °C; RHR = 62 + offset bpm; HRV = 48 + 4×offset ms. It supplies fixed nightly sleep stages: Core 3.4 h, Deep 1.1 h, REM 1.5 h and Awake 0.4 h. These sleep values are separate from the generator's random sleep predictor.

The parser does not provide a general daily aggregation/normalization pipeline suitable for the fitted model: quantities overwrite, temperature units are selectively converted, and overnight sleep is bucketed by each stage's start date. Its parsed dictionaries are used to show counts only. No feature builder or model consumes the upload.

read_generic_csv() supports date,temp,rhr,hrv,steps,period_start columns. Blank numerical cells become None, and period_start accepts 1/true/yes. There is no CSV upload widget or prediction connection. The reader uses temp, whereas the XML reader uses temperature; no canonical adapter-to-model bridge reconciles them.

Evidence: [src/adapters/apple_health.py:6–58](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/adapters/apple_health.py:6>); [scripts/make_synthetic_apple_export.py:9–38](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/scripts/make_synthetic_apple_export.py:9>); [app.py:186–199](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/app.py:186>).

### Safety inputs and UI controls

The guard accepts tsh_abnormal, prolactin_abnormal, hormonal_contraception, age, early_post_menarche, pregnant, postpartum, breastfeeding, perimenopausal and wear_completeness. These are flags/fractions, not hormone concentrations or diagnostic calculations. In the current UI they are generated/assigned, not entered by a person.

The UI assigns safety age 17 to early_menarche and 29 to all other archetypes, independently of the generated age used by EHR-lite. It sets thyroid/contraception/early-menarche flags from the known archetype. Prolactin, pregnancy, postpartum, breastfeeding and perimenopause are always false in displayed examples.

Human controls are navigation, tier, sort order, generated patient selection, scenario, mock-consent checkbox, XML upload and action buttons. None is a clinical questionnaire. The checkbox changes its receipt text; it does not gate access or file processing.

Evidence: [src/safety.py:3–15](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/safety.py:3>) and [app.py:201–235](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/app.py:201>).

## 3. Dataset inventory and exact denominators

All current research datasets are synthetic and generated by this repository. No clinical dataset, restricted cohort, actual hormone assay, personal wearable export or real EHR is used. Published studies in related_work.md are context, not training sources.

| Dataset (all synthetic) | People | Cycles | PMOS people | PMOS cycles | Positive cycles | Negative cycles | Absent | Ovulation >21 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Benchmark seed 97 | 1200 | 7200 | 533 | 3198 | 3745 | 3455 | 1104 | 2641 |
| Benchmark seed 101 | 1200 | 7200 | 533 | 3198 | 3634 | 3566 | 1085 | 2549 |
| Benchmark seed 103 | 1200 | 7200 | 533 | 3198 | 3643 | 3557 | 1091 | 2552 |
| Benchmark combined | 3600 | 21600 | 1599 | 9594 | 11022 | 10578 | 3280 | 7742 |
| Display seed 223 generated | 36 | 72 | 16 | 32 | 37 | 35 | 13 | 24 |
| Display seed 223 shown | 36 | 36 | 16 | 16 | 22 | 14 | 6 | 16 |
| Conformal seed 211 | 240 | 240 | 108 | 108 | 118 | 122 | 37 | 81 |

EHR-lite: data/ehr.csv, 3,600 derivative patient rows, eight columns, zero missing cells; no new participants. Apple fixture: apple_health_export/export.xml, seed 17, one generated healthy_regular participant/cycle, 281 XML records, 36 parsed date buckets; not a forecast dataset. The extra date comes from overnight sleep stages.

The EHR file is a derivative of the same 3,600 benchmark participants; do not add it as an independent cohort. The 36 visible dashboard records are second cycles selected from 72 generated display cycles. The 240-cycle conformal cohort has a separate seed. The Apple fixture is an additional single generated participant.

| Seed | Partition | People | Cycles | PMOS people/cycles | Positive | Negative | Absent | Late | Ovulatory (MAE denominator) | Temperature missing/total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 97 | train | 840 | 5040 | 371/2226 | 2624 | 2416 | 794 | 1830 | 4246 | 33493/277200 |
| 97 | validation | 180 | 1080 | 82/492 | 553 | 527 | 149 | 404 | 931 | 7196/59400 |
| 97 | test | 180 | 1080 | 80/480 | 568 | 512 | 161 | 407 | 919 | 7017/59400 |
| 101 | train | 840 | 5040 | 371/2226 | 2536 | 2504 | 771 | 1765 | 4269 | 33212/277200 |
| 101 | validation | 180 | 1080 | 82/492 | 550 | 530 | 151 | 399 | 929 | 7039/59400 |
| 101 | test | 180 | 1080 | 80/480 | 548 | 532 | 163 | 385 | 917 | 7069/59400 |
| 103 | train | 840 | 5040 | 371/2226 | 2544 | 2496 | 782 | 1762 | 4258 | 33379/277200 |
| 103 | validation | 180 | 1080 | 82/492 | 552 | 528 | 165 | 387 | 915 | 7230/59400 |
| 103 | test | 180 | 1080 | 80/480 | 547 | 533 | 144 | 403 | 936 | 7114/59400 |

Splits depend on patient index modulo 20: buckets 0–2 test, 3–5 validation, and 6–19 train. Every cycle of one ID stays together. The three seeds repeat this deterministic index pattern with different generated values; they are three runs of the same simulator, not external cohorts.

| Archetype | People | Cycles | Positive cycles | Negative cycles |
| --- | --- | --- | --- | --- |
| healthy_regular | 402 | 2412 | 146 | 2266 |
| healthy_variable | 402 | 2412 | 1786 | 626 |
| PMOS_A | 402 | 2412 | 2168 | 244 |
| PMOS_B | 399 | 2394 | 2137 | 257 |
| PMOS_C | 399 | 2394 | 170 | 2224 |
| PMOS_D | 399 | 2394 | 2139 | 255 |
| thyroid_mimic | 399 | 2394 | 2149 | 245 |
| contraception | 399 | 2394 | 166 | 2228 |
| early_menarche | 399 | 2394 | 161 | 2233 |

Within PMOS-labelled cycles: 6,614 positive and 2,980 negative of 9,594. Within non-PMOS-labelled cycles: 4,408 positive and 7,598 negative of 12,006. These categories are simulator assignments, not diagnosed populations.

“Equal archetype frequency” is only approximate because 1,200 is not divisible by nine. Per seed, healthy_regular, healthy_variable and PMOS_A have 134 participants each, while each other archetype has 133. Combined PMOS/non-PMOS participant counts are 1,599/2,001; corresponding cycle counts are 9,594/12,006.

### Missingness and preprocessing

There are 1,188,000 raw time points per stream across the benchmark: 21,600 cycles × 55 days. Temperature has 142,749 missing values and 1,045,251 observed values. RHR, HRV, steps and sleep have zero generated missing values. This is not a realistic simulation of missingness across every sensor.

The prior-cycle feature is unavailable for the initial cycle of every participant: 3,600 of 21,600 rows at each snapshot. Temperature-change features have 85 missing values at day 10 and none at days 14/18. These numerical NaNs are handled by training-set median imputation inside the fitted pipeline. The CSV supplies exact counts for every seed, day and split.

Raw series are summarized over the prefix available at the requested day. Missing temperatures are removed before calculating the change; no linear interpolation is performed in feature engineering. StandardScaler subtracts training means and divides by training standard deviations after imputation. No held-out values fit either transformation. A separate exact [seed-97 day-14 training-feature means by label table](seed97_training_day14_feature_means_by_label.json) confirms that early RHR/HRV/steps/sleep are weakly separated while prior-cycle length differs materially. These are descriptive training statistics, not additional held-out endpoints.

The EHR export contains 3,600 unique patient rows, eight columns and no blank cells. Every exported numeric value and archetype matches regeneration exactly. The evaluator does not actually read this CSV; it accesses the same generated fields directly.

The XML fixture contains 281 Record elements: 35 temperature, 35 RHR, 35 HRV, 35 step, 140 sleep and one menstrual-flow record. The parser returns 36 date buckets because sleep stages cross midnight, and one cycle-start date. Five quantity values are non-finite in this fixture; they originate from generated missing temperatures.

Tests create additional small synthetic fixtures, including seed 9 (four patients/two cycles), seed 61 (one patient/three cycles) and seed 5 (one patient/one cycle). Seeds 17, 29 and 43 are documented as development seeds. Historical evaluation outputs are retained in Git and exported in the audit folder; they are not independent current validation datasets.

### Exact generator rules: where the apparent signal comes from

For each patient, IR is Normal(0,1) clipped to [−2.5,2.5]; androgen is Normal(0.65,0.7 SD) for PMOS-labelled archetypes or Normal(0,0.7 SD) otherwise. Age is a uniform integer 18–42. BMI is Normal(25.5+1.8×max(IR,0),4.2 SD), clipped to [17,42]. Family history is a binary draw with probability 0.18+0.12×max(IR,0).

The base ovulation day is 16 for healthy_regular, PMOS_C, contraception and early_menarche; 22 for healthy_variable; 26 for other archetypes. The late-group flag is true for healthy_variable, PMOS_A/B/D and thyroid_mimic. Per cycle, stress is Normal(0,1). A candidate day is a Normal draw with mean base+6×positive IR×late-group+3×stress×late-group and SD 4, clipped to [12,45] and converted to an integer. Late-group cycles independently draw absence with probability 0.24+0.09×positive IR; absence replaces that candidate with −1. Androgen does not appear in these timing/absence equations, despite several documents implying direct label influence. Its association comes from the assigned archetype; it does directly affect the separate twin.

If absent, cycle length is a uniform integer 24–41; otherwise it is int(clip(ovulation day+Normal(13,1.8 SD),22,55)). True start date is 2025-01-01 plus cycle_index×38 plus patient_index×400 days. A logged start is shifted by a uniform choice from [−2,0,0,0,1,3], so zero occurs with probability 3/6. These dates extend far into the future across patient indices and are artificial identifiers/alignment fixtures, not observed visit dates.

Temperature has Normal(0,0.035 SD) daily noise, cumulative Normal(0,0.004 SD) increments, a +0.20°C offset from index ovulation_day onward if present, and independent 0.12 probability of a missing night. RHR/HRV have Normal(0,1 SD) noise and post-event offsets +0.35/−0.25. Steps are log-normal with log-mean 8.5 and log-SD 0.25. Sleep is Normal(7,0.75 SD) hours. Every raw cycle has 55 entries irrespective of generated cycle length.

These exact equations explain how prediction without measured hormones works in this experiment: the programmer explicitly creates correlated history, labels and sensor changes. They do not show that the same relationships are sufficient in people.

## 4. Complete workflow: two paths that must not be confused

### Fitted research benchmark

1. generate() creates patients, latent variables, six cycles and synthetic sensor series.
2. patient_partition() puts complete patient IDs into train/validation/test groups.
3. build_feature_matrix() calculates preceding-cycle history and snapshot-limited sensor summaries for the requested tier.
4. PlattModel.fit() fits training medians, scaling and base logistic regression, then fits a probability calibrator on validation scores.
5. Each richer candidate is compared with a fitted calendar baseline. A 500-resample patient-cluster validation interval estimates baseline Brier minus candidate Brier. If its lower bound is ≤0, that tier uses the calendar model.
6. choose_f1_threshold() chooses a threshold from validation predictions.
7. Selected models predict held-out patients; the script calculates metrics and 1,000-resample patient-cluster intervals.
8. results.json saves results, thresholds, selected feature tiers and diagnostic summaries. It does not save weights or predictions.
9. Other scripts turn that JSON into the README table and three SVG figures.

### Dashboard demonstration

1. Load results.json for benchmark context; generate the separate display/calibration cohorts.
2. Optionally parse a synthetic XML file; show parse counts. The scored cohort remains generated.
3. Select an existing patient and display tier. forecast() computes a hand-set sigmoid score.
4. Construct known-archetype safety flags and temperature completeness. Withhold selected patient metric panels when a rule fires.
5. Calculate the coverline/day fallback, class label set and illustrative conformal band.
6. Run the separate reproductive/metabolic simulator for selected examples. None of its state affects the displayed heuristic or saved fitted metrics.
7. Render deterministic text summaries, fixed-multiplier what-if ranges, and the session-only alert log.

The Overview and Method pages summarize saved fitted results. The Cohort and Patient pages calculate heuristic scores. The workflow card's “fitted model → safe alert” is a design-level overview; a fitted model has not been connected to the patient alert path.

Evidence: [scripts/run_eval.py:93–146](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/scripts/run_eval.py:93>); [src/fitted.py:9–21](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/fitted.py:9>); [app.py:118–160](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/app.py:118>), 219–244, 395–522.

## 5. Exact prediction targets, day estimates and intervals

### Binary outcome

event = 1 when ovulation_day < 0 or ovulation_day > 21; otherwise event = 0. The generator represents absence with −1. The classifier predicts the combined label, not separate probabilities of “late” versus “absent,” not a PMOS diagnosis, and not an exact future ovulation date.

At day 10 it uses the prefix through ten array entries; at day 14 fourteen; at day 18 eighteen. This is per generated cycle, not per calendar month. The cutoff at day 21 is an engineering target definition, not a validated clinical diagnostic boundary.

### Fitted probability

After imputation/scaling, the base model calculates a weighted sum z = intercept + weights·features. A separately fitted logistic calibrator converts z into sigmoid(a×z+b). The result is a fitted probability for the synthetic event under the simulator distribution. It is not clinically validated for the displayed patient.

### Fixed dashboard score

Let sigmoid(z) = 1/(1+exp(−z)), with the input clipped to −20…20:

- Tier 0, with history: sigmoid(0.12×(mean prior length−34.5)). Without history: sigmoid(−0.19).
- Tier 1: sigmoid(0.20×mean RHR offset−0.15). It ignores HRV, steps, sleep and calendar history, unlike the fitted Tier 1 feature set.
- Tier 2: sigmoid(−1.05−5×thermal change). It ignores calendar/RHR/HRV/steps/sleep, unlike the fitted Tier 2 feature set.

The dashboard therefore does not implement nested fitted sensor fusion merely because a tier is selected. It recomputes a different fixed formula. Its cutoff is 0.50; benchmark thresholds are validation-selected and differ.

### Ovulation-day heuristic and two confirmed gaps

estimate_ovulation_day() uses mean prior length−14 for Tiers 0/1 when a prior_cycle_lengths field exists. Otherwise it returns forecast day+10. For Tier 2+, it takes an early temperature baseline, searches for three consecutive finite values above baseline+0.12°C, and returns the detected array index; otherwise it uses day+10.

The benchmark's build_feature_matrix() calculates history internally but does not attach prior_cycle_lengths to the original record dictionaries. Consequently, benchmark Tier 0/1 ovulation-day estimates are always the fixed fallback: day 20, 24 or 28. Their reported MAE is not evidence that a calendar day estimator was evaluated correctly.

The dashboard sets item.ov_est using Tier 2 before the selected tier is applied. Changing to Tier 0 changes the score but not this day estimate. For s223-p0002, the current UI shows day 24 even though the helper, if called with Tier 0 and its available 42-day history, would return day 28.

Array/day indexing also needs care: generated rises begin at temperature[ovday:], while plotted cycle days start at one; the coverline returns an index rather than index+1. These conventions have not been reconciled.

### Conformal illustration

At alpha 0.10, calibration uses 240 seed-211 records for classification and 203 records with generated ovulation for day-error calibration. Classification residual is 1−p for positive labels and p for negative labels. The finite-sample quantile rank is ceil((n+1)×(1−alpha)), capped at n.

With n=240 and alpha=0.10, the classification rank is 217. With n=203 ovulatory calibration cases the day-error rank is 184. The resulting classification q is 0.7577412876798274. Label 0 is included when p≤q; label 1 when 1−p≤q. Both labels can be returned, meaning the illustration does not select one outcome. The day-error quantile is 12 days; an estimate of 24 therefore produces [12,36], bounded by the helper's general limits [1,60].

Nominal coverage is 90% under the relevant exchangeability assumptions, not a measured current coverage rate. The calibrated model/population differs from selected Tier 0/1 scores and from the second-cycle display cohort. Day calibration excludes absent-ovulation cycles. These ranges do not provide a 90% personal guarantee or an interval for “no ovulation.”

Evidence: [src/model.py:4–39](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/model.py:4>); [src/conformal.py:5–27](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/conformal.py:5>); [app.py:142–160](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/app.py:142>), 230–235 and 406–411.

## 6. Model architecture, hyperparameters, size and other algorithms

### Fitted classifiers

SimpleImputer(strategy="median", add_indicator=False, keep_empty_features=False) → StandardScaler(with_mean=True, with_std=True) → LogisticRegression. Both base and calibrator use C=1.0, L2 penalty, lbfgs, tolerance 0.0001, intercept enabled, max_iter=1000, no class weights and no warm start. The base random_state is 0 and the calibrator random_state is 1. The calibrator takes one base decision score per record.

There are no neural layers, LSTM, transformer, EKF, learned digital-twin state estimator, language model, online learning or hyperparameter grid search. For p features, the base has p weights plus an intercept; calibration adds one weight and one intercept: p+3 trainable scalar coefficients. The full introspected settings are in [actual_model_hyperparameters.json](actual_model_hyperparameters.json). Candidate sizes are therefore 4/8/10/15 for Tiers 0/1/2/3, excluding preprocessing arrays. Fallbacks have the calendar pipeline's size.

Across the 36 requested configurations, 26 select calendar features, one selects Tier 1 features, five select Tier 2 and four select Tier 3. Requested tier labels therefore do not prove those sensors were actually used.

The script fits 36 candidate PlattModel objects and 27 additional calendar comparison objects, or 63 base/calibrator pairs and 126 logistic-regression fits per complete run. It serializes none. There is no original model file size, persisted optimizer log, learned weights file, registry, load_model() path or deployed fitted inference API to report. Audit-refitted coefficients are supplied as new audit evidence only.

Threshold candidates are the unique union of validation probabilities with 0.05 and 0.95; those constants do not clamp probabilities or enforce a universal threshold range. Maximum validation F1 wins; ties select the larger threshold. A richer tier is compared with Tier 0, not necessarily the previous sensor tier, so adding EHR-lite can fall back to calendar even when Tier 2 was retained.

### Reproductive twin

The 55-day demonstration uses Euler-like daily updates. Follicle growth per day is 0.065−0.025×positive androgen−0.012×positive IR×kappa, plus Gaussian noise SD 0.003, with a minimum increment 0.01. Crossing follicle state 1.0 creates an ovulation-day event. A dimensionless progesterone-like state relaxes toward 1 with factor 0.5/day. Temperature uses a two-day lag, baseline 36.4°C, rise 0.20°C and noise SD 0.02°C. RHR uses baseline 62 bpm, 1.1×progesterone-like state and noise SD 0.6.

These are invented state dynamics for an illustration, not measured follicle diameters, measured LH peaks or measured progesterone concentrations. The chart shows the initial 35 simulated follicle states, not the constant scalar ovulation day.

### Metabolic twin and separate CGM fixture

The dashboard's metabolic twin generates 28 days × 96 samples/day = 2,688 points at 15-minute steps. It uses glucose baseline 95 mg/dL; insulin-state baseline 10 arbitrary units; glucose clearance 0.020/hour; insulin decay 0.10/hour; meal decay 0.40/hour; three meals near hours 8,13,19; log-normal meal amplitudes centred on 28; and 5 mg/dL observation noise. Internal glucose is clipped to 40…300 mg/dL.

At each step, dt=15/60=0.25 hours; meal appearance decays by 0.40×dt, insulin updates from −0.10×(I−10)+0.04×appearance, X updates from −0.05×X+0.0015×max(I−10,0)×sensitivity, and glucose updates from −0.020×(G−95)−X×(G−95)+appearance. Insulin and X are clipped nonnegative; glucose is clamped to [40,300] before and after observation noise. Sensitivity is (1−0.05×luteal_flag)/(1+0.2×positive IR). Meal times have a −1/0/+1 sample jitter. The luteal condition compares a zero-based day counter with the separate twin day, another place where day conventions should be reviewed.

Other update constants are 0.04 for meal-to-insulin gain, 0.05 for insulin-state decay, 0.0015 for insulin-state gain, 0.2 for positive IR's sensitivity effect and a 0.05 luteal sensitivity reduction. Reproductive ovulation timing switches the luteal metabolic term. Glucose itself is not fitted back into the reproductive state; there is no state assimilation from a person's observations.

Only generated patient indices divisible by four get a CGM display: nine of 36 visible patients. The line plots every eighth sample, so 336 displayed points are 120 minutes apart, despite the existing chart title saying “15-minute samples.” The excursion calculation uses full 15-minute data and includes the meal sample plus samples through 120 minutes, up to nine values.

src/metabolic.py also contains a separate simulate_cgm() fixture, used by tests, not by the current dashboard plot. It uses baseline 98+5×positive IR, meal amplitude 24+10×positive IR, exponential decay over up to 12 samples, noise SD 7, a +3 mg/dL luteal offset and a 55…260 clamp. Do not describe these two glucose generators as one fitted physiological model.

coupling_sweep() repeats the reproductive toy model at kappa 0,0.5,1,2 using seed 0. The displayed patient's baseline simulation uses seed 4000+patient index, so the sweep baseline is not the same random trajectory as the patient preview.

### What-ifs, explanations and visualization summaries

What-ifs multiply the current heuristic score by hand-set factors: sleep 0.80…0.98; walk 0.75…0.98; food swap 0.80…1.00; stress 0.80…1.00; weight change 0.75…0.98. They do not rerun a twin or estimate causal intervention effects.

explain_state() ranks the absolute values of supplied raw temperature/RHR summaries and inserts their names into a sentence. They are not fitted coefficient contributions or SHAP values. The same temperature/RHR explanation is used even when the selected score ignores those inputs. Chart summaries separately report actual array means, ranges, counts and peak days, using deterministic templates. No LLM is called.

Evidence: [src/fitted.py:9–35](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/fitted.py:9>); [src/twin.py:5–69](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/twin.py:5>); [src/metabolic.py:4–24](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/metabolic.py:4>); [src/explanations.py:3–12](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/explanations.py:3>); [app.py:438–522](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/app.py:438>).

## 7. Every available result, with exact denominators

### What is saved versus derived

Saved: AUROC, custom AUPRC, Brier, ovulation-day MAE, 95% bootstrap intervals for those four metrics, event rate, validation threshold, sensitivity, PPV, false alerts per 100 cycles, alert rate, nominal lead days, validation Brier-gain intervals, selected features, nine archetype false-positive rates, and eleven threshold-sweep points per configuration.

Audit-derived: integer confusion matrices, accuracy, specificity and F1, plus exact denominators for saved ratios. These were independently confirmed using audit-refitted probabilities that reproduce the current saved point metrics. Recall equals sensitivity; precision equals PPV, so these are not separate experiments.

Unavailable as original measured endpoints: clinical accuracy, externally validated performance, latency, peak/resident memory, serialized model size, reliability/calibration curves, ECE, calibration slope/intercept performance estimates, decision curves, subgroup AUROC/recall confidence intervals, tested abstention/conformal coverage, sensor-dropout robustness, simulator-shift performance, prospective alert lead time, CGM forecast accuracy and causal intervention effects. Toy unit-test coverage checks are not benchmark coverage evidence.

### Definitions for judges

TP means a positive generated cycle was flagged; FP means a negative cycle was flagged; TN means a negative cycle was not flagged; FN means a positive cycle was missed.

- Accuracy = (TP+TN)/all cycles.
- Precision or PPV = TP/(TP+FP): fraction of flags that are positive.
- Recall or sensitivity = TP/(TP+FN): fraction of positive cycles caught.
- Specificity = TN/(TN+FP): fraction of negative cycles left unflagged.
- F1 = 2TP/(2TP+FP+FN): a balance of precision and recall.
- AUROC measures ranking while accounting for score ties.
- Brier is mean squared probability error; lower is better, but it measures more than calibration alone.
- MAE is mean absolute day error, only among cycles with generated ovulation.

The saved AUPRC uses a custom rank-by-rank calculation. Equal scores are not grouped into common thresholds, so it differs from sklearn average_precision_score; the maximum difference found across these configurations is 0.010018763007265674. The audit preserves the published statistic and exports the standard comparison separately. A custom value should not be described as a standard AP result without this qualification.

“False alerts per 100 cycles” divides FP by all cycles, whereas archetype false-alarm rate divides FP by negative cycles in that archetype. These are different denominators.

“Median lead days versus day 35” is 35−forecast day for true-positive flags: 25,21,17 days at the three snapshots. It is not a measured lead time before the actual ovulation event. If a configuration has true positives, the calculation cannot provide anything except that snapshot's constant.

| Day | Requested tier | Mean AUROC | Mean custom AUPRC | Mean Brier | Mean day-MAE | Feature tiers selected (97,101,103) |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 0 | 0.8377224357236708 | 0.8353597941029861 | 0.16311850367792477 | 5.870416673854902 | [0, 0, 0] |
| 10 | 1 | 0.8377224357236708 | 0.8353597941029861 | 0.16311850367792477 | 5.870416673854902 | [0, 0, 0] |
| 10 | 2 | 0.8377224357236708 | 0.8353597941029861 | 0.16311850367792477 | 5.870416673854902 | [0, 0, 0] |
| 10 | 3 | 0.8377224357236708 | 0.8353597941029861 | 0.16311850367792477 | 5.870416673854902 | [0, 0, 0] |
| 14 | 0 | 0.8377224357236708 | 0.8353597941029861 | 0.16311850367792477 | 6.581647161080291 | [0, 0, 0] |
| 14 | 1 | 0.8377224357236708 | 0.8353597941029861 | 0.16311850367792477 | 6.581647161080291 | [0, 0, 0] |
| 14 | 2 | 0.850400359749365 | 0.840886270741104 | 0.15680910368817444 | 6.581647161080291 | [2, 0, 2] |
| 14 | 3 | 0.8433372338207447 | 0.8389720935038044 | 0.16080406836764188 | 6.581647161080291 | [0, 0, 3] |
| 18 | 0 | 0.8377224357236708 | 0.8353597941029861 | 0.16311850367792477 | 8.574076944720234 | [0, 0, 0] |
| 18 | 1 | 0.8386977297982733 | 0.8360190231151146 | 0.16273079934221843 | 8.574076944720234 | [0, 1, 0] |
| 18 | 2 | 0.9055841352847533 | 0.8800789329197162 | 0.11909081356511754 | 5.267415709909418 | [2, 2, 2] |
| 18 | 3 | 0.9065697596902321 | 0.8836479161864642 | 0.11887225370805767 | 5.267415709909418 | [3, 3, 3] |

Each row covers 3,240 cycle predictions from 540 people: 1,663 positive and 1,577 negative cycles. Day-MAE uses 2,772 ovulatory cycles, but the mean above weights seeds equally rather than pooling MAE by those denominators. The same cycles recur across forecast days and tiers; do not multiply the participant count by the number of configurations.

| Day | Tier | TP | FP | TN | FN | Pooled accuracy | Pooled precision | Pooled recall | Pooled specificity | Pooled F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 0 | 1427 | 554 | 1023 | 236 | 0.7561728395061729 | 0.7203432609793033 | 0.8580877931449188 | 0.6487000634115409 | 0.783205268935236 |
| 10 | 1 | 1427 | 554 | 1023 | 236 | 0.7561728395061729 | 0.7203432609793033 | 0.8580877931449188 | 0.6487000634115409 | 0.783205268935236 |
| 10 | 2 | 1427 | 554 | 1023 | 236 | 0.7561728395061729 | 0.7203432609793033 | 0.8580877931449188 | 0.6487000634115409 | 0.783205268935236 |
| 10 | 3 | 1427 | 554 | 1023 | 236 | 0.7561728395061729 | 0.7203432609793033 | 0.8580877931449188 | 0.6487000634115409 | 0.783205268935236 |
| 14 | 0 | 1427 | 554 | 1023 | 236 | 0.7561728395061729 | 0.7203432609793033 | 0.8580877931449188 | 0.6487000634115409 | 0.783205268935236 |
| 14 | 1 | 1427 | 554 | 1023 | 236 | 0.7561728395061729 | 0.7203432609793033 | 0.8580877931449188 | 0.6487000634115409 | 0.783205268935236 |
| 14 | 2 | 1415 | 479 | 1098 | 248 | 0.7756172839506172 | 0.7470960929250264 | 0.8508719182200842 | 0.6962587190868738 | 0.7956142816980601 |
| 14 | 3 | 1395 | 482 | 1095 | 268 | 0.7685185185185185 | 0.7432072456046883 | 0.8388454600120264 | 0.6943563728598605 | 0.788135593220339 |
| 18 | 0 | 1427 | 554 | 1023 | 236 | 0.7561728395061729 | 0.7203432609793033 | 0.8580877931449188 | 0.6487000634115409 | 0.783205268935236 |
| 18 | 1 | 1424 | 538 | 1039 | 239 | 0.7601851851851852 | 0.72579001019368 | 0.8562838244137102 | 0.6588459099556119 | 0.7856551724137931 |
| 18 | 2 | 1541 | 403 | 1174 | 122 | 0.8379629629629629 | 0.7926954732510288 | 0.9266386049308478 | 0.7444514901712111 | 0.8544496811754921 |
| 18 | 3 | 1516 | 390 | 1187 | 147 | 0.8342592592592593 | 0.7953830010493179 | 0.9116055321707757 | 0.7526949904882688 | 0.8495376856262258 |

These cross-seed point summaries are descriptive. The following tables give the actual saved per-seed values and their uncertainty.

#### Saved discrimination/probability metrics (point [95% patient-bootstrap interval])

| Seed | Day | Tier | Feature tier used | AUROC [CI] | Custom AUPRC [CI] | Brier [CI] |
| --- | --- | --- | --- | --- | --- | --- |
| 97 | 10 | 0 | 0 | 0.8433889469630281 [0.8132978986313895, 0.8711719790763468] | 0.8579562492762459 [0.8180306527054729, 0.8928405038707941] | 0.16063805584997093 [0.14505214180067164, 0.17623155093475273] |
| 97 | 10 | 1 | 0 | 0.8433889469630281 [0.8123837110084995, 0.870457480042607] | 0.8579562492762459 [0.8161639477659786, 0.8949126510758127] | 0.16063805584997093 [0.14493281337811745, 0.1763836755609201] |
| 97 | 10 | 2 | 0 | 0.8433889469630281 [0.8154741389536827, 0.8683798135514207] | 0.8579562492762459 [0.8181483813245983, 0.8914759867970561] | 0.16063805584997093 [0.14641810288569726, 0.17522097698268793] |
| 97 | 10 | 3 | 0 | 0.8433889469630281 [0.8119511278741668, 0.869286331818738] | 0.8579562492762459 [0.8164156094806839, 0.8913613878935661] | 0.16063805584997093 [0.1457403562510417, 0.17642426362694683] |
| 97 | 14 | 0 | 0 | 0.8433889469630281 [0.815635844456804, 0.8700161306528139] | 0.8579562492762459 [0.8211463297049297, 0.8937079727198277] | 0.16063805584997093 [0.14551086904621066, 0.17533387881959936] |
| 97 | 14 | 1 | 0 | 0.8433889469630281 [0.8126850353917866, 0.8719537490126719] | 0.8579562492762459 [0.814749888318067, 0.8910491941335478] | 0.16063805584997093 [0.14486836891625374, 0.17636587373742083] |
| 97 | 14 | 2 | 2 | 0.8621430732834507 [0.8328565349331672, 0.8861272539018201] | 0.8633178922522238 [0.8184993578194175, 0.8964290013099168] | 0.15046987744496398 [0.13649807601452613, 0.1664348220837626] |
| 97 | 14 | 3 | 0 | 0.8433889469630281 [0.8147197335713798, 0.8713475432088565] | 0.8579562492762459 [0.8211717069410013, 0.8917016882238751] | 0.16063805584997093 [0.14469455692127095, 0.17522242918642916] |
| 97 | 18 | 0 | 0 | 0.8433889469630281 [0.8135304151279713, 0.8713677210180867] | 0.8579562492762459 [0.8161976130216838, 0.891640599978466] | 0.16063805584997093 [0.14477582428239147, 0.17598382690373057] |
| 97 | 18 | 1 | 0 | 0.8433889469630281 [0.8120527840685627, 0.8714328397384575] | 0.8579562492762459 [0.8186340828375308, 0.8934083099024958] | 0.16063805584997093 [0.14474941751883527, 0.17609803656627177] |
| 97 | 18 | 2 | 2 | 0.9093550561179577 [0.8864679931063524, 0.9290191211006342] | 0.8883241965927711 [0.850734188339719, 0.9205875495605287] | 0.11570009278056827 [0.10310655450511864, 0.1297744491215726] |
| 97 | 18 | 3 | 3 | 0.9093860035211268 [0.8854928004774709, 0.9303307163022108] | 0.8886506559248354 [0.847829539872645, 0.9234481610405776] | 0.11573020885143721 [0.10128136661251887, 0.13026693657376742] |
| 101 | 10 | 0 | 0 | 0.8367131331979584 [0.8045132446522241, 0.8668128842258652] | 0.829774600268579 [0.7813628601149629, 0.8706864182117675] | 0.16428639510752058 [0.14861498085179162, 0.1797966533067524] |
| 101 | 10 | 1 | 0 | 0.8367131331979584 [0.8041856799315721, 0.8650204680309326] | 0.829774600268579 [0.7801567669714137, 0.8659119570193008] | 0.16428639510752058 [0.14951002983596715, 0.18019791180752587] |
| 101 | 10 | 2 | 0 | 0.8367131331979584 [0.8054150067580343, 0.8639607907086346] | 0.829774600268579 [0.780467350314056, 0.8684149157178639] | 0.16428639510752058 [0.14925793899239728, 0.17915414598099158] |
| 101 | 10 | 3 | 0 | 0.8367131331979584 [0.8048972759351996, 0.8661340492804162] | 0.829774600268579 [0.7840756531233962, 0.8703840548407847] | 0.16428639510752058 [0.14852071535394537, 0.1799087711779883] |
| 101 | 14 | 0 | 0 | 0.8367131331979584 [0.8053595492327076, 0.8653729316240617] | 0.829774600268579 [0.7807594635668365, 0.870606800057831] | 0.16428639510752058 [0.14905355870573647, 0.17904623393066635] |
| 101 | 14 | 1 | 0 | 0.8367131331979584 [0.8060544683077517, 0.8641563807048478] | 0.829774600268579 [0.7797206924760055, 0.8683309894461098] | 0.16428639510752058 [0.14952228866634898, 0.17902967417828974] |
| 101 | 14 | 2 | 0 | 0.8367131331979584 [0.8063374772019697, 0.8654433966742765] | 0.829774600268579 [0.7825455776679346, 0.868646249024802] | 0.16428639510752058 [0.14961536264017786, 0.17900232050963777] |
| 101 | 14 | 3 | 0 | 0.8367131331979584 [0.8030216247097166, 0.8660281078346069] | 0.829774600268579 [0.7804239878830549, 0.8697041621886772] | 0.16428639510752058 [0.14846654068838186, 0.18052539478946864] |
| 101 | 18 | 0 | 0 | 0.8367131331979584 [0.8052997576819002, 0.8637904933458298] | 0.829774600268579 [0.7845214175426969, 0.8699261438695405] | 0.16428639510752058 [0.14944972531720846, 0.1796302229803224] |
| 101 | 18 | 1 | 1 | 0.8396390154217661 [0.8101684663213122, 0.8661647529834109] | 0.8317522873049641 [0.787569081697247, 0.868243740525834] | 0.1631232821004016 [0.1487946267275934, 0.177922634727909] |
| 101 | 18 | 2 | 2 | 0.900314197903518 [0.8753716890663509, 0.9212274726069648] | 0.8779053367130706 [0.8420617248903424, 0.9112254394244104] | 0.1239556989278957 [0.11007170357444863, 0.13831391303670132] |
| 101 | 18 | 3 | 3 | 0.9040873168322265 [0.8830061720225771, 0.9252384869731589] | 0.8875598137906201 [0.8518688399899953, 0.9181866250651599] | 0.12260823140565633 [0.10799001826854476, 0.13598883883538232] |
| 103 | 10 | 0 | 0 | 0.8330652270100257 [0.8005352042757172, 0.8623530368000482] | 0.8183485327641334 [0.7670306777318067, 0.8579863542136086] | 0.16443106007628275 [0.14829490965249717, 0.18118842576589214] |
| 103 | 10 | 1 | 0 | 0.8330652270100257 [0.8024097504511833, 0.8605361910734206] | 0.8183485327641334 [0.7714291271595216, 0.8579850444327296] | 0.16443106007628275 [0.1496349176461072, 0.17974028703090877] |
| 103 | 10 | 2 | 0 | 0.8330652270100257 [0.7986575172587858, 0.8627598405438027] | 0.8183485327641334 [0.7695127861095039, 0.8565976353750909] | 0.16443106007628275 [0.1478664524856588, 0.1814625475622176] |
| 103 | 10 | 3 | 0 | 0.8330652270100257 [0.7998486227654729, 0.8637242272343115] | 0.8183485327641334 [0.7736308277709278, 0.8587957837967211] | 0.16443106007628275 [0.14795137676962675, 0.18126753575730664] |
| 103 | 14 | 0 | 0 | 0.8330652270100257 [0.8001819962463049, 0.8609686829998524] | 0.8183485327641334 [0.7742572607219742, 0.8567500502769771] | 0.16443106007628275 [0.14924832337528424, 0.1810391940449994] |
| 103 | 14 | 1 | 0 | 0.8330652270100257 [0.8013276238903652, 0.8621023589004699] | 0.8183485327641334 [0.7697920132966806, 0.8579415981274114] | 0.16443106007628275 [0.1487122237100806, 0.18033071945381893] |
| 103 | 14 | 2 | 2 | 0.8523448727666858 [0.822098558186951, 0.8779515586341242] | 0.8295663197025093 [0.7879813583527779, 0.8695534501759452] | 0.15567103851203873 [0.14031121571880592, 0.1721839280721015] |
| 103 | 14 | 3 | 3 | 0.8499096213012475 [0.8198865795723862, 0.876847330636035] | 0.8291854309665887 [0.7852038419661208, 0.8678828463510223] | 0.15748775414543414 [0.1415503109647078, 0.17371600763669548] |
| 103 | 18 | 0 | 0 | 0.8330652270100257 [0.8017923054971059, 0.8625599384711061] | 0.8183485327641334 [0.7731359423331771, 0.8555128113758115] | 0.16443106007628275 [0.1479261286035091, 0.1803194826071625] |
| 103 | 18 | 1 | 0 | 0.8330652270100257 [0.8001130576635344, 0.8620616215301475] | 0.8183485327641334 [0.7698074931735905, 0.8592915393665245] | 0.16443106007628275 [0.14833684977440725, 0.18056084038034845] |
| 103 | 18 | 2 | 2 | 0.907083151832784 [0.8830149191811731, 0.9261472373370184] | 0.8740072654533065 [0.8345408648111243, 0.907686831441005] | 0.11761664898688869 [0.1042852955066493, 0.132034663329018] |
| 103 | 18 | 3 | 3 | 0.9062359587173427 [0.8820831730100651, 0.926945616596309] | 0.8747332788439369 [0.8366861994797372, 0.910277613807725] | 0.11827832086707947 [0.1032399078339581, 0.1335886966311926] |

#### Exact confusion counts and audit-derived operating-point metrics

Every configuration below has 1,080 held-out cycles from 180 patients. Accuracy, specificity and F1 were derived in this audit, not separately logged in the original evaluator. Precision and sensitivity reproduce saved PPV/recall.

| Seed | Day | Tier | TP/FP/TN/FN | Accuracy (fraction) | Precision (fraction) | Sensitivity (fraction) | Specificity (fraction) | F1 (fraction) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 97 | 10 | 0 | 475/164/348/93 | 0.7620370370370371 (823/1080) | 0.7433489827856025 (475/639) | 0.8362676056338029 (475/568) | 0.6796875 (348/512) | 0.7870753935376967 (950/1207) |
| 97 | 10 | 1 | 475/164/348/93 | 0.7620370370370371 (823/1080) | 0.7433489827856025 (475/639) | 0.8362676056338029 (475/568) | 0.6796875 (348/512) | 0.7870753935376967 (950/1207) |
| 97 | 10 | 2 | 475/164/348/93 | 0.7620370370370371 (823/1080) | 0.7433489827856025 (475/639) | 0.8362676056338029 (475/568) | 0.6796875 (348/512) | 0.7870753935376967 (950/1207) |
| 97 | 10 | 3 | 475/164/348/93 | 0.7620370370370371 (823/1080) | 0.7433489827856025 (475/639) | 0.8362676056338029 (475/568) | 0.6796875 (348/512) | 0.7870753935376967 (950/1207) |
| 97 | 14 | 0 | 475/164/348/93 | 0.7620370370370371 (823/1080) | 0.7433489827856025 (475/639) | 0.8362676056338029 (475/568) | 0.6796875 (348/512) | 0.7870753935376967 (950/1207) |
| 97 | 14 | 1 | 475/164/348/93 | 0.7620370370370371 (823/1080) | 0.7433489827856025 (475/639) | 0.8362676056338029 (475/568) | 0.6796875 (348/512) | 0.7870753935376967 (950/1207) |
| 97 | 14 | 2 | 490/151/361/78 | 0.787962962962963 (851/1080) | 0.7644305772230889 (490/641) | 0.8626760563380281 (490/568) | 0.705078125 (361/512) | 0.8105872622001654 (980/1209) |
| 97 | 14 | 3 | 475/164/348/93 | 0.7620370370370371 (823/1080) | 0.7433489827856025 (475/639) | 0.8362676056338029 (475/568) | 0.6796875 (348/512) | 0.7870753935376967 (950/1207) |
| 97 | 18 | 0 | 475/164/348/93 | 0.7620370370370371 (823/1080) | 0.7433489827856025 (475/639) | 0.8362676056338029 (475/568) | 0.6796875 (348/512) | 0.7870753935376967 (950/1207) |
| 97 | 18 | 1 | 475/164/348/93 | 0.7620370370370371 (823/1080) | 0.7433489827856025 (475/639) | 0.8362676056338029 (475/568) | 0.6796875 (348/512) | 0.7870753935376967 (950/1207) |
| 97 | 18 | 2 | 539/138/374/29 | 0.8453703703703703 (913/1080) | 0.7961595273264401 (539/677) | 0.948943661971831 (539/568) | 0.73046875 (374/512) | 0.8658634538152611 (1078/1245) |
| 97 | 18 | 3 | 531/136/376/37 | 0.8398148148148148 (907/1080) | 0.7961019490254873 (531/667) | 0.9348591549295775 (531/568) | 0.734375 (376/512) | 0.8599190283400809 (1062/1235) |
| 101 | 10 | 0 | 457/170/362/91 | 0.7583333333333333 (819/1080) | 0.7288676236044657 (457/627) | 0.833941605839416 (457/548) | 0.6804511278195489 (362/532) | 0.7778723404255319 (914/1175) |
| 101 | 10 | 1 | 457/170/362/91 | 0.7583333333333333 (819/1080) | 0.7288676236044657 (457/627) | 0.833941605839416 (457/548) | 0.6804511278195489 (362/532) | 0.7778723404255319 (914/1175) |
| 101 | 10 | 2 | 457/170/362/91 | 0.7583333333333333 (819/1080) | 0.7288676236044657 (457/627) | 0.833941605839416 (457/548) | 0.6804511278195489 (362/532) | 0.7778723404255319 (914/1175) |
| 101 | 10 | 3 | 457/170/362/91 | 0.7583333333333333 (819/1080) | 0.7288676236044657 (457/627) | 0.833941605839416 (457/548) | 0.6804511278195489 (362/532) | 0.7778723404255319 (914/1175) |
| 101 | 14 | 0 | 457/170/362/91 | 0.7583333333333333 (819/1080) | 0.7288676236044657 (457/627) | 0.833941605839416 (457/548) | 0.6804511278195489 (362/532) | 0.7778723404255319 (914/1175) |
| 101 | 14 | 1 | 457/170/362/91 | 0.7583333333333333 (819/1080) | 0.7288676236044657 (457/627) | 0.833941605839416 (457/548) | 0.6804511278195489 (362/532) | 0.7778723404255319 (914/1175) |
| 101 | 14 | 2 | 457/170/362/91 | 0.7583333333333333 (819/1080) | 0.7288676236044657 (457/627) | 0.833941605839416 (457/548) | 0.6804511278195489 (362/532) | 0.7778723404255319 (914/1175) |
| 101 | 14 | 3 | 457/170/362/91 | 0.7583333333333333 (819/1080) | 0.7288676236044657 (457/627) | 0.833941605839416 (457/548) | 0.6804511278195489 (362/532) | 0.7778723404255319 (914/1175) |
| 101 | 18 | 0 | 457/170/362/91 | 0.7583333333333333 (819/1080) | 0.7288676236044657 (457/627) | 0.833941605839416 (457/548) | 0.6804511278195489 (362/532) | 0.7778723404255319 (914/1175) |
| 101 | 18 | 1 | 454/154/378/94 | 0.7703703703703704 (832/1080) | 0.7467105263157895 (454/608) | 0.8284671532846716 (454/548) | 0.7105263157894737 (378/532) | 0.7854671280276817 (908/1156) |
| 101 | 18 | 2 | 503/138/394/45 | 0.8305555555555556 (897/1080) | 0.7847113884555382 (503/641) | 0.9178832116788321 (503/548) | 0.7406015037593985 (394/532) | 0.8460891505466779 (1006/1189) |
| 101 | 18 | 3 | 504/140/392/44 | 0.8296296296296296 (896/1080) | 0.782608695652174 (504/644) | 0.9197080291970803 (504/548) | 0.7368421052631579 (392/532) | 0.8456375838926175 (1008/1192) |
| 103 | 10 | 0 | 495/220/313/52 | 0.7481481481481481 (808/1080) | 0.6923076923076923 (495/715) | 0.9049360146252285 (495/547) | 0.5872420262664165 (313/533) | 0.7844690966719493 (990/1262) |
| 103 | 10 | 1 | 495/220/313/52 | 0.7481481481481481 (808/1080) | 0.6923076923076923 (495/715) | 0.9049360146252285 (495/547) | 0.5872420262664165 (313/533) | 0.7844690966719493 (990/1262) |
| 103 | 10 | 2 | 495/220/313/52 | 0.7481481481481481 (808/1080) | 0.6923076923076923 (495/715) | 0.9049360146252285 (495/547) | 0.5872420262664165 (313/533) | 0.7844690966719493 (990/1262) |
| 103 | 10 | 3 | 495/220/313/52 | 0.7481481481481481 (808/1080) | 0.6923076923076923 (495/715) | 0.9049360146252285 (495/547) | 0.5872420262664165 (313/533) | 0.7844690966719493 (990/1262) |
| 103 | 14 | 0 | 495/220/313/52 | 0.7481481481481481 (808/1080) | 0.6923076923076923 (495/715) | 0.9049360146252285 (495/547) | 0.5872420262664165 (313/533) | 0.7844690966719493 (990/1262) |
| 103 | 14 | 1 | 495/220/313/52 | 0.7481481481481481 (808/1080) | 0.6923076923076923 (495/715) | 0.9049360146252285 (495/547) | 0.5872420262664165 (313/533) | 0.7844690966719493 (990/1262) |
| 103 | 14 | 2 | 468/158/375/79 | 0.7805555555555556 (843/1080) | 0.7476038338658147 (468/626) | 0.8555758683729433 (468/547) | 0.7035647279549718 (375/533) | 0.7979539641943734 (936/1173) |
| 103 | 14 | 3 | 463/148/385/84 | 0.7851851851851852 (848/1080) | 0.7577741407528642 (463/611) | 0.8464351005484461 (463/547) | 0.7223264540337712 (385/533) | 0.7996545768566494 (926/1158) |
| 103 | 18 | 0 | 495/220/313/52 | 0.7481481481481481 (808/1080) | 0.6923076923076923 (495/715) | 0.9049360146252285 (495/547) | 0.5872420262664165 (313/533) | 0.7844690966719493 (990/1262) |
| 103 | 18 | 1 | 495/220/313/52 | 0.7481481481481481 (808/1080) | 0.6923076923076923 (495/715) | 0.9049360146252285 (495/547) | 0.5872420262664165 (313/533) | 0.7844690966719493 (990/1262) |
| 103 | 18 | 2 | 499/127/406/48 | 0.8379629629629629 (905/1080) | 0.7971246006389776 (499/626) | 0.9122486288848263 (499/547) | 0.7617260787992496 (406/533) | 0.8508098891730606 (998/1173) |
| 103 | 18 | 3 | 481/114/419/66 | 0.8333333333333334 (900/1080) | 0.8084033613445378 (481/595) | 0.8793418647166362 (481/547) | 0.7861163227016885 (419/533) | 0.8423817863397548 (962/1142) |

#### Saved operating threshold, flag rates and nominal day-35 distance

| Seed | Day | Tier | Validation threshold | False flags/100 all cycles | Flag rate (flagged/1080) | Nominal lead vs day35 | Positive/negative counts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 97 | 10 | 0 | 0.47977756998218585 | 15.185185185185185 | 0.5916666666666667 (639/1080) | 25.0 | 568/512 |
| 97 | 10 | 1 | 0.47977756998218585 | 15.185185185185185 | 0.5916666666666667 (639/1080) | 25.0 | 568/512 |
| 97 | 10 | 2 | 0.47977756998218585 | 15.185185185185185 | 0.5916666666666667 (639/1080) | 25.0 | 568/512 |
| 97 | 10 | 3 | 0.47977756998218585 | 15.185185185185185 | 0.5916666666666667 (639/1080) | 25.0 | 568/512 |
| 97 | 14 | 0 | 0.47977756998218585 | 15.185185185185185 | 0.5916666666666667 (639/1080) | 21.0 | 568/512 |
| 97 | 14 | 1 | 0.47977756998218585 | 15.185185185185185 | 0.5916666666666667 (639/1080) | 21.0 | 568/512 |
| 97 | 14 | 2 | 0.40442880140125764 | 13.981481481481481 | 0.5935185185185186 (641/1080) | 21.0 | 568/512 |
| 97 | 14 | 3 | 0.47977756998218585 | 15.185185185185185 | 0.5916666666666667 (639/1080) | 21.0 | 568/512 |
| 97 | 18 | 0 | 0.47977756998218585 | 15.185185185185185 | 0.5916666666666667 (639/1080) | 17.0 | 568/512 |
| 97 | 18 | 1 | 0.47977756998218585 | 15.185185185185185 | 0.5916666666666667 (639/1080) | 17.0 | 568/512 |
| 97 | 18 | 2 | 0.3121237502922655 | 12.777777777777779 | 0.6268518518518519 (677/1080) | 17.0 | 568/512 |
| 97 | 18 | 3 | 0.3390451644641081 | 12.592592592592593 | 0.6175925925925926 (667/1080) | 17.0 | 568/512 |
| 101 | 10 | 0 | 0.4721112439689477 | 15.74074074074074 | 0.5805555555555556 (627/1080) | 25.0 | 548/532 |
| 101 | 10 | 1 | 0.4721112439689477 | 15.74074074074074 | 0.5805555555555556 (627/1080) | 25.0 | 548/532 |
| 101 | 10 | 2 | 0.4721112439689477 | 15.74074074074074 | 0.5805555555555556 (627/1080) | 25.0 | 548/532 |
| 101 | 10 | 3 | 0.4721112439689477 | 15.74074074074074 | 0.5805555555555556 (627/1080) | 25.0 | 548/532 |
| 101 | 14 | 0 | 0.4721112439689477 | 15.74074074074074 | 0.5805555555555556 (627/1080) | 21.0 | 548/532 |
| 101 | 14 | 1 | 0.4721112439689477 | 15.74074074074074 | 0.5805555555555556 (627/1080) | 21.0 | 548/532 |
| 101 | 14 | 2 | 0.4721112439689477 | 15.74074074074074 | 0.5805555555555556 (627/1080) | 21.0 | 548/532 |
| 101 | 14 | 3 | 0.4721112439689477 | 15.74074074074074 | 0.5805555555555556 (627/1080) | 21.0 | 548/532 |
| 101 | 18 | 0 | 0.4721112439689477 | 15.74074074074074 | 0.5805555555555556 (627/1080) | 17.0 | 548/532 |
| 101 | 18 | 1 | 0.44634905365633165 | 14.25925925925926 | 0.562962962962963 (608/1080) | 17.0 | 548/532 |
| 101 | 18 | 2 | 0.42482470550764995 | 12.777777777777779 | 0.5935185185185186 (641/1080) | 17.0 | 548/532 |
| 101 | 18 | 3 | 0.4140484964211517 | 12.962962962962964 | 0.5962962962962963 (644/1080) | 17.0 | 548/532 |
| 103 | 10 | 0 | 0.359280405455455 | 20.37037037037037 | 0.6620370370370371 (715/1080) | 25.0 | 547/533 |
| 103 | 10 | 1 | 0.359280405455455 | 20.37037037037037 | 0.6620370370370371 (715/1080) | 25.0 | 547/533 |
| 103 | 10 | 2 | 0.359280405455455 | 20.37037037037037 | 0.6620370370370371 (715/1080) | 25.0 | 547/533 |
| 103 | 10 | 3 | 0.359280405455455 | 20.37037037037037 | 0.6620370370370371 (715/1080) | 25.0 | 547/533 |
| 103 | 14 | 0 | 0.359280405455455 | 20.37037037037037 | 0.6620370370370371 (715/1080) | 21.0 | 547/533 |
| 103 | 14 | 1 | 0.359280405455455 | 20.37037037037037 | 0.6620370370370371 (715/1080) | 21.0 | 547/533 |
| 103 | 14 | 2 | 0.39406806056274535 | 14.62962962962963 | 0.5796296296296296 (626/1080) | 21.0 | 547/533 |
| 103 | 14 | 3 | 0.4117168311510615 | 13.703703703703704 | 0.5657407407407408 (611/1080) | 21.0 | 547/533 |
| 103 | 18 | 0 | 0.359280405455455 | 20.37037037037037 | 0.6620370370370371 (715/1080) | 17.0 | 547/533 |
| 103 | 18 | 1 | 0.359280405455455 | 20.37037037037037 | 0.6620370370370371 (715/1080) | 17.0 | 547/533 |
| 103 | 18 | 2 | 0.39521510469750376 | 11.75925925925926 | 0.5796296296296296 (626/1080) | 17.0 | 547/533 |
| 103 | 18 | 3 | 0.46096241535455973 | 10.555555555555555 | 0.5509259259259259 (595/1080) | 17.0 | 547/533 |

#### Saved day-error metrics and validation candidate-selection evidence

The requested tier drives the day helper even when classification falls back to Tier 0. This table therefore does not describe a learned day-regression model. Gain intervals are validation baseline Brier minus candidate Brier, not held-out intervals. An empty Tier 0 entry means not applicable.

| Seed | Day | Tier | Day MAE [95% CI] | Ovulatory denominator | Validation Brier-gain [95% CI] | Selected feature tier |
| --- | --- | --- | --- | --- | --- | --- |
| 97 | 10 | 0 | 6.169749727965179 [5.800431499460625, 6.588715538555406] | 919 |  | 0 |
| 97 | 10 | 1 | 6.169749727965179 [5.786141364612932, 6.5915970203488365] | 919 | [-0.0003271264917682335, 0.000221117006547604] | 0 |
| 97 | 10 | 2 | 6.169749727965179 [5.805962500126792, 6.588188325991189] | 919 | [-0.0009399191218766289, 0.0003958651296858658] | 0 |
| 97 | 10 | 3 | 6.169749727965179 [5.797776316955712, 6.559801838129562] | 919 | [-0.005834115442947826, 0.0025163712254691033] | 0 |
| 97 | 14 | 0 | 6.787812840043525 [6.430681818181818, 7.127485435249614] | 919 |  | 0 |
| 97 | 14 | 1 | 6.787812840043525 [6.399242025716598, 7.139673026084299] | 919 | [-0.0004339330400343754, 0.000844312689408382] | 0 |
| 97 | 14 | 2 | 6.787812840043525 [6.410306871696065, 7.153656811287595] | 919 | [0.0019775100423390923, 0.01115556152481386] | 2 |
| 97 | 14 | 3 | 6.787812840043525 [6.414739458081476, 7.151882803060813] | 919 | [-0.0009266439344271018, 0.011309701417332667] | 0 |
| 97 | 18 | 0 | 8.576713819368878 [7.960406278139796, 9.126806981170553] | 919 |  | 0 |
| 97 | 18 | 1 | 8.576713819368878 [7.996643698830447, 9.163180718962819] | 919 | [-0.0013105613111659585, 0.003580133366928528] | 0 |
| 97 | 18 | 2 | 5.137105549510338 [4.851393792031153, 5.45093810847086] | 919 | [0.03178983360807669, 0.04890641150048263] | 2 |
| 97 | 18 | 3 | 5.137105549510338 [4.863689766424137, 5.453204766696307] | 919 | [0.03138564192115538, 0.05081047305446928] | 3 |
| 101 | 10 | 0 | 5.854961832061068 [5.494483048657313, 6.236228051939052] | 917 |  | 0 |
| 101 | 10 | 1 | 5.854961832061068 [5.464291741908599, 6.261497784045125] | 917 | [-0.0003849164454376345, 0.00037600533708273553] | 0 |
| 101 | 10 | 2 | 5.854961832061068 [5.476439699827022, 6.2747924498746865] | 917 | [-0.000808650025359628, 0.0006675830396394471] | 0 |
| 101 | 10 | 3 | 5.854961832061068 [5.4696208164656355, 6.295343869134764] | 917 | [-0.0038050938834730424, 0.0038247631457041416] | 0 |
| 101 | 14 | 0 | 6.624863685932389 [6.255573233944498, 6.989113959712636] | 917 |  | 0 |
| 101 | 14 | 1 | 6.624863685932389 [6.262008645881102, 6.979466906882138] | 917 | [-0.0002631842894979782, 0.0005225142885062326] | 0 |
| 101 | 14 | 2 | 6.624863685932389 [6.258172107015305, 6.967990202901007] | 917 | [-0.0011500026392516195, 0.006541307229380818] | 0 |
| 101 | 14 | 3 | 6.624863685932389 [6.263853340516345, 6.973720656258704] | 917 | [-0.0025702676067069206, 0.007996454063382567] | 0 |
| 101 | 18 | 0 | 8.642311886586695 [8.081629620280731, 9.154490982501489] | 917 |  | 0 |
| 101 | 18 | 1 | 8.642311886586695 [8.094942562383789, 9.237949807604076] | 917 | [0.0002759202215541582, 0.0028851559271768786] | 1 |
| 101 | 18 | 2 | 5.5038167938931295 [5.18967420233124, 5.818099974617679] | 917 | [0.03235643906322308, 0.04950714049334661] | 2 |
| 101 | 18 | 3 | 5.5038167938931295 [5.206759199428233, 5.847157972827509] | 917 | [0.03100676246977223, 0.0491257753719462] | 3 |
| 103 | 10 | 0 | 5.586538461538462 [5.282095398417384, 5.924898728512084] | 936 |  | 0 |
| 103 | 10 | 1 | 5.586538461538462 [5.264665331048567, 5.900060307017545] | 936 | [-9.184075825036281e-05, 0.0009343967707392511] | 0 |
| 103 | 10 | 2 | 5.586538461538462 [5.28485262634758, 5.923290796168437] | 936 | [-0.00019031382947031977, 0.0009015622287481352] | 0 |
| 103 | 10 | 3 | 5.586538461538462 [5.266461189539776, 5.904407653002975] | 936 | [-0.0004977507949044055, 0.007805075372602627] | 0 |
| 103 | 14 | 0 | 6.332264957264957 [5.986971449084965, 6.69106221109399] | 936 |  | 0 |
| 103 | 14 | 1 | 6.332264957264957 [5.95583780816519, 6.701505694508409] | 936 | [-0.0005815791508385754, 0.0005160435741943954] | 0 |
| 103 | 14 | 2 | 6.332264957264957 [5.97739548536641, 6.6605197438412755] | 936 | [0.002927629070810225, 0.009890976896237785] | 2 |
| 103 | 14 | 3 | 6.332264957264957 [5.9606790558601865, 6.717644240691058] | 936 | [0.0047460438250519574, 0.014224019655021554] | 3 |
| 103 | 18 | 0 | 8.503205128205128 [7.906005852269184, 9.131745224820522] | 936 |  | 0 |
| 103 | 18 | 1 | 8.503205128205128 [7.874124414725297, 9.104342197035745] | 936 | [-0.0015604642956635634, 0.0021796155788311603] | 0 |
| 103 | 18 | 2 | 5.161324786324786 [4.8515376458112405, 5.457030571737214] | 936 | [0.03702170266646946, 0.055431160007587056] | 2 |
| 103 | 18 | 3 | 5.161324786324786 [4.875645458399731, 5.453507095425894] | 936 | [0.038437984524202856, 0.056899512639366684] | 3 |

#### Reference constant and standard AP comparison

The reference constant below is fitted post hoc to test prevalence, p×(1−p), solely as an audit reference. It is not a trained deployment baseline. Standard AP here is an audit comparison, not the originally reported custom AUPRC.

| Seed | Day | Tier | Test event rate | Test-prevalence constant Brier | sklearn average precision |
| --- | --- | --- | --- | --- | --- |
| 97 | 10 | 0 | 0.5259259259259259 | 0.2493278463648834 | 0.8483171738899342 |
| 97 | 10 | 1 | 0.5259259259259259 | 0.2493278463648834 | 0.8483171738899342 |
| 97 | 10 | 2 | 0.5259259259259259 | 0.2493278463648834 | 0.8483171738899342 |
| 97 | 10 | 3 | 0.5259259259259259 | 0.2493278463648834 | 0.8483171738899342 |
| 97 | 14 | 0 | 0.5259259259259259 | 0.2493278463648834 | 0.8483171738899342 |
| 97 | 14 | 1 | 0.5259259259259259 | 0.2493278463648834 | 0.8483171738899342 |
| 97 | 14 | 2 | 0.5259259259259259 | 0.2493278463648834 | 0.8633178922522239 |
| 97 | 14 | 3 | 0.5259259259259259 | 0.2493278463648834 | 0.8483171738899342 |
| 97 | 18 | 0 | 0.5259259259259259 | 0.2493278463648834 | 0.8483171738899342 |
| 97 | 18 | 1 | 0.5259259259259259 | 0.2493278463648834 | 0.8483171738899342 |
| 97 | 18 | 2 | 0.5259259259259259 | 0.2493278463648834 | 0.8883241965927712 |
| 97 | 18 | 3 | 0.5259259259259259 | 0.2493278463648834 | 0.8886506559248355 |
| 101 | 10 | 0 | 0.5074074074074074 | 0.2499451303155007 | 0.8197558372613133 |
| 101 | 10 | 1 | 0.5074074074074074 | 0.2499451303155007 | 0.8197558372613133 |
| 101 | 10 | 2 | 0.5074074074074074 | 0.2499451303155007 | 0.8197558372613133 |
| 101 | 10 | 3 | 0.5074074074074074 | 0.2499451303155007 | 0.8197558372613133 |
| 101 | 14 | 0 | 0.5074074074074074 | 0.2499451303155007 | 0.8197558372613133 |
| 101 | 14 | 1 | 0.5074074074074074 | 0.2499451303155007 | 0.8197558372613133 |
| 101 | 14 | 2 | 0.5074074074074074 | 0.2499451303155007 | 0.8197558372613133 |
| 101 | 14 | 3 | 0.5074074074074074 | 0.2499451303155007 | 0.8197558372613133 |
| 101 | 18 | 0 | 0.5074074074074074 | 0.2499451303155007 | 0.8197558372613133 |
| 101 | 18 | 1 | 0.5074074074074074 | 0.2499451303155007 | 0.8317522873049641 |
| 101 | 18 | 2 | 0.5074074074074074 | 0.2499451303155007 | 0.8779053367130706 |
| 101 | 18 | 3 | 0.5074074074074074 | 0.2499451303155007 | 0.88755981379062 |
| 103 | 10 | 0 | 0.5064814814814815 | 0.24995799039780525 | 0.8088978037989553 |
| 103 | 10 | 1 | 0.5064814814814815 | 0.24995799039780525 | 0.8088978037989553 |
| 103 | 10 | 2 | 0.5064814814814815 | 0.24995799039780525 | 0.8088978037989553 |
| 103 | 10 | 3 | 0.5064814814814815 | 0.24995799039780525 | 0.8088978037989553 |
| 103 | 14 | 0 | 0.5064814814814815 | 0.24995799039780525 | 0.8088978037989553 |
| 103 | 14 | 1 | 0.5064814814814815 | 0.24995799039780525 | 0.8088978037989553 |
| 103 | 14 | 2 | 0.5064814814814815 | 0.24995799039780525 | 0.8295663197025093 |
| 103 | 14 | 3 | 0.5064814814814815 | 0.24995799039780525 | 0.8291854309665885 |
| 103 | 18 | 0 | 0.5064814814814815 | 0.24995799039780525 | 0.8088978037989553 |
| 103 | 18 | 1 | 0.5064814814814815 | 0.24995799039780525 | 0.8088978037989553 |
| 103 | 18 | 2 | 0.5064814814814815 | 0.24995799039780525 | 0.8740072654533065 |
| 103 | 18 | 3 | 0.5064814814814815 | 0.24995799039780525 | 0.8747332788439368 |

### Subgroups and threshold sweeps

The four saved confidence intervals per configuration are reported exactly as stored in results.json. This audit independently refitted the selected predictors and reproduced nine point statistics per configuration; it did not independently rerun all bootstrap intervals or candidate-selection intervals. Identical point models can have slightly different saved interval endpoints because the bootstrap seed includes the requested tier. The current results have no AUROC below 0.5; minimum is 0.8330652270100257. The largest Brier is 0.16443106007628275, and every selected result is at least as good as its Tier 0 counterpart on Brier in these runs. This is an observed synthetic outcome, not a guaranteed consequence of validation selection.

The attached [subgroup_false_alarm_rates.csv](subgroup_false_alarm_rates.csv) includes all 324 archetype rows with FP/negative counts and saved full-precision rates. No subgroup clinical-validity claim follows from these simulated categories. An undefined rate is left undefined when no negative cycle exists.

[threshold_tradeoff_points.csv](threshold_tradeoff_points.csv) includes all 396 saved points: 36 configurations × 11 thresholds from 0.05 to 0.95. It includes each threshold, sensitivity, PPV, FP/all-cycle rate and nominal day-35 lead, with counts. These held-out sweeps are descriptive and must not be used to choose a deployed threshold afterward.

Bootstrap intervals use 1,000 patient-resamples, retaining all sampled patient cycles. Validation gain intervals use 500 such resamples. These intervals describe resampling within a fixed generator and split; they do not capture uncertainty about whether the generator represents people.



Illustrative pooled subgroup view for day 18 / Tier 2 (audit-derived; no safety filtering):

| Archetype | People | Cycles | False flags / negative cycles | False-positive rate |
| --- | --- | --- | --- | --- |
| PMOS_A | 63 | 378 | 27/36 | 0.75 |
| PMOS_B | 60 | 360 | 29/39 | 0.7435897435897436 |
| PMOS_C | 60 | 360 | 73/337 | 0.2166172106824926 |
| PMOS_D | 57 | 342 | 30/34 | 0.8823529411764706 |
| contraception | 57 | 342 | 51/310 | 0.16451612903225807 |
| early_menarche | 60 | 360 | 54/330 | 0.16363636363636364 |
| healthy_regular | 60 | 360 | 45/343 | 0.13119533527696792 |
| healthy_variable | 63 | 378 | 59/107 | 0.5514018691588785 |
| thyroid_mimic | 60 | 360 | 35/41 | 0.8536585365853658 |

### Dashboard-only numbers

The visible cohort has 36 records: 22 generated positives and 14 negatives. Thirteen records trigger abstention: four thyroid flags, four contraception flags, four age/early-menarche flags and one completeness flag. Thus 23 records remain non-abstaining; the displayed abstention rate rounds 13/36 to 36%.

At day 14 the Tier 2 fixed scores range 0.15484532849776414…0.3243682194521506, so none reaches 0.50. Tier 1 also produces no eligible alert. Tier 0 produces eight budgeted alerts after abstention. These are not the fitted benchmark's validation-threshold operating points.

The complete risk–coverage arrays, score distributions and alert counts are in [dashboard_statistics.json](dashboard_statistics.json), including each tier. In the default Tier 2 diagnostic, the final included subset contains 23/36 records and has selective error 16/23. That is a small-cohort display calculation, not a held-out fitted-model performance estimate.

## 8. Every abstention and safety rule

| Rule input | Condition | Message/reason | Actual dashboard source |
|---|---|---|---|
| tsh_abnormal | true | Thyroid result outside simulated reference flag | Known thyroid_mimic archetype |
| prolactin_abnormal | true | Prolactin result outside simulated reference flag | Always false in current display |
| hormonal_contraception | true | Hormonal contraception | Known contraception archetype |
| age / early_post_menarche | age<18 OR early-post-menarche true | Age or early post-menarche condition | Assigned safety age 17 and flag for early_menarche; other safety ages 29 |
| pregnant / postpartum / breastfeeding | any true | Pregnancy-related state | Always false in current display |
| perimenopausal | true | Perimenopausal age band | Always false in current display |
| wear_completeness | strictly <0.75 | Wear-time completeness below threshold | Finite temperature count among initial 14 nights |

The same temperature-completeness gate is used for all selected display tiers, including calendar-only Tier 0. At day 14, at least 11/14 observed temperatures pass; 10/14 fail. Exactly 0.75 passes the general rule. No interval-width rule, both-label classification-set rule, score-confidence threshold, out-of-distribution detector or uncertain-date rule triggers abstention.

In the patient view, abstention replaces the two risk metric panels with a banner/withheld state and prevents alert selection. It does not stop computing the score, hide the cohort table's score, disable what-if ranges, remove the ovulation-day interval or suppress the generated explanation. AppTest reproduced both a visible cohort score and a what-if range for an abstaining record. Therefore “prediction is withheld” is only partially enforced in the current UI.

The guard defaults missing age to 99 and missing completeness to 1.0, and absent Boolean flags act false. A record with missing safety information can pass rather than abstain. There is no validated clinical policy, lab-reference conversion or physical-unit check behind these flags.

apply_alert_budget() groups by patient/cycle, excludes abstaining rows, retains scores ≥0.50 and selects the highest score, up to one per cycle. Ties keep earlier input order. The app computes days 10/14/18 together and chooses a winner using all three snapshots; this is an offline budget demonstration with possible future-snapshot lookahead, not an online alert scheduler.

The main evaluation does not call the abstention guard or apply_alert_budget(). Its metrics are per snapshot, including all test archetypes. They do not establish the end-to-end safety/one-alert policy's performance.

Evidence: [src/safety.py:3–15](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/safety.py:3>); [src/alerts.py:3–15](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/src/alerts.py:3>); [app.py:219–235](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/app.py:219>), 290–318, 395–411 and 491–522; [scripts/run_eval.py:50–75](</Users/kushagragupta/Documents/New project/CycleTwin_VIT/scripts/run_eval.py:50>), 121–141.

## 9. Implementation status: working versus illustrative versus absent

| Component | Status | Exact boundary |
|---|---|---|
| Synthetic generator, patient split, engineered features | Working, simulated | Reproducible arrays and labels; no real cohort |
| Logistic fitting/calibration/validation fallback | Working, fitted | Benchmark pipeline; selected models reproduce saved point metrics |
| Saved results, README table, SVG figures | Working | Descriptive synthetic benchmark |
| Deployed fitted patient predictor / model files | Missing | Dashboard does not load learned weights; no serialized original models |
| Overview/Cohort/Patient/Method and guided demo | Working | AppTest-rendered; no browser visual audit in this task |
| Cohort/patient score | Working, heuristic/hardcoded coefficients | Different inputs and calibration from fitted tiers |
| Calendar ovulation-day estimator evaluation | Incomplete integration | Benchmark records lack the helper's expected history field |
| Patient day estimate follows tier selector | Bug | UI always initializes day estimate with Tier 2 |
| Explicit abstention helper | Working rule code | Supported flags are tested; UI withholding remains incomplete |
| Conformal ranges / label sets | Working illustration | No benchmark coverage evaluation; calibration mismatch for selected tiers |
| Reproductive/metabolic twin | Working simulation | No patient fitting, filtering or use in scored benchmark |
| CGM panel | Working synthetic display | No evaluated E2 forecast; line downsampled |
| What-if scenarios | Working, fixed multipliers | No causal training, twin rerun or validated intervention effect |
| Alert budget/session log | Working demonstration | Offline snapshot selection; no notifications or durable storage |
| Apple XML adapter | Working limited parser | No imported-data forecasting; raw upload written to a fixed temporary path |
| Generic CSV adapter | Function exists | No current upload widget or predictor link |
| Explanation/summary text | Deterministic templates | Not faithful model-attribution explanations; no runtime LLM |
| Public repository and CI | Working | Audited commit's CI succeeded; 13 local unit tests passed |
| Architecture/pitch PDF and PPTX | Files exist, stale content | Current models/EHR/results are not consistently represented |
| Video | Scripts exist | Actual recording remains a human deliverable |
| External validation, robustness, clinical deployment | Missing/planned | No evidence yet |

## 10. Research validity and audit findings

### High-priority scientific/reporting gaps

1. **Synthetic generator recovery is not clinical prediction.** Labels and informative temperature/heart-rate patterns are produced by shared assumptions. There is no independent ovulation reference, endocrine assay or prospective clinical cohort.
2. **Fitted benchmark and dashboard are different predictors.** Displayed heuristics cannot inherit the benchmark AUROC/Brier or its calibration. A score beside a strong model card can otherwise be misread.
3. **The test set is not a demonstrably untouched final holdout.** Git already contains seeds 97/101/103 results in e43ea93. Later commits fit new models, add EHR draws and change the calendar history window/fallback protocol while continuing to evaluate these seeds. In particular, d6314fb changes history from all preceding cycles to the latest three after previous current-seed results existed. The current code uses validation for its explicit selections, but the historical claim “test evaluated once after a fully frozen process” is unsupported. A genuinely fresh final evaluation needs frozen code and new untouched seeds, and still would be synthetic only.
4. **Calendar ovulation-day MAE is a fallback MAE.** The classifier's calendar feature is fitted correctly from prior cycle indices, but the day-estimation helper never receives that derived field in the evaluation.
5. **UI tier/day mismatch remains.** Scores change with the tier while the day estimate/band uses a Tier 2 calculation initialized earlier.
6. **Abstention is incomplete.** Raw table scores and what-if ranges still expose a withheld record's heuristic output.
7. **Saved custom AUPRC is tie-sensitive.** It is not the standard threshold-grouped AP computation; the full comparison is exported without overwriting results.
8. **One-alert and lead-time claims need qualification.** Evaluation metrics do not apply the longitudinal budget, and day-35 lead is a constant snapshot distance, not observed clinical early-warning time.
9. **EHR-lite is oracle-adjacent.** Internal label-generating parameters are available to Tier 3. The age/BMI/history draws are also simulated, not independent EHR measurements.

### Further validity and integration limitations

- The classifier does not directly use current-cycle truth labels or ovulation_day as feature columns; the imputer/scaler fit on train and patient IDs are separated. These are genuine protections, but they do not remove simulator dependence or the development-history concern.
- The benchmark trains on a mixed phenotype population, including scenarios that the dashboard withholds. Reported performance is not PMOS-only, nor performance conditional on passing safety gates.
- Fixed cycle starts are spaced 38 days while cycle_length can be 22…55. Adjacent records can be temporally inconsistent or overlap. Treating the preceding cycle index's full length as already known is an engineering assumption, not proof of real-time availability.
- Logged start errors do not propagate through a calendar-aligned resampling pipeline; features are sliced directly by generated array position. This understates some real input-alignment difficulties.
- Later snapshots can include a post-ovulation signal for already-ovulated negative cycles. This partly tests recognition of an inserted completed-event pattern, not solely forecasting before any event occurs.
- Steps and sleep are drawn independently of the target; early wearables are weak by design. Strong calendar persistence can dominate a within-generator benchmark.
- One validation set is reused for calibration, fallback selection and F1 selection. The gain bootstrap has no multiple-comparison adjustment. This is an exploratory procedure, not a prospectively validated clinical operating point.
- “Best tier” on Overview is chosen descriptively by held-out Brier among displayed sensor tiers at the latest snapshot. This is acceptable as a labelled comparison but must not be presented as an independently confirmed deployment-selection rule.
- Confidence-interval envelopes across seeds are not a confidence interval for their mean. The audit gives each saved seed interval separately.
- The class conformal calibration uses one-cycle Tier 2 records; the UI can apply it to Tier 0/1 scores and second-cycle display records without recalibration. Marginal coverage has not been demonstrated under this use.
- The interval excludes absent-ovulation cases from its calibration, yet the UI can display a day range for every record. An anovulatory outcome has no true ovulation day to place inside that range.
- The period-start chart marker is assigned day 1 and is not driven by parsed menstrual events. The temperature line drops missing values and connects remaining points across gaps; markers expose missing nights, but the line visually bridges them.
- The CGM label says 15-minute samples while the plotted series is every 120 minutes; the metric uses full samples. The two are easy to confuse.
- Twin timing, coverline timing and generator truth can disagree; they come from different calculations. No filtering/calibration forces them to describe one person's physiology.
- explain_state() uses raw, differently scaled values as if they were contributions, including values ignored by the selected heuristic. It should be described as a template about available signals rather than a faithful explanation of the selected model.
- XML inputs have limited validation: repeated quantities overwrite, other-unit conversion is absent, NaNs can pass through, and malformed data can raise errors. No wearable quality contract is enforced for imported records.
- The raw uploaded XML is written to /tmp/cycletwin_synthetic_upload.xml and is not deleted by this code. A common path can collide across sessions. The mock consent receipt is not a privacy/compliance mechanism. The README's aggregate-only wording does not fully describe this implementation.
- The original fitted models and per-record predictions were not persisted. The audit has refitted evidence, not recovered original weights. There is no clinical model governance or monitoring stack.
- Main numerical libraries are pinned, but Python differs between the inspected local environment and CI, and transitive dependencies are not fully locked. The current reproduction is strong evidence for this environment, not a promise of byte-identical execution everywhere.

### Stale documents and competition artifacts

Both pitch PDF and PPTX still contain old Tier 2 day-14 values: seed 97 AUROC 0.637/Brier 0.306; seed 101 AUROC 0.638/Brier 0.316; seed 103 AUROC 0.663/Brier 0.309. These describe a historical fixed-score version, not current results.json. Slides also describe neutral Tier 0, RHR-only Tier 1, unfused other wearables, unevaluated EHR and planned CGM/EHR tier numbering that conflicts with the fitted implementation.

The architecture diagram still says EHR is not implemented/evaluated. docs/architecture.md and docs/tripod_ai.md retain old “simple/fixed score” descriptions. docs/assumptions.md mixes benchmark and dashboard formula descriptions; its Tier 2 wording can imply an additive wearable model even though forecast() replaces the RHR expression.

The presentation-finalization logs certify structural package checks only. Their own claim boundary says slide text/model values were not inspected; a passed package check does not verify science. The video scripts are newer, but the previous calendar/day-estimate explanation should be qualified by the integration findings above.

No production code was changed during this audit. The gaps are findings, not silently fixed assumptions.

## 11. Judge-friendly explanation and one exact illustrative example

**Truthful short explanation:** “CycleTwin is a synthetic experiment in cycle-by-cycle early-warning workflows. A fitted benchmark tests whether calendar and wearable-style signals recover a generated late/absent-ovulation label. An interactive dashboard separately demonstrates missing-data displays, safety rules, uncertainty ranges, a simplified twin and a one-alert budget. It neither diagnoses PMOS nor validates ovulation prediction in people.”

### Existing generated example: s223-p0002, displayed cycle 2

This is an illustrative synthetic PMOS_A record, not a real woman. Its preceding generated cycle length is 42 days. Twelve of the initial fourteen temperature observations are present. The generated age is 18, although the dashboard safety code assigns this archetype age 29.

| Patient | Tier | Heuristic score | Withheld | UI day estimate | Helper day if selected tier used | Generator truth day/event | UI class set / day band |
| --- | --- | --- | --- | --- | --- | --- | --- |
| s223-p0000 | 0 | 0.3407396115486146 | False | 24 | 15 | 15/0 | [0, 1] / [12, 36] |
| s223-p0000 | 1 | 0.45770973369809254 | False | 24 | 15 | 15/0 | [0, 1] / [12, 36] |
| s223-p0000 | 2 | 0.2645316849625668 | False | 24 | 24 | 15/0 | [0, 1] / [12, 36] |
| s223-p0002 | 0 | 0.7109495026250039 | False | 24 | 28 | 36/1 | [0, 1] / [12, 36] |
| s223-p0002 | 1 | 0.43171154944476553 | False | 24 | 28 | 36/1 | [0, 1] / [12, 36] |
| s223-p0002 | 2 | 0.242495156722727 | False | 24 | 24 | 36/1 | [0, 1] / [12, 36] |
| s223-p0026 | 0 | 0.24232036099629517 | True | 24 | 11 | 14/0 | [0, 1] / [12, 36] |
| s223-p0026 | 1 | 0.4723002330934904 | True | 24 | 11 | 14/0 | [0, 1] / [12, 36] |
| s223-p0026 | 2 | 0.30052396961330935 | True | 24 | 24 | 14/0 | [0, 1] / [12, 36] |

For p0002 the exact available day-14 sensor means are: RHR offset -0.6243573484637694, HRV offset 0.26296298973514165, steps 5157.991929058873, sleep hours 7.17311696018888. The full 14-entry raw temperature array, including nulls at missing nights, is in [illustrative_examples.json](illustrative_examples.json). Tier 0 uses none of these sensor means.

The UI's Tier 0 score comes from sigmoid(0.12×(42−34.5)) = 0.7109495026250039. It crosses the demo's 0.50 cutoff and is not blocked by its assigned safety flags. It is not the probability from a saved fitted classifier.

The current UI still shows day 24 and [12,36] because it used the Tier 2 fallback estimate. Calling the Tier 0 calendar helper with the available history would return 28. The independent twin returns day 41. The generator's ground-truth ovulation day is 36 and event=1. These differences are useful to explain the prototype's boundaries; none should be replaced by an invented “correct” clinical prediction.

The classification label set is [0,1], meaning the conformal illustration includes both outcomes. Adding the alert selects one stored synthetic alert for this cycle; repeated additions are blocked. For this fixed Tier 0 score, equal-score snapshots lead to the earlier input day being selected.

Selecting Daily walk produces the score multiplied by 0.75…0.98. It is an assumption-only range, not evidence that walking changes that person's ovulation outcome. This record does not get a CGM panel because its index is not divisible by four.

For the CGM illustration, switch to s223-p0000: the toy metabolic stream has 2,688 underlying points, 336 plotted points and 83 excursion windows out of 84 simulated meals, or 0.9880952380952381. A “healthy_regular” reproductive archetype and this toy glucose result are not a clinical metabolic classification.

### What judges actually see

- Overview: generated-data badge, plain purpose, workflow, runtime synthetic benchmark chips, limits and a guided-demo button.
- Cohort: generated records, heuristic score, archetype, completeness, review badges and a small display-cohort diagnostic.
- Patient: selected record, heuristic score or partial withholding, temperature/interval display, separate twin and selected CGM, assumption-based scenarios and session log.
- Method: saved fitted results, all tier/snapshot means, selected-tier seed details and limitations.
- Guided route: p0000 for the normal display, p0026 for the assigned abstain rule, p0002 at Tier 0 for an eligible alert.

Do not tell judges that the live patient score uses the fitted model, that the twin improves AUROC, that uploaded XML is scored, that hormone levels are inferred, or that the what-if range predicts treatment response.

## 12. Comprehensive input → source → processing → output map

| Input | Source | Processing | Model/rule | Output | Evaluation evidence |
|---|---|---|---|---|---|
| Prior cycle lengths | Generated completed-cycle fields | Mean of up to three preceding indices | Fitted Tier 0 | Binary synthetic event probability | Held-out benchmark; history-value unit test |
| RHR/HRV offsets, steps, sleep | Generated daily arrays | Prefix means, train median imputation/scaling | Fitted Tier 1 candidate; validation fallback | Binary synthetic event probability | Held-out results, often fallback |
| Temperature offsets/missingness | Generated nightly array | Observed change and observation fraction | Fitted Tier 2 candidate | Binary synthetic event probability | Held-out results and saved CIs |
| IR, androgen, age, BMI, family history | Generated static internals; mirrored in EHR CSV | Numeric features, imputation/scaling | Fitted Tier 3 candidate | Oracle-adjacent event probability | Internal synthetic check only |
| Generated prior length | Separate display cohort | Hand-set sigmoid of calendar mean | Dashboard Tier 0 heuristic | Demo score | No fitted performance transfer |
| Generated RHR | Separate display cohort | Hand-set sigmoid of prefix mean | Dashboard Tier 1 heuristic | Demo score | Display diagnostic only |
| Generated temperature | Separate display cohort | Hand-set sigmoid of temperature change | Dashboard Tier 2 heuristic | Demo score | Display diagnostic only |
| Prior length or temperature | Generated records | Calendar-minus-14 or coverline; day+10 fallback | Ovulation-day helper | Day estimate | MAE saved, with integration/indexing limitations |
| Calibration labels and heuristic scores | Seed 211, 240 cycles | Finite-sample nonconformity quantile | Split-conformal helper | Class set [0], [1], [0,1] or possibly empty | No held-out coverage result |
| Calibration true/estimated ovulation days | Seed 211, 203 ovulatory cycles | Absolute-error quantile | Split-conformal helper | Clipped day interval | No coverage validation for UI use |
| Known archetype flags and temperature completeness | Generated/assigned UI fields | Explicit Boolean/threshold checks | Abstention rules | Banner, some withheld panels, alert exclusion | Unit tests; no safety-performance benchmark |
| IR and androgen | Simulator internals | Daily growth/threshold/lag updates | Reproductive twin | Follicle/progesterone-like/temp/RHR arrays and toy event day | Determinism/positivity/monotonicity tests only |
| IR, toy event day and meals | Simulator internals | Euler glucose/insulin/meal dynamics | Metabolic twin | Simulated CGM and excursion counts | Sanity/reverse-coupling tests; no E2 evaluation |
| Scenario name and heuristic score | UI selection plus current display score | Fixed multiplication | What-if rules | Assumption-only score range | No causal/intervention validation |
| Snapshot scores and abstain flags | Dashboard forecasts | Group by patient/cycle, choose largest eligible score | Offline alert-budget rule | At most one selected log entry | Unit/UI duplicate-protection checks; no longitudinal benchmark |
| XML HealthKit-shaped fields | Synthetic fixture or local upload | Limited streaming parser | Adapter only | Daily dictionary and cycle-start/count display | One synthetic round-trip fixture; not scored |
| Generic CSV columns | Caller-supplied file to standalone reader | Float parsing and start flag | Unconnected adapter function | Daily dictionary | No end-to-end imported-data prediction evaluation |
| Raw temperature/RHR summaries | Selected generated record | Rank absolute raw values, insert names in text | Deterministic explanation template | Text summary | Not faithful model attribution |
| Displayed chart arrays | Current generated data or display diagnostic | Means, changes, counts, extrema | Deterministic chart templates | Plain-language numeric descriptions | Computation/rendering checks; no LLM |

## Configuration, build, publication and deliverable evidence

- Numerical/application dependencies are pinned in requirements.txt: NumPy 2.0.2, pandas 2.3.3, Streamlit 1.50.0, Altair 5.5.0, scikit-learn 1.6.1, SciPy 1.13.1, joblib 1.5.3 and threadpoolctl 3.7.0. The inspected local runtime is Python 3.9.6 on macOS 15.8 ARM64. The full installed provenance and source SHA-256 hashes are in [environment_and_provenance.json](environment_and_provenance.json). This audit used that installed environment; it did not create another clean venv. README describes a previous clean rerun; the current CI log independently shows requirements installation and unit tests on Python 3.11, not a complete benchmark rerun in CI.
- Makefile all runs EHR export, evaluation, README-table regeneration and figure generation. demo-apple writes the synthetic XML then launches Streamlit; test runs unittest discovery. No build step trains a model for the dashboard.
- .streamlit/config.toml is a light theme with primary #0e766e, background #f7faf9, secondary #ffffff, text #18313d and a system sans-serif setting. app.py provides additional local CSS. No downloaded font, runtime language-model SDK or external inference service is used.
- .github/workflows/ci.yml installs requirements on Ubuntu/Python 3.11 and runs unittest on push/pull request. It does not run the full benchmark, validate medical claims, inspect screenshots or audit deck metrics. The current published run succeeded; the log is preserved.
- The public GitHub repository is https://github.com/kushagragupta2005/CycleTwin_VIT. MIT LICENSE and the README AI-coding-assistance disclosure exist. Public-source reachability was checked during the audit; this says nothing about clinical approval.
- deliverables/CycleTwin_VIT_architecture_v4.pptx and its PDF contain one slide/page. deliverables/CycleTwin_VIT_pitch_deck_v8.pptx and PDF contain 14 slides/pages. Original PPTX/PDF text and .ppt_build validation logs were inspected; the older candidate packages are build artifacts, not extra studies. See the stale-science findings above.
- docs/video_script_20min.md and docs/video_script_3min.md exist. No recorded video is present in the inspected repository, and README states the human recording remains outstanding.
- docs/screenshots contains the five existing screenshots and its README. Their existence is not a current browser visual-verification result. This audit did not recapture them or repeat the earlier accepted static-width check.
- All substantive source modules, scripts, tests, configs, research docs, tracked data and current result/deliverable families were inspected. [file_inventory.json](file_inventory.json) lists the local files and byte counts, including ignored build/fixture artifacts. No original saved learned-model artifact was found.

For reproducibility of this audit's evidence, activate the existing pinned environment and run `python docs/audit_2026-10-20/reproduce_audit.py`. It writes audit derivatives only. `verify_dashboard.py` exercises the four views and three guided steps with AppTest. The full report is an audit snapshot, not a change to production behavior.

## Audit execution and completeness

The main reconstruction verified 36 configurations and 324 saved scalar fields, all 324 saved archetype false-alarm rates, and exported 396 saved trade-off points. The original current results.json and source files were left untouched. No serialized original model was found. Thirteen unit tests passed in the installed pinned environment; the audited published commit's GitHub CI succeeded. Seven AppTest view/step renders passed; focused interactions reproduced the reported withholding and selected-tier day-estimate gaps.

No browser screenshots, clinical study, latency benchmark or memory benchmark were produced. A passed test checks software behavior, not clinical usefulness. All raw exact evidence is alongside this report.
