import unittest
import numpy as np
from src.twin import simulate_reproductive_axis, simulate_metabolic_axis, coupling_sweep

class TwinTests(unittest.TestCase):
    def test_reproductive_state_units_and_positivity(self):
        twin=simulate_reproductive_axis(0.2,0.3,days=55,seed=4)
        self.assertEqual(len(twin['follicle']),55)
        self.assertTrue(np.all(twin['follicle']>=0))
        self.assertTrue(np.all(twin['progesterone_like']>=0))
        self.assertTrue(np.all((twin['temperature_c']>35)&(twin['temperature_c']<38)))
    def test_shared_latent_monotonic_growth_and_sweep(self):
        low=simulate_reproductive_axis(0,0,seed=7)['ovulation_day']
        high=simulate_reproductive_axis(2,.8,seed=7)['ovulation_day']
        self.assertGreater(high,low)
        self.assertEqual(set(coupling_sweep(.2,.3).keys()),{0.0,.5,1.0,2.0})
    def test_metabolic_units_sanity_and_reverse_coupling(self):
        coupled=simulate_metabolic_axis(.5,15,days=28,seed=8)
        uncoupled=simulate_metabolic_axis(.5,15,days=28,seed=8,luteal_coupling=False)
        self.assertEqual(len(coupled['glucose_mg_dl']),28*96)
        self.assertTrue(np.all(coupled['insulin_state']>=0))
        self.assertTrue(np.all(coupled['insulin_sensitivity_state']>=0))
        self.assertTrue(np.all((coupled['glucose_mg_dl']>=40)&(coupled['glucose_mg_dl']<=300)))
        self.assertGreaterEqual(coupled['glucose_mg_dl'][15*96:].mean(),uncoupled['glucose_mg_dl'][15*96:].mean())
        with self.assertRaises(ValueError): simulate_metabolic_axis(0,14,step_minutes=7)

if __name__=='__main__': unittest.main()
