import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import stage3_dialogue as dialogue


SOURCES = [dict(evidence_id=f'U{i:05d}', text=f'原文{i}：この点は条件によって判断が変わると思う。',
                themes=['thinking'], context_group=f'S{i}', review_status='reviewed',
                url=f'https://example.com/{i}', source_type='conversation', caveat='文脈限定')
           for i in range(1, 4)]


def generated(prompt):
    return dict(title='判断を変える条件', observation='異なる条件への言及があります。',
                hypothesis='条件に応じた判断かもしれません。', limits='一般化はできません。',
                next_question='どんな時に判断を変えますか？',
                evidence=[dict(evidence_id='E01', quote='原文1')]), {'model_version': 'test-model'}


class DialogueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'prompts').mkdir()
        (self.root / 'prompts/stage3_dialogue.md').write_text('Test instructions')
        self.pool = patch.object(dialogue, 'source_pool', return_value=copy.deepcopy(SOURCES))
        self.pool.start()
        self.addCleanup(self.pool.stop)
        self.git = patch.object(dialogue.subprocess, 'check_output', return_value='abc123\n')
        self.git.start()
        self.addCleanup(self.git.stop)

    def prepare(self, issues=None, comments=None, generator=generated):
        return dialogue.prepare(self.root, 'Owner/repo', 'Owner', issues or [],
                                lambda n: comments or [], generator=generator)

    def delivered_initial(self):
        self.prepare()
        turn = dialogue.artifacts(self.root)[0]
        (self.root / 'data').mkdir()
        (self.root / 'data/stage3_dialogue_receipts.json').write_text(
            json.dumps({turn['turn_id']: {'url': 'https://example.com/issues/1'}}))
        return turn, dict(number=1, body=turn['issue_body'], html_url='https://example.com/issues/1')

    def test_initial_and_pending_outbox_do_not_generate_twice(self):
        self.assertEqual(self.prepare()['status'], 'prepared')
        self.assertEqual(self.prepare(generator=lambda p: self.fail('duplicate call'))['status'], 'pending_delivery')
        turn = dialogue.artifacts(self.root)[0]
        self.assertEqual(turn['generation']['evidence'][0]['evidence_id'], 'U00001')
        self.assertFalse(turn['formal_analysis_updated'])

    def test_wait_without_owner_reply_or_on_other_authors(self):
        turn, issue = self.delivered_initial()
        no_call = lambda p: self.fail('waiting must not call model')
        self.assertEqual(self.prepare([issue], generator=no_call)['status'], 'waiting_for_owner')
        other = dict(id=2, body='agree', user={'login': 'Other'})
        self.assertEqual(self.prepare([issue], [other], no_call)['status'], 'waiting_for_owner')

    def test_owner_reply_to_closed_issue_is_input_not_approval(self):
        turn, issue = self.delivered_initial()
        issue['state'] = 'closed'
        c = dict(id=3, body='いつもではないです。', user={'login': 'OWNER'}, html_url='https://example.com/c3')
        self.assertEqual(self.prepare([issue], [c])['status'], 'prepared')
        followup = dialogue.artifacts(self.root)[-1]
        self.assertEqual(followup['owner_comments'][0]['body'], c['body'])
        self.assertEqual(followup['issue_number'], 1)
        self.assertNotIn('approved', followup)

    def test_next_command_completes_without_model(self):
        turn, issue = self.delivered_initial()
        c = dict(id=3, body='次へ。', user={'login': 'Owner'})
        self.prepare([issue], [c], generator=lambda p: self.fail('next command needs no model'))
        final = dialogue.artifacts(self.root)[-1]
        self.assertEqual(final['status'], 'complete_unconfirmed')
        self.assertEqual(final['generation']['next_question'], '')

    def test_invalid_quote_does_not_advance(self):
        def bad(prompt):
            value, model = generated(prompt)
            value['evidence'][0]['quote'] = '原文に存在しない引用'
            return value, model
        with self.assertRaises(ValueError):
            self.prepare(generator=bad)
        self.assertEqual(dialogue.artifacts(self.root), [])

    def test_used_sources_are_not_recycled(self):
        previous = [dict(theme='thinking', sources=SOURCES[:2])]
        theme, sources = dialogue.choose_sources(SOURCES, previous)
        self.assertIsNone(theme)
        self.assertEqual(sources, [])

    def test_conversation_uses_review_themes_and_segment_groups(self):
        self.pool.stop()
        data = self.root / 'data'
        data.mkdir()
        (data / 'reviews.jsonl').write_text(json.dumps(dict(
            utterance_id='U1', authorship='own', theme_labels=['thinking'])) + '\n')
        (data / 'segments.jsonl').write_text(json.dumps(dict(
            segment_id='S1', user_utterance_ids=['U1'])) + '\n')
        row = dict(id='U1', role='user', _body='本人の文章で条件や考え方について説明しているところです。' * 3,
                   start_line=1, end_line=3)
        with patch.object(dialogue, 'parse_sources', return_value=[({'source_url': 'https://example.com'}, [row])]):
            pool = dialogue.source_pool(self.root)
        self.assertEqual(pool[0]['themes'], ['thinking'])
        self.assertEqual(pool[0]['context_group'], 'S1')

    def test_delivery_recovers_already_created_issue(self):
        self.prepare()
        turn = dialogue.artifacts(self.root)[0]
        issue = dict(number=1, body=turn['issue_body'], html_url='https://example.com/issues/1')
        with patch.object(dialogue, 'ensure_label'), patch.object(dialogue, 'run') as gh:
            dialogue.deliver(self.root, 'Owner/repo', [issue])
            gh.assert_not_called()
            self.assertEqual(dialogue.deliver(self.root, 'Owner/repo', [issue])['status'], 'nothing_to_deliver')

    def test_third_turn_stops_without_automatic_confirmation(self):
        turn, issue = self.delivered_initial()
        c = dict(id=3, body='条件による。', user={'login': 'Owner'})
        self.prepare([issue], [c])
        second = dialogue.artifacts(self.root)[-1]
        receipt_path = self.root / 'data/stage3_dialogue_receipts.json'
        receipts = json.loads(receipt_path.read_text())
        receipts[second['turn_id']] = {'url': 'https://example.com/c4'}
        receipt_path.write_text(json.dumps(receipts))
        c2 = dict(id=5, body='あと一つ例があります。', user={'login': 'Owner'})
        self.prepare([issue], [c, c2])
        final = dialogue.artifacts(self.root)[-1]
        self.assertEqual(final['status'], 'complete_unconfirmed')
        self.assertFalse(final['generation_prompt_updated'])
