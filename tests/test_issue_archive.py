import copy
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from archive_issue_comments import api, append_snapshots, snapshot, validate


class IssueArchiveTests(unittest.TestCase):
    def setUp(self):
        self.issue = dict(id=10, number=1, body='AI draft', title='News', state='open',
                          user={'login': 'bot'}, labels=[])
        self.comment = dict(id=20, body='知識がありません。', user={'login': 'Owner'},
                            created_at='2026-10-23T00:00:00Z')

    def test_exact_body_roles_and_no_inferred_approval(self):
        self.comment['body'] = ' 賛成\n\nでも質問です。  '
        row = snapshot('Owner/repo', 'owner', self.issue, [self.comment])
        validate([row])
        self.assertEqual(row['context']['comments'][0]['body'], self.comment['body'])
        self.assertEqual(row['context']['issue']['speaker_role'], 'other')
        self.assertEqual(row['context']['comments'][0]['speaker_role'], 'owner')
        self.assertNotIn('user_approved', str(row))

    def test_repeated_capture_and_edits_preserve_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'snapshots.jsonl'
            row = snapshot('Owner/repo', 'Owner', self.issue, [self.comment])
            self.assertEqual(append_snapshots(path, [row]), 1)
            original = path.read_bytes()
            self.assertEqual(append_snapshots(path, [row]), 0)
            edited = copy.deepcopy(self.comment)
            edited['body'] = '訂正します。'
            self.assertEqual(append_snapshots(path, [snapshot('Owner/repo', 'Owner', self.issue, [edited])]), 1)
            self.assertTrue(path.read_bytes().startswith(original))

    def test_no_other_authors_or_pull_requests_as_owner_sources(self):
        self.assertIsNone(snapshot('Owner/repo', 'other', self.issue, [self.comment]))
        self.issue['pull_request'] = {}
        self.assertIsNone(snapshot('Owner/repo', 'Owner', self.issue, [self.comment]))

    def test_tampering_is_rejected(self):
        row = snapshot('Owner/repo', 'Owner', self.issue, [self.comment])
        row['context']['comments'][0]['body'] = 'changed'
        with self.assertRaises(ValueError):
            validate([row])

    def test_api_collects_all_pages_without_slurp(self):
        with patch('archive_issue_comments.subprocess.check_output',
                   return_value='[ {"id": 1} ]\n[{"id": 2}]\n'):
            self.assertEqual(api('example'), [{'id': 1}, {'id': 2}])

    def test_context_and_comment_removal_produce_distinct_snapshots(self):
        other = dict(id=21, body='Additional context', user={'login': 'bot'})
        full = snapshot('Owner/repo', 'Owner', self.issue, [self.comment, other])
        removed = snapshot('Owner/repo', 'Owner', self.issue, [self.comment])
        self.assertNotEqual(full['snapshot_sha256'], removed['snapshot_sha256'])
        issue_edit = dict(self.issue, body='Changed AI draft')
        changed = snapshot('Owner/repo', 'Owner', issue_edit, [self.comment])
        self.assertNotEqual(removed['snapshot_sha256'], changed['snapshot_sha256'])
