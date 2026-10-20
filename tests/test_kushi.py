from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

from src.personas import make_kushi


class KushiTests(unittest.TestCase):
    def test_persona_selection_never_uses_predictions(self):
        make_kushi.cache_clear()
        with patch('src.inference.predict', side_effect=AssertionError('Selection must not query a model')):
            story=make_kushi()
        self.assertEqual(len(story['six_past_lengths']),6)
        self.assertEqual([s['seed'] for s in story['cycles']],[2107,2108,2109])
        self.assertTrue(30<=story['cycles'][0]['record']['ovulation_day']<=38)
        for sample in story['cycles']:
            self.assertEqual(sample['record']['age'],21)
            self.assertEqual(sample['record']['bmi'],27.0)
            self.assertEqual(sample['record']['family_history'],1)

    def test_all_chapters_scenarios_and_guardrails_render(self):
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app_legacy.py'),default_timeout=45).run()
        at.get('button_group')[0].set_value(['Meet Kushi']).run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Fictional synthetic persona' in w.value for w in at.warning))
        for chapter in range(7):
            self.assertFalse(at.exception,chapter)
            if chapter==4:
                for key in ('kushi_contra','kushi_missing','kushi_thyroid'):
                    at.get('button_group')[0].set_value(['Meet Kushi'])
                    at.checkbox(key=key).check().run()
                    self.assertFalse(at.exception)
                    self.assertIsNone(at.session_state['kushi_visible_prediction']['prob'])
                    self.assertFalse(any(m.label=='Fitted synthetic probability' for m in at.metric))
                    at.get('button_group')[0].set_value(['Meet Kushi'])
                    at.checkbox(key=key).uncheck().run()
            if chapter<6:
                at.get('button_group')[0].set_value(['Meet Kushi'])
                next(b for b in at.button if b.label=='Next chapter').click().run()
        for cycle in (8,9):
            at.get('button_group')[0].set_value(['Meet Kushi'])
            at.selectbox(key='kushi_cycle').select(cycle).run()
            self.assertFalse(at.exception)
