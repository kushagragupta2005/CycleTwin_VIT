import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.generator import generate
from src.inference import predict


class DashboardTests(unittest.TestCase):
    def test_views_and_guided_steps_render(self):
        at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=45).run()
        self.assertFalse(at.exception)
        for name in ("Cohort", "Patient", "Method", "Overview"):
            at.get("button_group")[0].set_value([name]).run()
            self.assertFalse(at.exception, name)
        at.get("button_group")[0].set_value([at.session_state["view"]])
        next(b for b in at.button if b.label == "Try the demo").click().run()
        self.assertFalse(at.exception)
        for _ in range(2):
            at.get("button_group")[0].set_value([at.session_state["view"]])
            next(b for b in at.button if b.label == "Next").click().run()
            self.assertFalse(at.exception)

    def test_dashboard_uses_fitted_inference_exactly(self):
        at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=45).run()
        at.get("button_group")[0].set_value(["Patient"]).run()
        rows = generate(223, patients=36, cycles=2)
        patient = at.session_state["patient_choice"]
        row = next(r for r in rows if r["patient"] == patient and r["cycle"] == 1)
        row["prior_cycle_lengths"] = [r["cycle_length"] for r in rows if r["patient"] == patient and r["cycle"] < 1]
        result = predict(row, 14, at.session_state["display_tier"])
        self.assertAlmostEqual(at.session_state["visible_prediction"]["prob"], result["prob"], delta=1e-12)
        self.assertFalse(at.exception)
