import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from import_issue_feedback import build_events, comment_parts
from publication_feedback import latest_approval, digest
from publication_calibration import build_pairs
from reviewed_feedback import load_verdict_keys, is_verdict_comment


class VerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshots = [json.loads(l) for l in (ROOT / 'sources/github-issues-001/snapshots.jsonl').read_text().splitlines()]
        cls.keys = load_verdict_keys()

    def fixture(self, number=238):
        snapshot = next(s for s in reversed(self.snapshots) if s['context']['issue']['number'] == number)
        issue = dict(snapshot['context']['issue'], labels=[{'name': 'rss-agent'}])
        comments = [dict(c, user={'login': 'Xyngwie'}) for c in snapshot['context']['comments']]
        return issue, comments

    def run_import(self, issue, comments, existing=(), **kwargs):
        return build_events(list(existing), issue, comments, 'Xyngwie', 'Xyngwie', allow_empty=True, **kwargs)[0]

    def test_reviewed_rejections_and_approval_verdict_are_not_final(self):
        for number in [221, 234, 238]:
            with self.subTest(issue=number):
                issue, comments = self.fixture(number)
                self.assertEqual(self.run_import(issue, comments), [])

    def test_exact_revision_not_keyword_filter(self):
        issue, comments = self.fixture()
        changed = dict(comments[0], body='こんな無責任なことは言わない。まず現場を見よう。')
        self.assertFalse(is_verdict_comment(self.keys, issue['number'], changed))
        events = self.run_import(issue, [changed])
        self.assertEqual(events[-1]['event_type'], 'user_approved')
        self.assertEqual(events[-2]['content'], changed['body'])
        self.assertFalse(is_verdict_comment(self.keys, 99999, comments[0]))

    def test_explicit_final_keeps_legacy_contract(self):
        body = '/final\n```text\n本人が確定した文章。\n```'
        self.assertEqual(comment_parts({'body': body}, reviewed_verdict=True), ('本人が確定した文章。', False, None))

    def test_old_verdict_cannot_be_published_or_used_as_approval(self):
        issue, comments = self.fixture()
        old = self.run_import(issue, comments, verdict_keys=set())
        report = dict(id=999999999, body='投稿しました', user={'login': 'Xyngwie'}, created_at='2026-11-04T12:00:00Z')
        self.assertEqual(self.run_import(issue, comments+[report], old), old)
        with self.assertRaisesRegex(SystemExit, 'verdict'):
            latest_approval(old, old[0]['record_id'])

    def test_real_final_after_verdict_can_be_reported_without_changing_old_events(self):
        issue, comments = self.fixture()
        old = self.run_import(issue, comments, verdict_keys=set())
        final = dict(id=999999998, body='工夫を楽しむ人がいる。それで十分じゃないか。', user={'login': 'Xyngwie'}, created_at='2026-11-04T11:00:00Z')
        report = dict(id=999999999, body='投稿しました', user={'login': 'Xyngwie'}, created_at='2026-11-04T12:00:00Z')
        events = self.run_import(issue, comments+[final, report], old)
        self.assertEqual(events[:len(old)], old)
        self.assertEqual(events[-1]['event_type'], 'published')
        self.assertEqual(events[-1]['posted_content'], final['body'])
        self.assertEqual(self.run_import(issue, comments+[final, report], events), events)

    def test_historical_bad_pair_is_excluded_from_calibration(self):
        issue, comments = self.fixture()
        old = self.run_import(issue, comments, verdict_keys=set())
        report = dict(id=999999999, body='投稿しました', user={'login': 'Xyngwie'}, created_at='2026-11-04T12:00:00Z')
        historical = self.run_import(issue, comments+[report], old, verdict_keys=set())
        self.assertEqual(historical[-1]['event_type'], 'published')
        self.assertEqual(build_pairs(historical, self.snapshots), [])


if __name__ == '__main__':
    unittest.main()
