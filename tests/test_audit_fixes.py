import importlib
from pathlib import Path
import unittest
from unittest.mock import patch

from src.features import attach_prior_cycle_lengths, build_feature_matrix
from src.generator import generate
from src.inference import safe_predict
from src.model import estimate_ovulation_day
from src.safety import abstain, synthetic_safety_record


class AuditFixTests(unittest.TestCase):
    def test_missing_or_invalid_safety_information_fails_closed(self):
        record = generate(61, patients=1, cycles=1)[0]
        flags = synthetic_safety_record(record, 14)
        flags['wear_completeness'] = 1.0
        self.assertFalse(abstain(flags))
        for key in flags:
            missing = dict(flags); missing.pop(key)
            self.assertTrue(abstain(missing), key)
        for value in (None, float('nan'), float('inf'), -1, 2):
            self.assertTrue(abstain(dict(flags, wear_completeness=value)))
        with patch('src.inference.predict') as model:
            out = safe_predict(record, 14, 2, safety={})
            model.assert_not_called()
        self.assertIsNone(out['prob']); self.assertIsNone(out['interval'])
        self.assertEqual(out['contributions'], [])
        from src.alerts import apply_alert_budget
        self.assertFalse(apply_alert_budget([{'patient':'unknown','cycle':0,'risk':1.0}])[0]['alert'])

    def test_calendar_day_helper_receives_only_completed_history(self):
        raw = generate(61, patients=1, cycles=6)
        rows = attach_prior_cycle_lengths(raw)
        import numpy as np
        self.assertTrue(np.array_equal(build_feature_matrix(raw, 14, 0),
                                       build_feature_matrix(rows, 14, 0), equal_nan=True))
        for index, row in enumerate(rows):
            self.assertEqual(row['prior_cycle_lengths'], [r['cycle_length'] for r in raw[max(0,index-3):index]])
            if index:
                expected = max(1, round(float(np.mean(row['prior_cycle_lengths']))-14))
                self.assertEqual(estimate_ovulation_day(row, 14, 0), expected)

    def test_uploaded_xml_temporary_file_is_deleted_even_on_failure(self):
        adapter = importlib.import_module('src.adapters.apple_health')
        original = adapter.parse_export
        paths = []
        def track(path):
            paths.append(Path(path)); self.assertTrue(Path(path).exists())
            return original(path)
        with patch.object(adapter, 'parse_export', side_effect=track):
            adapter.parse_upload_bytes(b'<HealthData/>')
            with self.assertRaises(Exception): adapter.parse_upload_bytes(b'<broken')
        self.assertNotEqual(paths[0], paths[1])
        self.assertFalse(any(p.exists() for p in paths))
