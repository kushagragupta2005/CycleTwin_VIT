# Simulated assay-like extension

This is a post-freeze extension, separate from the frozen primary endpoint. For each generated person, the code converts the simulator's insulin-resistance latent and androgen load to positive indices using `exp(latent)` and adds an independent mean-one log-normal draw with coefficient of variation 15%. The model is trained, Platt-calibrated and thresholded using train/validation patients; test patients are reported afterward.

The indices are not measured hormone concentrations, do not have clinical units, and retain simulator-internal leakage risk because their sources help define the generated outcome. They are therefore compared with, but cannot validate, the original Tier-3 oracle-adjacent upper-bound reference.
