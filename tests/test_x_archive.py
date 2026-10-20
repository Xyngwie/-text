import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_x_index', ROOT / 'tools/build_x_index.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class XArchiveTest(unittest.TestCase):
    def fixture(self, root, entries, suffix=''):
        (root / 'data').mkdir()
        raw = ('window.YTD.tweets.part0 = ' + json.dumps(entries) + suffix).encode()
        path = root / 'tweets.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('tweets.js', raw)
        config = dict(sources=[dict(source_id='x-test', account_handle='Example', path='tweets.zip',
                                   archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                   members=['tweets.js'], member_sha256={'tweets.js': hashlib.sha256(raw).hexdigest()})])
        (root / 'data/x_sources.json').write_text(json.dumps(config))

    def tweet(self, pid, text, **extra):
        return dict(tweet=dict(id_str=pid, full_text=text, created_at='Thu Dec 31 23:00:00 +0000 2020', **extra))

    def test_context_authorship_and_local_year_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, [self.tweet('2', 'RT @other: quoted words'),
                                self.tweet('1', 'reply', in_reply_to_status_id_str='99')], ';')
            summary = module.build(root)
            rows = [json.loads(line) for line in (root / 'data/x_posts.jsonl').read_text().splitlines()]
            self.assertEqual([r['post_id'] for r in rows], ['1', '2'])
            self.assertEqual(rows[0]['in_reply_to_status_id'], '99')
            self.assertEqual(rows[1]['kind'], 'repost_candidate')
            self.assertEqual(rows[1]['authorship'], 'unreviewed')
            self.assertEqual(summary['sources'][0]['year_counts_jst'], {2021: 2})
            before = (root / 'data/x_posts.jsonl').read_bytes()
            module.build(root)
            self.assertEqual(before, (root / 'data/x_posts.jsonl').read_bytes())
            (root / 'tweets.zip').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'archive changed'):
                module.build(root)
            self.assertEqual(before, (root / 'data/x_posts.jsonl').read_bytes())

    def test_duplicate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, [self.tweet('1', 'a'), self.tweet('1', 'b')])
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                module.build(root)
            self.assertFalse((root / 'data/x_posts.jsonl').exists())

    def test_review_survives_rebuild_and_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, [self.tweet('1', 'hello')])
            module.build(root)
            row = json.loads((root / 'data/x_posts.jsonl').read_text())
            review = dict(post_id='1', source_id='x-test', text_sha256=row['text_sha256'],
                          review_status='reviewed', authorship='own', theme_confirmed=['life'],
                          speech_act='greeting', review_note='test', batch_id='X001', context_status='standalone')
            path = root / 'data/x_reviews.jsonl'
            path.write_text(json.dumps(review) + '\n')
            summary = module.build(root)
            self.assertEqual(summary['reviewed_posts'], 1)
            self.assertIsNone(summary['next_post_id'])
            before = (root / 'data/x_posts.jsonl').read_bytes()
            module.build(root)
            self.assertEqual(before, (root / 'data/x_posts.jsonl').read_bytes())
            review['text_sha256'] = 'wrong'
            path.write_text(json.dumps(review) + '\n')
            with self.assertRaisesRegex(ValueError, 'review mismatch'):
                module.build(root)
            self.assertEqual(before, (root / 'data/x_posts.jsonl').read_bytes())

    def test_javascript_is_parsed_as_data_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, [self.tweet('1', 'a')], '; malicious()')
            with self.assertRaises(json.JSONDecodeError):
                module.build(root)
