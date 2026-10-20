# CycleTwin 20-minute script

Synthetic research prototype. Not for diagnosis, contraception or conception planning.

Human recording deferred. All project numbers below come from docs/claims.json.

## CycleTwin
Cycle-by-cycle late or absent ovulation research
Team CycleTwin / VIT
A fitted synthetic forecasting workflow with explicit safety gates
Meet Kushi: fictional persona, never performance evidence

## The research problem
Monitoring irregular cycles without claiming a PMOS diagnosis
Target: generated ovulation after the configured cutoff, or generated absence
India context: 7.2% by NIH criteria and 19.6% by Rotterdam criteria
Published prevalence depends on definition. It is not the simulator mixture or model accuracy.

## Meet Kushi
Fictional synthetic persona - not a real patient - not performance evidence.
21 years, year 3 B.Tech
Hostel life, exam-season sleep debt, mother with type 2 diabetes, smartwatch wearer.
Actual generated past lengths: 41, 38, 41, 38, 44, 51 days
Selection uses generator truth and a declared seed, never predicted risk

## Static and dynamic input streams
EHR-lite is implemented and explicitly oracle-adjacent
Static: generated IR latent, androgen, age, BMI and family history
Dynamic: calendar history, RHR, HRV, steps, sleep and temperature
No measured hormone values. The XML parser demonstrates input shape only.

## One fitted prediction path
The dashboard loads the same persisted pipeline used by the benchmark


## Training and selection
Every explicit operating choice uses train or validation data
Patient counts per development seed: train 840, validation 180, test 180
Training medians and scaling, logistic regression, validation Platt calibration
Validation Brier-gain rule selects richer features or calendar fallback
Validation F1 chooses the threshold. Test outcomes never choose that threshold.

## Synthetic development evidence: day 10
Seed means describe the current generator, not clinical forecasting


## Synthetic development evidence: day 14
Seed means describe the current generator, not clinical forecasting


## Synthetic development evidence: day 18
Seed means describe the current generator, not clinical forecasting


## Frozen synthetic evidence: day 10
Reserved seeds, unchanged train/validation choices, one guarded run


## Frozen synthetic evidence: day 14
Reserved seeds, unchanged train/validation choices, one guarded run


## Frozen synthetic evidence: day 18
Reserved seeds, unchanged train/validation choices, one guarded run


## Evidence at the latest sensor snapshot
Predeclared temperature sensor tier, descriptive seed means
Synthetic day 18, Tier 2: AUROC 0.907, Brier 0.117
3,240 synthetic test cycles across 3 frozen seeds
A separate frozen evaluation artifact is available.
Standard average precision and calibration diagnostics are available from stored predictions.

## What the clinician view shows
Decision-support research display
Fitted probability beside its own validation threshold and held-out model evidence
Exact additive feature contributions and explicit imputation
Heuristic day estimate and conditional, illustrative day band
Data-quality ribbon and the reason for any withholding

## Guardrails live
Missing safety information causes abstention
Contraception, thyroid and prolactin flags, age and pregnancy-related states
Early post-menarche, perimenopause and insufficient observed temperature
Withholding removes personal scores, intervals, explanations, sandbox outputs and alerts
The workflow is synthetic and its safety effectiveness has not been clinically evaluated

## The twin and assumption sandbox
Clear boundaries around simulated physiology
Reproductive and metabolic equations generate an illustrative state trajectory
The twin does not affect the logistic score or its reported performance
The sandbox edits invented model inputs. It does not predict a treatment effect
Glucose threshold crossings are simulated counts, not an evaluated glucose forecast

## Where it fails
All declared Kushi scenarios remain visible
Display the fixed scenario seeds with misses, false alarms or withholding unchanged
Different snapshots can fall back to calendar even when sensors are available
A class set containing both outcomes does not identify one result
Robustness, state-estimator and conformal coverage evidence remain separate work

## Validity limits
Synthetic recovery is not prospective evidence in women
Labels and sensor changes share generator assumptions
EHR-lite includes a label-generating internal latent
Old test seeds were reused during development
The current benchmark does not evaluate the complete sequential alert policy

## Reproducible demonstration
Public source, inspectable artifacts and explicit next work
README, model cards and the audit link every claim to evidence
Persisted inference reproduces the benchmark and exposes exact feature calculations
The required video remains a human recording and upload task
Clinical validation, clinician feedback and sim-to-real evaluation remain outstanding

End on limitations. This is a synthetic engineering experiment, not evidence of reliable forecasting in people.
