import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


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
