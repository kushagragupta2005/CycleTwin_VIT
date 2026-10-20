"""Synthetic assay-like indices for a clearly labeled post-freeze extension."""
import math
import hashlib
import numpy as np


def mean_one_lognormal(seed, key, cv=0.15):
    """A deterministic independent per-person draw with specified coefficient of variation."""
    sigma=math.sqrt(math.log1p(cv**2));mu=-.5*sigma**2
    digest=hashlib.sha256(f'{seed}:{key}'.encode()).digest()
    rng=np.random.default_rng(int.from_bytes(digest[:8],'big'))
    return float(rng.lognormal(mu,sigma))


def assay_like_features(row, seed, cv=0.15):
    noise_ir=mean_one_lognormal(seed,row['patient']+':ir',cv)
    noise_androgen=mean_one_lognormal(seed,row['patient']+':androgen',cv)
    return np.asarray([math.exp(float(row['ir']))*noise_ir,math.exp(float(row['androgen']))*noise_androgen],dtype=float)
