import json
from pathlib import Path
import unittest

from scripts.build_claims import build
from scripts.validate_claims import main, check_text


class ClaimsTests(unittest.TestCase):
    def test_claims_are_rebuilt_from_artifacts(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(build(write=False),json.loads((root/'docs/claims.json').read_text()))

    def test_all_deliverable_metric_strings_match_claims(self):
        main()

    def test_unknown_or_stale_metric_is_rejected(self):
        with self.assertRaises(AssertionError):
            check_text('Synthetic AUROC 0.637, Brier 0.306',['Synthetic AUROC 0.906, Brier 0.119'],'stale-example')
