"""Single fitted inference path. Load only repository-generated, trusted joblib files."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np

from src.features import record_features

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=4)
def _card(path, modified):
    return json.loads(Path(path).read_text())


def model_card():
    path = ROOT / "models/model_card.json"
    return _card(str(path), path.stat().st_mtime_ns)


@lru_cache(maxsize=64)
def _load(path, modified, expected_hash):
    path = Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError("Model artifact does not match its model card")
    return joblib.load(path)


def model_key(seed, day, tier):
    return f"seed_{int(seed)}_day_{int(day)}_tier_{int(tier)}"


def predict(record, day, tier, *, seed=97):
    """Return a synthetic fitted probability and exact additive logit evidence.

    Safety is an explicit caller gate; this low-level function is also used by evaluation.
    Contributions sum to the base decision score. Multiplying by the fitted Platt
    coefficient gives additive contributions to the final calibrated logit.
    """
    meta = model_card()["models"][model_key(seed, day, tier)]
    path = ROOT / meta["artifact"]
    fitted = _load(str(path), path.stat().st_mtime_ns, meta["sha256"])
    x = record_features(record, int(day), meta["selected_tier"])
    imputed = fitted.base.named_steps["impute"].transform(x)
    standardized = fitted.base.named_steps["scale"].transform(imputed)[0]
    lr = fitted.base.named_steps["lr"]
    slope = float(fitted.calibrator.coef_[0, 0])
    contributions = [
        {"feature": name, "raw_value": float(raw) if np.isfinite(raw) else None,
         "imputed_value": float(value), "standardized_value": float(z),
         "coefficient": float(coef), "base_logit_contribution": float(coef * z),
         "calibrated_logit_contribution": float(slope * coef * z)}
        for name, raw, value, z, coef in zip(meta["features"], x[0], imputed[0], standardized, lr.coef_[0])
    ]
    probability = float(fitted.predict_proba(x)[0])
    return {"prob": probability, "threshold": meta["threshold"],
            "flag": probability >= meta["threshold"], "fallback_used": meta["selected_tier"] != int(tier),
            "selected_tier": meta["selected_tier"], "requested_tier": int(tier), "day": int(day),
            "seed": int(seed), "contributions": contributions,
            "base_intercept": float(lr.intercept_[0]),
            "calibrated_intercept": float(slope * lr.intercept_[0] + fitted.calibrator.intercept_[0]),
            "metrics": meta["metrics"], "scope": "synthetic-only; not clinical performance"}
