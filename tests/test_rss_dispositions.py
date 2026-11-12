import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from generate_rss_issues import issue_payload
from rss_draft_dispositions import decision, record, validate


class CloseDecisionTests(unittest.TestCase):
    def setUp(self):
        candidate = dict(candidate_id='rss-'+'a'*20, track='normal', publisher='Source',
                         source_name='Source', title='記事', description='', published_at=None,
                         link='https://example.com', source_claim_status='unverified')
        generation = dict(facts=[], uncertainties=[], value_mapping=[], stance='立場',
                          draft='無理なく続けられる仕組みがよい。', do_not_publish_reason='')
        payload = issue_payload(candidate, generation)
        self.issue = dict(number=900, state='closed', closed_at='2026-11-12T10:00:00Z',
                          body=payload['body'], labels=[{'name':'rss-agent'}])
        self.draft = payload['draft']

    def comment(self, text, owner='Owner', cid=1):
        return dict(id=cid, body=text, user={'login':owner})

    def decide(self, comments, **changes):
        return decision(dict(self.issue, **changes), comments, 'Owner', 'Owner', verdict_keys=set())

    def test_bare_close_rejects_only_the_draft(self):
        row = self.decide([])
        self.assertEqual(row['disposition'], 'rejected')
        self.assertEqual(row['rejection_scope'], 'draft_only_not_news_or_belief')
        self.assertFalse(row['publication_inferred'])

    def test_copy_and_revision_are_owner_adopted_not_spontaneous_or_published(self):
        for text, origin in [(self.draft,'copied_ai_draft'), ('手直しした原稿。','owner_supplied_or_revised')]:
            row = self.decide([self.comment(text)])
            self.assertEqual(row['disposition'],'adopted')
            self.assertEqual(row['manuscripts'][0]['content'], text)
            self.assertEqual(row['manuscripts'][0]['origin'], origin)
            self.assertFalse(row['publication_inferred'])

    def test_verdict_thanks_publication_report_and_others_are_not_manuscripts(self):
        for text in ['言う', '採用', '言わん\n僕なら書かない', 'ありがとう', '投稿しました']:
            self.assertEqual(self.decide([self.comment(text)])['disposition'], 'rejected')
        self.assertEqual(self.decide([self.comment(self.draft,owner='Other')])['disposition'],'rejected')

    def test_scope_and_actor_are_checked(self):
        with self.assertRaises(SystemExit):
            self.decide([], labels=[{'name':'x-classification'}])
        with self.assertRaises(ValueError):
            decision(self.issue, [], 'Owner', 'Other')

    def test_append_only_edits_reopening_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'decisions.jsonl'
            opened=dict(self.issue,state='open',closed_at=None)
            record(path, opened, [], 'Owner','Owner')
            self.assertFalse(path.exists())
            record(path,self.issue,[],'Owner','Owner')
            first=path.read_text()
            record(path,self.issue,[],'Owner','Owner')
            self.assertEqual(first,path.read_text())
            record(path,self.issue,[self.comment(self.draft)],'Owner','Owner')
            record(path,opened,[self.comment(self.draft)],'Owner','Owner')
            rows=[json.loads(l) for l in path.read_text().splitlines()]
            self.assertEqual([r['disposition'] for r in rows],['rejected','adopted','pending'])
            self.assertTrue(path.read_text().startswith(first))
            validate(path)
