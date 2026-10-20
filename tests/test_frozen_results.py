import csv
import hashlib
import json
from pathlib import Path
import unittest

from src.features import attach_prior_cycle_lengths
from src.generator import generate
from src.inference import predict

ROOT=Path(__file__).resolve().parents[1]


class FrozenResultsTests(unittest.TestCase):
    def test_frozen_raw_result_is_immutable_and_matches_tagged_source(self):
        receipt=json.loads((ROOT/'results/frozen_receipt.json').read_text())
        self.assertEqual(receipt['status'],'completed once')
        self.assertEqual(hashlib.sha256((ROOT/'results_final_frozen.json').read_bytes()).hexdigest(),receipt['results_sha256'])
        card=json.loads((ROOT/'models/frozen/model_card.json').read_text())
        self.assertEqual(card['git_hash'],receipt['commit'])
        self.assertEqual(len(card['models']),36)
        lock=json.loads((ROOT/'results/frozen_execution.lock').read_text())
        self.assertEqual(lock['protocol_sha256'],hashlib.sha256((ROOT/'docs/frozen_protocol.json').read_bytes()).hexdigest())

    def test_frozen_persisted_inference_reproduces_saved_predictions(self):
        with (ROOT/'results/predictions_final_frozen.csv').open() as handle:
            records=list(csv.DictReader(handle))
        self.assertEqual(len(records),38880)
        sources={}
        for seed in json.loads((ROOT/'docs/frozen_protocol.json').read_text())['seeds']:
            sources[seed]={(r['patient'],r['cycle']):r for r in attach_prior_cycle_lengths(generate(seed))}
        checked=set()
        for r in records:
            key=(int(r['seed']),int(r['day']),int(r['tier']),int(r['cycle']))
            if key[-1] not in (0,2) or key in checked: continue
            row=sources[key[0]][(r['patient'],key[-1])]
            output=predict(row,key[1],key[2],seed=key[0])
            self.assertAlmostEqual(output['prob'],float(r['probability']),delta=1e-12)
            checked.add(key)
        self.assertEqual(len(checked),72)
