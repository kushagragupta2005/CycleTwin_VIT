"""Simplified, non-clinical two-axis twin using NumPy Euler updates."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class TwinParameters:
    follicle_base_growth: float = 0.065
    androgen_growth_effect: float = 0.025
    insulin_growth_effect: float = 0.012
    lh_threshold: float = 1.0
    luteal_temp_rise_c: float = 0.20
    luteal_insulin_sensitivity_drop: float = 0.05
    glucose_base_mg_dl: float = 95.0
    glucose_clearance_per_hour: float = 0.020
    insulin_decay_per_hour: float = 0.10
    meal_decay_per_hour: float = 0.40

def simulate_reproductive_axis(z_ir: float, androgen: float, days: int = 55,
                               kappa: float = 1.0, seed: int = 0):
    """Follicle maturation -> LH-threshold event -> lagged progesterone-like state."""
    p=TwinParameters(); rng=np.random.default_rng(seed)
    follicle=np.zeros(days); prog=np.zeros(days); temp=np.zeros(days); rhr=np.zeros(days)
    ov_day=-1
    for d in range(days):
        if d:
            growth=p.follicle_base_growth-p.androgen_growth_effect*max(androgen,0)-p.insulin_growth_effect*max(z_ir,0)*kappa
            growth=max(0.01,growth+rng.normal(0,.003))
            follicle[d]=follicle[d-1]+growth
            if ov_day<0 and follicle[d]>=p.lh_threshold: ov_day=d+1
        if ov_day>0 and d+1>=ov_day:
            prev=prog[d-1] if d else 0.0
            prog[d]=prev+0.5*(1.0-prev)
        lagged_prog=prog[d-2] if d>=2 else 0.0
        temp[d]=36.4+p.luteal_temp_rise_c*lagged_prog+rng.normal(0,.02)
        rhr[d]=62+1.1*prog[d]+rng.normal(0,.6)
    return {"follicle":follicle,"progesterone_like":prog,"temperature_c":temp,
            "resting_hr_bpm":rhr,"ovulation_day":ov_day}

def simulate_metabolic_axis(z_ir: float, ovulation_day: int, days: int = 28,
                            seed: int = 0, step_minutes: int = 15,
                            luteal_coupling: bool = True):
    """Bergman-style glucose/insulin states with a meal compartment and luteal coupling."""
    if step_minutes <= 0 or 60 % step_minutes: raise ValueError("step_minutes must divide one hour")
    dt=step_minutes/60.0; per_day=24*60//step_minutes; n=days*per_day
    rng=np.random.default_rng(seed); p=TwinParameters()
    glucose=np.empty(n); insulin=np.empty(n); x=np.empty(n); meal=np.zeros(n)
    G=p.glucose_base_mg_dl; I=10.0; X=0.0; appearance=0.0
    meal_ix=[]
    for d in range(days):
        for hr in (8,13,19):
            ix=d*per_day+hr*per_day//24+int(rng.integers(-1,2))
            meal_ix.append(ix); meal[ix]=float(rng.lognormal(np.log(28),.25))
    for t in range(n):
        day=t//per_day
        if meal[t]>0: appearance+=meal[t]
        appearance += dt*(-p.meal_decay_per_hour*appearance)
        luteal=ovulation_day>0 and day>=ovulation_day
        delta=p.luteal_insulin_sensitivity_drop*float(luteal and luteal_coupling)
        sens=(1-delta)/(1+0.2*max(z_ir,0))
        dI=-p.insulin_decay_per_hour*(I-10.0)+.04*appearance
        dX=-.05*X+.0015*max(I-10.0,0)*sens
        dG=-p.glucose_clearance_per_hour*(G-p.glucose_base_mg_dl)-X*(G-p.glucose_base_mg_dl)+appearance
        I=max(0.0,I+dt*dI); X=max(0.0,X+dt*dX); G=float(np.clip(G+dt*dG,40,300))
        glucose[t]=G+rng.normal(0,5); insulin[t]=I; x[t]=X
    return {"glucose_mg_dl":np.clip(glucose,40,300),"insulin_state":insulin,
            "insulin_sensitivity_state":x,"meal_indices":meal_ix,"step_minutes":step_minutes}

def coupling_sweep(z_ir: float, androgen: float, kappas=(0,.5,1,2), days: int = 55):
    return {float(k):simulate_reproductive_axis(z_ir,androgen,days,kappa=float(k))["ovulation_day"] for k in kappas}
