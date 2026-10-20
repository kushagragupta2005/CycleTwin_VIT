import csv
import json
from pathlib import Path
import unittest

import numpy as np

from src.features import build_feature_matrix, record_features
from src.fitted import PlattModel
from src.generator import generate
from src.inference import model_card, predict
from src.splits import patient_partition

ROOT = Path(__file__).resolve().parents[1]


class PersistedInferenceTests(unittest.TestCase):
    def test_classification_regression_to_audited_results(self):
        before = json.loads((ROOT / "tests/fixtures/classification_before_audit.json").read_text())
        after = json.loads((ROOT / "results.json").read_text())

        def compare(a, b, path):
            if isinstance(a, dict):
                for k, v in a.items():
                    if k == "auprc" and "legacy_custom_auprc" in b:
                        compare(v, b["legacy_custom_auprc"], path + "/" + k)
                    elif k == "auprc_cluster_bootstrap_95ci" and "legacy_custom_auprc_cluster_bootstrap_95ci" in b:
                        compare(v, b["legacy_custom_auprc_cluster_bootstrap_95ci"], path + "/" + k)
                    else:
                        compare(v, b[k], path + "/" + k)
            elif isinstance(a, list):
                self.assertEqual(len(a), len(b), path)
                for x, y in zip(a, b): compare(x, y, path)
            elif isinstance(a, (int, float)):
                self.assertAlmostEqual(a, b, delta=1e-12, msg=path)
            else:
                self.assertEqual(a, b, path)
        compare(before["seeds"], after["seeds"], "classification")

    def test_persisted_pipeline_matches_independent_benchmark_refit(self):
        rows = generate(97)
        parts = {key: [r for r in rows if patient_partition(r["patient"]) == key]
                 for key in ("train", "validation", "test")}
        for day in (10, 14, 18):
            for tier in range(4):
                result = model_card()["models"][f"seed_97_day_{day}_tier_{tier}"]
                selected = result["selected_tier"]
                model = PlattModel().fit(
                    build_feature_matrix(parts["train"], day, selected), [r["event"] for r in parts["train"]],
                    build_feature_matrix(parts["validation"], day, selected), [r["event"] for r in parts["validation"]])
                expected = model.predict_proba(build_feature_matrix(parts["test"], day, selected))
                for index in (0, 1, 5, 6, 17):
                    row = dict(parts["test"][index])
                    row["prior_cycle_lengths"] = [r["cycle_length"] for r in parts["test"]
                                                   if r["patient"] == row["patient"] and r["cycle"] < row["cycle"]]
                    output = predict(row, day, tier)
                    self.assertAlmostEqual(output["prob"], expected[index], delta=1e-12)
                    total = output["calibrated_intercept"] + sum(c["calibrated_logit_contribution"] for c in output["contributions"])
                    self.assertAlmostEqual(1/(1+np.exp(-total)), output["prob"], delta=1e-12)

    def test_inference_does_not_require_current_cycle_truth(self):
        row = generate(61, patients=1, cycles=1)[0]
        row["prior_cycle_lengths"] = [31, 35, 39]
        expected = predict(row, 14, 2)["prob"]
        for key in ("event", "ovulation_day", "cycle_length", "patient", "cycle"):
            row.pop(key)
        self.assertAlmostEqual(predict(row, 14, 2)["prob"], expected, delta=1e-12)

    def test_all_saved_models_and_heldout_predictions_exist(self):
        card = model_card()
        self.assertEqual(len(card["models"]), 36)
        for value in card["models"].values():
            self.assertTrue((ROOT / value["artifact"]).is_file())
            self.assertEqual(len(value["features"]), len(value["coefficients"]))
        with (ROOT / "results/predictions_heldout.csv").open() as handle:
            self.assertEqual(sum(1 for _ in csv.DictReader(handle)), 38880)
