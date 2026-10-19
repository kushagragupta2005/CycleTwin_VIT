# Jury Q&A

1. **Why synthetic data?** No verified, permissioned cohort is available for this prototype. Synthetic data makes the pipeline reproducible without exposing anyone's health information.
2. **What if the generator is wrong?** Then the reported metrics may not transfer. The generator is an engineering fixture, not a physiological reference.
3. **What does the model predict?** A synthetic cycle-level flag for no ovulation or ovulation after cycle day 21, evaluated at days 10, 14 and 18.
4. **What is not claimed?** No clinical accuracy, diagnostic ability, treatment effect, or usefulness for contraception or conception planning.
5. **Why include sensor tiers?** They make it possible to report which simulated input streams change the score. In G1, tier 1 uses resting-heart-rate offsets; tier 2 adds temperature.
6. **Does the project use CGM?** The dashboard can display synthetic 15-minute CGM windows. There is no evaluated CGM forecast or E2 result.
7. **Is this a digital twin of a patient?** No. The dashboard has a simplified coupled reproductive/metabolic simulator with a shared latent, but it is not calibrated and does not model a real person. It is separate from the evaluated G1 score.
8. **Why not use a language model in the clinical loop?** There is no LLM in the loop. The current dashboard only parses and displays synthetic records.
9. **Why does the evaluator split by patient?** Cycles from one synthetic patient share latent characteristics; keeping them together limits patient leakage.
10. **How should the metrics be read?** As held-out results within three versions of this simulator, with patient-cluster bootstrap intervals. They are not clinical performance estimates.
11. **Why can the event rate be near one half?** The simulator uses a fixed mix of phenotype archetypes and assumptions. That mix is not a prevalence estimate.
12. **Is the temperature rule an ovulation confirmation?** No. It is a simple coverline heuristic over generated data and may be wrong even in the simulator.
13. **Why does the project abstain?** The demo applies explicit flags for thyroid/prolactin results, hormonal contraception, age, pregnancy-related states, perimenopause and incomplete wear. These are simulator rules, not clinically validated policy.
14. **What personal data is in the repo?** None. The included XML is synthetic and generated locally.
15. **What would be needed before clinical use?** Clinician co-design, a validated target definition, privacy and governance review, and prospective evaluation on appropriately consented data.
