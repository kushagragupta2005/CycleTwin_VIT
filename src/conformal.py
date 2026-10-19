"""Split-conformal helpers. Coverage claims are marginal, not conditional."""
import math
import numpy as np

def finite_sample_quantile(scores, alpha: float = 0.10) -> float:
    values=np.sort(np.asarray(scores,dtype=float))
    if not len(values): raise ValueError("calibration scores are required")
    rank=min(len(values), int(math.ceil((len(values)+1)*(1-alpha))))
    return float(values[max(0,rank-1)])

def classification_set(probability_positive: float, q: float) -> list[int]:
    p=float(np.clip(probability_positive,0,1))
    labels=[]
    if p <= q: labels.append(0)
    if 1-p <= q: labels.append(1)
    return labels

def calibrate_binary(y_true, p_positive, alpha: float = 0.10) -> float:
    y=np.asarray(y_true,dtype=int); p=np.clip(np.asarray(p_positive,dtype=float),0,1)
    scores=np.where(y==1,1-p,p)
    return finite_sample_quantile(scores,alpha)

def calibrate_ovulation_interval(y_day, estimate_day, alpha: float = 0.10) -> float:
    return finite_sample_quantile(np.abs(np.asarray(y_day)-np.asarray(estimate_day)),alpha)

def ovulation_interval(estimate_day: float, q: float, min_day: int = 1, max_day: int = 60):
    return max(min_day,int(math.floor(estimate_day-q))), min(max_day,int(math.ceil(estimate_day+q)))
