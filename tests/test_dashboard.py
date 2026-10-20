import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.generator import generate
from src.inference import predict


class DashboardTests(unittest.TestCase):
    def test_abstention_hides_all_personal_prediction_outputs(self):
        at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=45).run()
        at.get("button_group")[0].set_value(["Patient"]).run()
        at.get("button_group")[0].set_value([at.session_state["view"]])
        at.selectbox(key="patient_choice").select("s223-p0026").run()
        self.assertFalse(at.exception)
        self.assertIsNone(at.session_state["visible_prediction"]["prob"])
        self.assertFalse(any('Synthetic ovulation-day estimate:' in x.value for x in at.markdown))
        self.assertFalse(any('sandbox' in b.label.lower() or 'alert to log' in b.label for b in at.button))
        at.get("button_group")[0].set_value(["Cohort"]).run()
        html = next(m.value for m in at.markdown if '<table' in m.value)
        start = html.index('s223-p0026'); row = html[start:html.index('</tr>', start)]
        self.assertIn('Withheld', row)

    def test_tier0_day_estimate_uses_calendar_history(self):
        at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=45).run()
        at.get("button_group")[0].set_value(["Patient"]).run()
        at.get("button_group")[0].set_value([at.session_state["view"]])
        at.selectbox(key="display_tier").select(0).run()
        at.get("button_group")[0].set_value([at.session_state["view"]])
        at.selectbox(key="patient_choice").select('s223-p0002').run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Synthetic ovulation-day estimate: day 28,' in m.value for m in at.markdown))

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
