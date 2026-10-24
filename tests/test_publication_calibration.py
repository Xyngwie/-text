import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from publication_calibration import comparison_text, load_examples, validate_pairs
from generate_rss_issues import prompt_for, generate_all


class PublicationCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / 'analysis/v039/publication_pairs.json'

    def test_frozen_examples_preserve_counterexample_and_provenance(self):
        examples = load_examples(self.path)
        self.assertEqual(examples['sample_count'], 18)
        self.assertTrue(any('違うか？' in e['final'] for e in examples['examples']))
        self.assertTrue(any('頑張って！！' in e['final'] for e in examples['examples']))
        self.assertTrue(all(e['source_comment_url'] and e['publication_report_url'] for e in examples['examples']))

    def test_tampered_final_is_rejected(self):
        data = json.loads(self.path.read_text())
        data['pairs'][0]['final'] += '変更'
        with self.assertRaises(ValueError):
            validate_pairs(data)

    def test_comparison_removes_metadata_but_keeps_question(self):
        text = '※価値観スライドによるゼロショット仮説\n本文。違うか？\nhttps://example.com/'
        self.assertEqual(comparison_text(text), '本文。違うか？')

    def test_examples_are_actually_supplied_to_generation_prompt(self):
        candidate = dict(candidate_id='id', track='normal', publisher='source', title='記事',
                         description='概要', published_at=None, link='https://example.com',
                         source_claim_status='fact_candidate_not_verified')
        examples = load_examples(self.path)
        prompt = prompt_for(candidate, 'instructions', {}, examples)
        self.assertIn(json.dumps(examples['examples'][0]['final'], ensure_ascii=False), prompt)
        self.assertIn('本人が採用・修整した校正例', prompt)
        self.assertEqual(len(examples['examples']), 6)

    def test_complete_generation_path_loads_frozen_feedback(self):
        candidate = dict(candidate_id='id', track='normal', publisher='source', title='記事',
                         description='概要', published_at=None, link='https://example.com',
                         source_claim_status='fact_candidate_not_verified')
        calls = []
        def generator(prompt):
            calls.append(prompt)
            return dict(facts=[], uncertainties=['原記事未確認'], value_mapping=[],
                        stance='保留', draft='', do_not_publish_reason='材料不足')
        result = generate_all({'candidates': [candidate]}, generator)
        self.assertEqual(len(calls), 1)
        self.assertIn('retrospective_owner_adopted_examples', calls[0])
        self.assertIn('publication_report_url', calls[0])
        self.assertIn('insufficient-source', result['issues'][0]['labels'])
