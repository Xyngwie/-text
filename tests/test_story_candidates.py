"""Unit tests for short-story candidate selection."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import story_candidates  # noqa: E402

FEED = """<?xml version='1.0' encoding='UTF-8'?>
<rss version='2.0'><channel>
  <item><title>商店街の名物リレーが復活 - 神戸新聞</title><link>https://example.test/1</link>
    <source>神戸新聞</source><pubDate>{date}</pubDate></item>
  <item><title>容疑者を逮捕 - 神戸新聞</title><link>https://example.test/2</link>
    <source>神戸新聞</source><pubDate>{date}</pubDate></item>
  <item><title>宣伝記事 - どこかの媒体</title><link>https://example.test/3</link>
    <source>どこかの媒体</source><pubDate>{date}</pubDate></item>
</channel></rss>"""


class StoryCandidatesTest(unittest.TestCase):
    def config(self):
        return {
            'sources': [{'source_id': 'story-test', 'track': 'story', 'name': 'test', 'url': 'https://example.test/rss',
                         'allowed_publishers': ['神戸新聞'], 'category': 'local-life', 'enabled': True}],
            'max_age_hours': None,
            'category_order': ['local-life'],
            'excluded_terms': ['逮捕'],
        }

    def fetcher(self, url, timeout):
        from email.utils import format_datetime
        import datetime as dt
        return FEED.format(date=format_datetime(dt.datetime.now(dt.timezone.utc))).encode('utf-8')

    def test_excludes_terms_and_unlisted_publishers(self):
        result = story_candidates.pick(self.config(), [], 5, fetcher=self.fetcher)
        self.assertEqual([row['title'] for row in result['candidates']], ['商店街の名物リレーが復活 - 神戸新聞'])

    def test_skips_registered_candidates_and_registry_check(self):
        first = story_candidates.pick(self.config(), [], 5, fetcher=self.fetcher)['candidates'][0]
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            story = Path(tmp) / 'story.md'
            story.write_text('x', encoding='utf-8')
            registry = Path(tmp) / 'registry.jsonl'
            story_candidates.register(registry, first, story.relative_to(ROOT))
            rows = story_candidates.load_registry(registry)
            self.assertEqual(story_candidates.check(registry), [])
            again = story_candidates.pick(self.config(), rows, 5, fetcher=self.fetcher)
            self.assertEqual(again['candidates'], [])
            with self.assertRaises(SystemExit):
                story_candidates.register(registry, first, story.relative_to(ROOT))

    def test_config_is_valid(self):
        config = json.loads((ROOT / 'config/story_rss_sources.json').read_text(encoding='utf-8'))
        ids = [source['source_id'] for source in config['sources']]
        self.assertEqual(len(ids), len(set(ids)))
        for source in config['sources']:
            self.assertTrue(source['allowed_publishers'])
            self.assertIn(source['category'], config['category_order'])


if __name__ == '__main__':
    unittest.main()
