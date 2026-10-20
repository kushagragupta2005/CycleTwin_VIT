import unittest
import numpy as np
from src.generator import generate
from src.adapters.apple_health import parse_export
from src.model import forecast
from src.splits import patient_partition
from pathlib import Path
import subprocess

class CoreTests(unittest.TestCase):
    def test_generator_determinism(self):
        a=generate(9,patients=4,cycles=2); b=generate(9,patients=4,cycles=2)
        self.assertEqual([(r['event'],r['ovulation_day']) for r in a],[(r['event'],r['ovulation_day']) for r in b])
    def test_forecast_bounded(self):
        r=generate(5,patients=1,cycles=1)[0]
        for tier in range(3): self.assertGreaterEqual(forecast(r,14,tier),0); self.assertLessEqual(forecast(r,14,tier),1)
    def test_apple_roundtrip_shape(self):
        subprocess.run(["python3","scripts/make_synthetic_apple_export.py"],check=True,capture_output=True)
        data=parse_export("apple_health_export/export.xml")
        self.assertTrue(data["daily"]); self.assertEqual(len(data["cycle_starts"]),1)
        patient=generate(17,patients=1,cycles=1)[0]
        date=str(patient['period_start'])
        self.assertAlmostEqual(data['daily'][date]['temperature'],36.4+patient['temperature'][0],places=2)
        self.assertAlmostEqual(data['daily'][date]['sleep_core_hours'],3.4,places=2)
    def test_patient_cycles_stay_in_one_partition(self):
        for pid in ("s17-p0000","s17-p0001","s17-p0017"):
            self.assertEqual({patient_partition(pid) for _ in range(6)}, {patient_partition(pid)})
    def test_period_dates_chain_by_generated_cycle_length(self):
        rows=generate(5,patients=1,cycles=4)
        for earlier,later in zip(rows,rows[1:]):
            self.assertEqual(later['period_start'],earlier['period_start']+np.timedelta64(earlier['cycle_length'],'D'))

if __name__ == '__main__': unittest.main()
