import unittest
import numpy as np
from src.safety import abstain, abstention_reasons
from src.conformal import calibrate_binary, classification_set, ovulation_interval
from src.alerts import apply_alert_budget
from src.metabolic import simulate_cgm, excursion_event

class SafetyTests(unittest.TestCase):
    def test_all_abstention_rules_are_explicit(self):
        record={"tsh_abnormal":True,"prolactin_abnormal":True,"hormonal_contraception":True,
                "age":17,"pregnant":True,"postpartum":True,"breastfeeding":True,
                "perimenopausal":True,"wear_completeness":.4}
        reasons=abstention_reasons(record)
        self.assertTrue(abstain(record)); self.assertGreaterEqual(len(reasons),6)
    def test_conformal_helpers_are_bounded(self):
        q=calibrate_binary([0,1,0,1],[.1,.8,.2,.9],alpha=.25)
        self.assertGreaterEqual(q,0); self.assertLessEqual(q,1)
        self.assertEqual(ovulation_interval(18,3),(15,21))
        self.assertTrue(classification_set(.9,q))
        y=[0,1,0,1]; p=[.1,.8,.2,.9]
        empirical=sum(label in classification_set(prob,q) for label,prob in zip(y,p))/len(y)
        self.assertGreaterEqual(empirical,.75)
    def test_alert_budget_and_abstention(self):
        rows=[{"patient":"p1","cycle":0,"day":10,"risk":.8},
              {"patient":"p1","cycle":0,"day":14,"risk":.9},
              {"patient":"p2","cycle":0,"day":14,"risk":.99,"abstain":True}]
        out=apply_alert_budget(rows)
        self.assertEqual(sum(r['alert'] for r in out if r['patient']=='p1'),1)
        self.assertFalse(any(r['alert'] for r in out if r['patient']=='p2'))
    def test_cgm_is_deterministic_and_uses_postmeal_window(self):
        _,a,meals=simulate_cgm(3,.5)
        _,b,_=simulate_cgm(3,.5)
        self.assertTrue(np.array_equal(a,b)); self.assertEqual(len(a),28*96); self.assertEqual(len(meals),28*3)
        self.assertIsInstance(excursion_event(a,meals[0]),bool)

if __name__=='__main__': unittest.main()
