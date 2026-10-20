"""Train/validation-only probability calibration for the synthetic benchmark."""
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class PlattModel:
    def __init__(self):
        self.base = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()),
                              ("lr", LogisticRegression(max_iter=1000, random_state=0))])
        self.calibrator = LogisticRegression(max_iter=1000, random_state=1)

    def fit(self, x_train, y_train, x_val, y_val):
        self.base.fit(x_train, y_train)
        self.calibrator.fit(self.base.decision_function(x_val).reshape(-1, 1), y_val)
        return self

    def predict_proba(self, x):
        return self.calibrator.predict_proba(self.base.decision_function(x).reshape(-1, 1))[:, 1]


def choose_f1_threshold(y_true, probability) -> float:
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(probability, dtype=float)
    best = (-1.0, 0.5)
    for threshold in np.unique(np.r_[0.05, p, 0.95]):
        predicted = p >= threshold
        tp = int(np.sum(predicted & (y == 1)))
        fp = int(np.sum(predicted & (y == 0)))
        fn = int(np.sum((~predicted) & (y == 1)))
        f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
        best = max(best, (f1, float(threshold)))
    return best[1]
