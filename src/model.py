"""Fixed, transparent synthetic forecasting scores; no fitting or clinical calibration."""
import numpy as np

def sigmoid(x): return 1 / (1 + np.exp(-np.clip(x, -20, 20)))

def forecast(cycle, day: int, tier: int):
    temps = cycle["temperature"][:day]
    t = temps[np.isfinite(temps)]
    thermal = (float(np.mean(t[-4:])) - float(np.mean(t[:min(5, len(t))]))) if len(t) >= 6 else 0.0
    if tier == 0:
        # A neutral period-log-only score until prior-cycle history is available.
        score = -0.04
    elif tier == 1:
        score = .20 * float(np.nanmean(cycle["rhr"][:day]))
    else:
        score = -.9 - 5.0 * thermal
    return float(sigmoid(score - .15))

def estimate_ovulation_day(cycle, day: int, tier: int):
    """Simple temperature coverline estimate; fixed fallback is an assumption."""
    if tier < 2:
        return day + 10
    temps = cycle["temperature"][:day]
    baseline = temps[:min(5, len(temps))]
    base = np.nanmean(baseline)
    if not np.isfinite(base):
        return day + 10
    for ix in range(6, len(temps)-2):
        if np.all(np.isfinite(temps[ix:ix+3])) and np.all(temps[ix:ix+3] > base + .12):
            return max(1, ix)
    return day + 10

