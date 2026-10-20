import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class SubmissionTests(unittest.TestCase):
    def test_technical_checklist_passes_and_human_work_is_not_claimed(self):
        status=json.loads((ROOT/'docs/submission_status.json').read_text())
        self.assertEqual(status['technical_failures'],[])
        self.assertTrue(status['human_actions'])
        self.assertTrue(any('video' in s.lower() for s in status['human_actions']))
        self.assertTrue(all(r['human_only'] for r in status['rules'] if r['status']!='PASS'))
        self.assertTrue(json.loads((ROOT/'docs/public_access_check.json').read_text())['all_pass'])

    def test_recording_runbook_has_full_duration_and_limitations(self):
        claims=json.loads((ROOT/'docs/claims.json').read_text())
        runbook=(ROOT/'docs/video_runbook_20min.md').read_text()
        self.assertEqual(runbook,claims['deliverables']['runbook'])
        minutes=claims['context']['competition']['minimum_video_minutes']
        self.assertEqual(sum(line.startswith('| ') and ':00-' in line for line in runbook.splitlines()),minutes)
        for minute in range(minutes-claims['configuration']['limitations_minutes'],minutes):
            self.assertTrue(any(line.startswith(f'| {minute:02d}:00-') and 'Limitations:' in line for line in runbook.splitlines()))
