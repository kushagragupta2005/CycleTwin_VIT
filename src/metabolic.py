"""Illustrative 15-minute synthetic CGM windows; not a glucose physiology model."""
import numpy as np

def simulate_cgm(seed: int, insulin_resistance: float, days: int = 28, luteal_start: int = 16):
    rng=np.random.default_rng(seed)
    n=days*96
    minutes=np.arange(n)*15
    glucose=np.full(n,98.0+5*max(insulin_resistance,0),dtype=float)
    meals=[]
    for day in range(days):
        for hour in (8,13,19):
            idx=day*96+hour*4+int(rng.integers(-2,3))
            meals.append(idx)
            size=float(rng.lognormal(0,.35))
            amp=(24+10*max(insulin_resistance,0))*size
            span=min(n-idx,12)
            glucose[idx:idx+span]+=amp*np.exp(-np.arange(span)/4)
    glucose[minutes//1440 >= luteal_start]+=3.0
    glucose+=rng.normal(0,7,n)
    return minutes, np.clip(glucose,55,260), meals

def excursion_event(glucose, meal_index, threshold_mg_dl=140, horizon_minutes=120):
    start=max(0,int(meal_index)); end=min(len(glucose),start+horizon_minutes//15+1)
    return bool(np.any(np.asarray(glucose)[start:end] > threshold_mg_dl))
