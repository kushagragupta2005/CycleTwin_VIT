import unittest

import numpy as np

from src.features import build_feature_matrix
from src.fitted import PlattModel, choose_f1_threshold
from src.generator import generate


class FittedPipelineTests(unittest.TestCase):
    def test_calendar_feature_has_no_current_or_future_cycle_value(self):
        rows = generate(61, patients=1, cycles=3)
        matrix = build_feature_matrix(rows, day=14, tier=0)
        self.assertTrue(np.isnan(matrix[0, 0]))
        self.assertAlmostEqual(matrix[1, 0], rows[0]["cycle_length"])
        self.assertAlmostEqual(matrix[2, 0], np.mean([rows[0]["cycle_length"], rows[1]["cycle_length"]]))

    def test_platt_model_outputs_probabilities_and_validation_threshold(self):
        x_train = np.array([[0.0], [0.2], [0.8], [1.0]])
        y_train = np.array([0, 0, 1, 1])
        x_val = np.array([[0.1], [0.3], [0.7], [0.9]])
        y_val = np.array([0, 0, 1, 1])
        model = PlattModel().fit(x_train, y_train, x_val, y_val)
        probabilities = model.predict_proba(x_val)
        self.assertTrue(np.all((probabilities >= 0) & (probabilities <= 1)))
        self.assertGreaterEqual(choose_f1_threshold(y_val, probabilities), 0.05)


if __name__ == "__main__":
    unittest.main()
