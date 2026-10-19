# Assumptions

Every parameter below is a literature-informed assumption (verify with clinician). These values configure a synthetic engineering exercise and are not clinical thresholds.

- The simulated cohorts, phenotype labels, physiologic quantities, signal noise, missingness, and all intervention effects are synthetic.
- A cycle is tagged as event E1 when its simulated ovulation is absent or occurs after day 21. The label is synthetic ground truth.
- Cycle-level probabilities are generated from patient-level latent traits and wearable summaries. The simulator does not represent a validated hormone model.
- Daily temperature, resting heart rate, SDNN, steps, and sleep are noisy synthetic observations. Temperature support is deliberately varied; it is not calibrated to a clinical population.
- Alert cutoff 0.50 and maximum one alert per patient-cycle are operational demo settings, not clinical cutoffs.
- Any stated glucose excursion setting is an illustrative simulator setting only.
- PMOS phenotype archetypes and demographic bands are simulation design choices, not diagnostic criteria.
