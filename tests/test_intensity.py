import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import generate_rss_issues as rss
from import_issue_feedback import build_events, parse_issue


class IntensityTests(unittest.TestCase):
    def candidate(self, number):
        return dict(candidate_id='rss-' + f'{number:020x}', track='normal', publisher='Source',
                    source_name='Source', title='記事', description='概要', published_at=None,
                    link='https://example.com', source_claim_status='fact_candidate_not_verified')

    def generation(self, prompt):
        return dict(facts=[], uncertainties=[], value_mapping=[], stance='改善を提案する',
                    draft='この点は改善した方がよい。', do_not_publish_reason='')

    def test_per_draft_values_reach_prompt_issue_and_feedback(self):
        prompts = []
        def generate(prompt):
            prompts.append(prompt)
            return self.generation(prompt)
        with patch.object(rss, 'select_intensity', side_effect=[1.5, 2.0, 2.5]) as draw:
            result = rss.generate_all({'candidates': [self.candidate(i) for i in range(3)]}, generate)
        self.assertEqual(draw.call_count, 3)
        for index, value in enumerate([1.5, 2.0, 2.5]):
            payload = result['issues'][index]
            self.assertIn(f'今回の強度は {value:.2f}', prompts[index])
            self.assertIn(f'強度{value:.2f}', payload['body'])
            self.assertEqual(payload['intensity'], value)
            issue = dict(number=index+1, body=payload['body'], labels=[{'name': 'rss-agent'}])
            events, _ = build_events([], issue, [dict(id=10+index, body='本人の確定文',
                                                     user={'login': 'Owner'})], 'Owner', 'Owner')
            self.assertEqual(events[0]['intensity'], value)

    def test_marker_mismatch_is_rejected_and_old_heading_is_supported(self):
        payload = rss.issue_payload(self.candidate(1), self.generation(''), 1.5)
        issue = dict(number=1, body=payload['body'], labels=[{'name': 'rss-agent'}])
        issue['body'] = issue['body'].replace('draft-intensity:1.50', 'draft-intensity:2.50')
        with self.assertRaises(SystemExit):
            parse_issue(issue)
        old = rss.issue_payload(self.candidate(2), self.generation(''), 2.25)
        issue['body'] = old['body'].replace('<!-- draft-intensity:2.25 -->', '')
        self.assertEqual(parse_issue(issue)[1], old['draft'])

    def test_invalid_values_fail_before_generation(self):
        for value in [1.49, 2.51, float('nan'), True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                rss.issue_payload(self.candidate(1), self.generation(''), value)
