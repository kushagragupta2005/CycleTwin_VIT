# Architecture

Synthetic generator -> patient-level split -> tiered feature extraction -> simple cycle forecast -> risk-ranked dashboard.

The export adapter is a separate input path: synthetic Apple Health-shaped XML -> daily canonical table -> dashboard. Generator ground truth remains separate from adapter inputs. The dashboard also runs simplified reproductive and metabolic dynamics coupled through a shared synthetic latent, displays an illustrative CGM stream, and shows synthetic-calibration conformal ranges. This twin is not used by the held-out G1 score evaluation and is not clinically calibrated.
