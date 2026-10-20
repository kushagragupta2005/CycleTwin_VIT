# Jury Q&A

All numerical evidence is generated in [claims.json](claims.json). It describes synthetic data and is not clinical performance evidence.

1. **What problem is CycleTwin solving?** It forecasts a generated cycle with late or absent ovulation from calendar and wearable-style inputs. It does not diagnose PMOS.
2. **Why use synthetic data?** No permissioned real cohort is included. Synthetic data permits an inspectable pipeline without exposing health data.
3. **What if the generator is wrong?** Its metrics may not transfer. The generator is an engineering fixture, not a physiology reference.
4. **What is the label?** A generated event: ovulation after the configured cutoff or no generated ovulation. [assumptions.md](assumptions.md) records the rule.
5. **Does PMOS status drive the prediction?** No diagnosis is output. The synthetic cohort includes PMOS and non-PMOS archetypes only as generator context.
6. **How are patients separated?** Train, validation and held-out partitions are by generated patient, so a patient's cycles do not cross partitions.
7. **Why are days 10 and 14 mainly calendar history?** Validation retained the calendar fallback for many early snapshots; temperature evidence has not yet supplied a validated gain. See [claims.json](claims.json).
8. **When do sensors help in this simulation?** The frozen Tier-2 day-18 row reports the intended temperature-assisted comparison.
9. **What is the fitted score?** A train-fitted logistic regression, Platt-calibrated and thresholded using validation data. [eval_plan.md](eval_plan.md) records the separation.
10. **Does the twin drive that score?** No. The reproductive/metabolic illustration is separate from the persisted logistic path.
11. **What is the Bayesian timing posterior?** A separate train-only calendar/static prior with temperature, RHR and HRV likelihoods. Its frozen comparison is in [claims.json](claims.json).
12. **Why can the Bayesian posterior look favorable?** It is evaluated against labels made by the same simulator family. That construction limits its meaning outside the simulator.
13. **What happened to the ovulation-day interval?** Its heuristic day band failed the frozen coverage check. It stays labelled illustrative in the app and README.
14. **What happens under temperature drift?** Frozen synthetic ranking remains similar while calibration degrades materially; the robustness artifact reports both values.
15. **Why are FSH, LH, estradiol and progesterone absent?** Their interpretation depends on cycle day and clinical context. Progesterone can also function as event confirmation, making it inappropriate as a prospective predictor here.
16. **Why use nightly wrist temperature rather than manual morning BBT?** The input is a wearable-shaped nighttime stream with completeness checks; it is not claimed to be equivalent to clinical BBT.
17. **Why are cervical mucus and urinary LH absent?** They are pre-ovulatory signals for a future, consented-data branch; they are not simulated as scored inputs now.
18. **What is EHR-lite?** Generated age, BMI, family history and simulator internals. It is labelled oracle-adjacent because an internal latent contributes to label generation.
19. **Are there real patients or hormone measurements?** No. All records, labels, display personas and assay-like proxies are synthetic.
20. **What is the DPDP stance?** No personal data is bundled. Any future Indian deployment needs a purpose-specific DPDP assessment, consent and governance process; none is complete.
21. **When does the app abstain?** Missing safety information, contraindication-style flags, age-related states and insufficient observed temperature can withhold personal outputs. [assumptions.md](assumptions.md) lists the rules.
22. **What happens after abstention?** The app suppresses score, interval, explanation, sandbox and alert output, then shows the triggering rule.
23. **How is alert fatigue limited?** The frozen policy retains the earliest safe threshold crossing and permits one synthetic alert per cycle.
24. **Are alert rates clinical rates?** No. They are simulator outcomes, with exact frozen counts and denominators in [claims.json](claims.json).
25. **What does the conformal class set mean?** It is a synthetic classification-set check. It does not rescue the failed day band or provide an individual guarantee.
26. **What does the CGM panel show?** Generated glucose for a selected synthetic record. It is not an evaluated glucose forecast.
27. **Is the what-if panel a treatment recommendation?** No. It shows assumption-only input edits and does not estimate causal effects.
28. **What is tested automatically?** The suite covers persisted inference, patient splits, safety withholding, dashboard paths, claims consistency and frozen-artifact protection.
29. **Can results be reproduced?** The pinned requirements support a clean-environment test run; [deploy_streamlit.md](deploy_streamlit.md) records the deployment path.
30. **What is not claimed?** Clinical validity, PMOS diagnosis, hormone inference, contraception or conception guidance, treatment benefit, real-patient performance and a validated digital twin.
