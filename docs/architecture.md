# Architecture

Synthetic generator -> patient-level split -> tiered feature extraction -> simple cycle forecast -> risk-ranked dashboard.

The export adapter is a separate input path: synthetic Apple Health-shaped XML -> daily canonical table -> forecast. Generator ground truth remains separate from adapter inputs. A shared latent can connect reproductive and metabolic axes in later work; current released evaluation covers only the reproductive synthetic axis.
