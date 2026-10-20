# Frozen synthetic robustness extension

This post-freeze extension holds the frozen Tier-2 day-18 models and their validation thresholds fixed. It evaluates the predeclared sweeps in `docs/frozen_protocol.json`: added missing temperature readings, added noise, constant temperature bias, linear device drift, and a generated timing shift on independent synthetic cohorts. It reports AUROC, Brier score, and the fail-closed safety-withhold rate. The results are synthetic sensitivity analyses, not evidence of device robustness or clinical performance.
