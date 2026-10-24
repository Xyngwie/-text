"""Unit tests for RSS filtering and Issue feedback import."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rss = load_module("rss_agent", ROOT / "tools/rss_agent.py")
generator = load_module("generate_rss_issues", ROOT / "tools/generate_rss_issues.py")


class RssAgentTest(unittest.TestCase):
    def sample_feed(self):
        return """<?xml version='1.0' encoding='UTF-8'?>
        <rss version='2.0'><channel>
          <item><title>法案を国会へ提出 - Reuters</title><link>https://example.test/1</link>
            <guid>a</guid><pubDate>Wed, 01 Oct 2025 10:00:00 GMT</pubDate>
            <description>政府は法案を提出した。</description><source>Reuters</source></item>
          <item><title>批判殺到の衝撃コラム - Reuters</title><link>https://example.test/2</link>
            <guid>b</guid><description>意見記事</description><source>Reuters</source></item>
          <item><title>別媒体の記事</title><link>https://example.test/3</link>
            <guid>c</guid><description>記事</description><source>Unknown Media</source></item>
        </channel></rss>""".encode("utf-8")

    def test_experimental_feed_requires_publisher_and_rejects_opinion_terms(self):
        source = {
            "source_id": "reuters", "name": "Reuters", "track": "experimental-politics",
            "allowed_publishers": ["Reuters"],
        }
        rows = rss.parse_feed(self.sample_feed(), source, ["コラム", "批判殺到", "衝撃"])
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["rejected_reasons"], [])
        self.assertIn("excluded_term:コラム,批判殺到,衝撃", rows[1]["rejected_reasons"])
        self.assertIn("publisher_not_allowlisted", rows[2]["rejected_reasons"])
        self.assertEqual(rows[0]["source_claim_status"], "fact_candidate_not_verified")

    def test_publisher_name_does_not_accept_a_different_pr_service(self):
        self.assertTrue(rss.publisher_allowed(' Reuters ', ['Reuters']))
        self.assertFalse(rss.publisher_allowed('共同通信PRワイヤー', ['共同通信']))
        self.assertFalse(rss.publisher_allowed('Not Reuters', ['Reuters']))

    def test_collection_deduplicates_same_candidate(self):
        config = {
            "experimental_excluded_terms": [],
            "sources": [
                {"source_id": "same", "name": "One", "track": "normal", "url": "https://one", "allowed_publishers": []},
                {"source_id": "same", "name": "Two", "track": "normal", "url": "https://two", "allowed_publishers": []},
            ],
        }
        result = rss.collect(config, 1, fetcher=lambda _url, _timeout: self.sample_feed())
        self.assertEqual(len(result["candidates"]), 3)

    def candidate(self, pid, source, category, date='2026-01-01T00:00:00+00:00'):
        return dict(candidate_id=pid, source_id=source, category=category, track='normal', published_at=date)

    def test_selection_is_balanced_not_first_feed_only(self):
        rows = [self.candidate(f'game-{i}', 'atelier', 'games') for i in range(20)]
        rows += [self.candidate('general', 'nhk', 'general'), self.candidate('politics', 'nhk-politics', 'politics'),
                 self.candidate('world', 'bbc', 'world'), self.candidate('tech', 'ai', 'technology'),
                 self.candidate('official', 'egov', 'official')]
        selected = rss.balanced_candidates(rows, 6, ['general', 'politics', 'world', 'technology', 'games', 'official'])
        self.assertEqual([r['category'] for r in selected], ['general', 'politics', 'world', 'technology', 'games', 'official'])

    def test_existing_issues_are_excluded_before_slot_selection(self):
        rows = [self.candidate('old', 'atelier', 'games'), self.candidate('new', 'nhk', 'general')]
        self.assertEqual([r['candidate_id'] for r in rss.balanced_candidates(rows, 1, excluded_ids={'old'})], ['new'])

    def test_categories_beyond_six_slots_get_their_turn_next_run(self):
        categories = ['science', 'health', 'education', 'environment', 'culture', 'sports', 'life', 'labor']
        rows = [self.candidate(c, 'feed-' + c, c) for c in categories]
        first = rss.balanced_candidates(rows, 6, categories, category_last_seen={})
        seen = {r['category']: '2026-10-23T00:00:00Z' for r in first}
        second = rss.balanced_candidates(rows, 6, categories, category_last_seen=seen)
        self.assertEqual([r['category'] for r in second[:2]], ['life', 'labor'])

    def test_longest_absent_category_precedes_recent_category(self):
        rows = [self.candidate('a', 'a', 'science'), self.candidate('b', 'b', 'politics')]
        selected = rss.balanced_candidates(rows, 1, ['science', 'politics'], category_last_seen={
            'science': '2026-10-23T00:00:00Z', 'politics': '2026-10-20T00:00:00Z'})
        self.assertEqual(selected[0]['category'], 'politics')

    def test_history_includes_closed_issues_and_ignores_unmarked_records(self):
        cid = 'rss-' + 'a' * 20
        issues = [dict(body=f'<!-- candidate-id:{cid} -->', state='closed',
                       labels=[{'name': 'news-science'}], created_at='2026-10-23T00:00:00Z'),
                  dict(body='unrelated', labels=[{'name': 'news-health'}], created_at='2026-10-24T00:00:00Z')]
        ids, history = rss.issue_selection_history(issues)
        self.assertEqual(ids, {cid})
        self.assertEqual(history, {'science': '2026-10-23T00:00:00Z'})

    def test_diverse_sources_are_not_tied_to_known_interests(self):
        config = json.loads((ROOT / 'config/rss_sources.json').read_text())
        active = [s for s in config['sources'] if s.get('enabled', True)]
        categories = {s['category'] for s in active}
        self.assertTrue({'science', 'health', 'education', 'environment', 'culture', 'sports',
                         'life', 'labor', 'law', 'infrastructure', 'economy'} <= categories)
        self.assertEqual(len({s['source_id'] for s in config['sources']}), len(config['sources']))
        self.assertFalse(any('atelier' in s['source_id'] for s in active))

    def test_sources_rotate_and_newest_is_first_within_source(self):
        rows = [self.candidate('old', 'one', 'world', '2025-01-01T00:00:00+00:00'),
                self.candidate('new', 'one', 'world', '2026-01-01T00:00:00+00:00'),
                self.candidate('other', 'two', 'world', '2025-06-01T00:00:00+00:00')]
        self.assertEqual([r['candidate_id'] for r in rss.balanced_candidates(rows, 3)], ['new', 'other', 'old'])

    def test_direct_feed_publisher_and_stale_item_are_recorded(self):
        source = dict(source_id='direct', name='Official', track='experimental-politics', category='general',
                      publisher='NHK', allowed_publishers=[], url='https://example.test/feed')
        feed = b'<rss><channel><item><title>News</title><link>https://example.test/a</link><pubDate>Wed, 01 Jan 2020 00:00:00 GMT</pubDate></item></channel></rss>'
        result = rss.collect(dict(sources=[source], max_age_hours=168), 1, True, lambda *_: feed)
        self.assertEqual(result['candidates'][0]['publisher'], 'NHK')
        self.assertIn('stale_item', result['candidates'][0]['rejected_reasons'])
        self.assertEqual(result['source_diagnostics'][0]['accepted'], 0)

    def test_disabled_feed_is_not_fetched(self):
        def fail(*_):
            raise AssertionError('disabled feed fetched')
        result = rss.collect({'sources': [dict(source_id='off', enabled=False)]}, 1, fetcher=fail)
        self.assertEqual(result['candidates'], [])

    def test_stock_quote_page_is_not_a_news_article(self):
        source = dict(source_id='search', name='Reuters', track='experimental-politics',
                      allowed_publishers=[], url='https://example.test/feed')
        feed = b'<rss><channel><item><title>8101.TW - | Stock Price &amp; Latest News - Reuters</title><link>https://example.test/a</link></item></channel></rss>'
        result = rss.collect(dict(sources=[source], excluded_title_patterns=['Stock Price']), 1, True, lambda *_: feed)
        self.assertIn('non_article_title', result['candidates'][0]['rejected_reasons'])
        self.assertEqual(result['source_diagnostics'][0]['accepted'], 0)

    def test_issue_marks_political_draft_as_unverified_hypothesis(self):
        candidate = {
            "candidate_id": "rss-0123456789abcdef0123", "track": "experimental-politics",
            "publisher": "Reuters", "source_name": "Reuters", "title": "法案提出",
            "description": "政府は法案を提出した。", "published_at": "2025-10-01T10:00:00+00:00",
            "link": "https://example.test/1", "source_claim_status": "fact_candidate_not_verified",
            "rejected_reasons": [],
        }
        generated = {
            "facts": ["政府が法案を提出したとRSSにある"], "uncertainties": ["法案本文"],
            "value_mapping": ["修正可能性を見る"], "stance": "制度の検証手段を先に示すべきだ",
            "draft": "法案の看板より、間違えた時に直せる仕組みを先に示すべきだ。",
            "do_not_publish_reason": "",
        }
        issue = generator.issue_payload(candidate, generated)
        self.assertIn("本人の意見ではなく", issue["body"])
        self.assertIn("投稿禁止", issue["body"])
        self.assertIn("experimental-politics", issue["labels"])
        self.assertIn("タグやコードブロックは不要", issue["body"])
        self.assertIn("Closeは不要", issue["body"])
        self.assertIn("本人承認済み・未投稿", issue["body"])

    def test_model_selection_prefers_stable_flash_and_excludes_specialized_models(self):
        models = [
            "gemini-pro-latest", "gemini-3-flash-preview", "gemini-2.5-flash",
            "gemini-2.0-flash", "gemini-embedding-001", "gemini-2.5-flash-image",
        ]
        self.assertEqual(generator.rank_generation_models(models), [
            "gemini-2.5-flash", "gemini-2.0-flash", "gemini-3-flash-preview", "gemini-pro-latest",
        ])


class IssueFeedbackImportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.issue_file = self.folder / "issue.json"
        self.comments_file = self.folder / "comments.json"
        self.log = self.folder / "events.jsonl"
        self.draft = "AIの初稿"
        import hashlib
        sha = hashlib.sha256(self.draft.encode()).hexdigest()
        self.issue = {
            "number": 12, "created_at": "2026-01-01T00:00:00Z", "closed_at": "2026-01-01T01:00:00Z",
            "labels": [{"name": "rss-agent"}, {"name": "experimental-politics"}],
            "body": f"<!-- rss-agent:v1 -->\n<!-- candidate-id:rss-0123456789abcdef0123 -->\n<!-- draft-sha256:{sha} -->\n<!-- track:experimental-politics -->\n\n## 本人確認前の初稿（強度2.25）\n\n```text\n{self.draft}\n```",
        }
        self.issue_file.write_text(json.dumps(self.issue), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_import(self, actor="Xyngwie", success=True):
        result = subprocess.run([
            "python3", str(ROOT / "tools/import_issue_feedback.py"),
            "--issue-file", str(self.issue_file), "--comments-file", str(self.comments_file),
            "--authorized-login", "Xyngwie", "--closing-actor", actor, "--log", str(self.log),
        ], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def test_authorized_final_and_posted_url_are_imported(self):
        comments = [{
            "id": 99, "created_at": "2026-01-01T00:30:00Z", "user": {"login": "Xyngwie"},
            "body": "/final\n```text\n本人が直した確定文\n```\n/posted https://example.social/post/1",
        }]
        self.comments_file.write_text(json.dumps(comments), encoding="utf-8")
        self.run_import()
        events = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual([row["event_type"] for row in events], [
            "draft_created", "user_revised", "user_approved", "published"
        ])
        self.assertEqual(events[1]["content"], "本人が直した確定文")
        self.assertEqual(events[-1]["post_reference"], "https://example.social/post/1")

    def test_other_user_cannot_supply_or_approve_final(self):
        comments = [{
            "id": 100, "created_at": "2026-01-01T00:30:00Z", "user": {"login": "attacker"},
            "body": "/final\n```text\n悪意ある文面\n```",
        }]
        self.comments_file.write_text(json.dumps(comments), encoding="utf-8")
        self.run_import(success=False)
        self.comments_file.write_text(json.dumps([]), encoding="utf-8")
        self.run_import(actor="attacker", success=False)

    def owner_comment(self, cid, body, when='2026-01-01T00:30:00Z'):
        return dict(id=cid, body=body, created_at=when, user={'login': 'Xyngwie'},
                    html_url=f'https://github.com/owner/repo/issues/12#issuecomment-{cid}')

    def events(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def save_comments(self, comments):
        self.comments_file.write_text(json.dumps(comments), encoding='utf-8')

    def test_plain_final_then_separate_publication_without_url(self):
        final = self.owner_comment(101, '本人がそのまま貼った文\n改行も残す。')
        self.save_comments([final])
        self.run_import()
        first = self.events()
        self.assertEqual(first[1]['content'], final['body'])
        self.assertEqual(first[-1]['event_type'], 'user_approved')
        posted = self.owner_comment(102, '投稿しました', '2026-01-01T00:40:00Z')
        self.save_comments([final, posted])
        self.run_import()
        events = self.events()
        self.assertEqual(events[:len(first)], first)
        self.assertEqual(events[-1]['event_type'], 'published')
        self.assertIsNone(events[-1]['post_url'])
        self.assertEqual(events[-1]['publication_evidence'], 'owner_report')
        self.assertEqual(events[-1]['post_reference'], posted['html_url'])
        before = self.log.read_bytes()
        self.run_import()
        self.assertEqual(before, self.log.read_bytes())

    def test_closed_issue_can_receive_publication_report_later(self):
        final = self.owner_comment(101, '最終版')
        self.save_comments([final])
        self.run_import()
        url = 'https://x.com/Xyngwie/status/123456'
        self.save_comments([final, self.owner_comment(102, url, '2026-01-01T02:00:00Z')])
        self.run_import()
        self.assertEqual(self.events()[-1]['post_reference'], url)

    def test_prefixed_publication_report_and_legacy_repair(self):
        final = self.owner_comment(101, '実際の投稿本文')
        self.save_comments([final])
        self.run_import()
        previous = self.events()
        posted = self.owner_comment(102, '上記のコメントで投稿しました。', '2026-01-01T00:40:00Z')
        # Reproduce the prior importer misclassifying this report as a final.
        import hashlib
        sha = hashlib.sha256(posted['body'].encode()).hexdigest()
        wrong = dict(previous[-2], content=posted['body'], content_sha256=sha,
                     previous_content_sha256=previous[-2]['content_sha256'],
                     issue_comment_id=102, issue_comment_sha256=sha, recorded_at=posted['created_at'])
        approval = dict(previous[-1], approved_content_sha256=sha,
                        issue_comment_id=102, issue_comment_sha256=sha, recorded_at=posted['created_at'])
        old = previous + [wrong, approval]
        self.log.write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in old))
        self.save_comments([final, posted])
        self.run_import()
        rows = self.events()
        self.assertEqual(rows[:len(old)], old)
        self.assertEqual(rows[-1]['event_type'], 'published')
        self.assertEqual(rows[-1]['posted_content'], final['body'])
        self.assertEqual(rows[-1]['publication_evidence'], 'owner_report')
        before = self.log.read_bytes()
        self.run_import()
        self.assertEqual(before, self.log.read_bytes())

    def test_natural_short_publication_reports_are_not_final_text(self):
        sys.path.insert(0, str(ROOT / 'tools'))
        from import_issue_feedback import comment_parts
        for text in ['上記投稿しました', '上記投稿しました。', '上記X投稿しました。',
                     '上記、投稿しました。', '上記のコメントで投稿しました。']:
            with self.subTest(text=text):
                self.assertEqual(comment_parts({'body': text}), (None, True, None))
        self.assertEqual(comment_parts({'body': '上記、まだ投稿していません。'}), (None, False, None))

    def test_other_users_posted_report_is_ignored(self):
        final = self.owner_comment(101, '最終版')
        other = self.owner_comment(102, '投稿しました')
        other['user']['login'] = 'attacker'
        self.save_comments([final, other])
        self.run_import()
        self.assertEqual(self.events()[-1]['event_type'], 'user_approved')

    def test_revised_final_requires_a_new_publication_report(self):
        first = self.owner_comment(101, '最初の確定文')
        posted = self.owner_comment(102, '投稿しました', '2026-01-01T00:40:00Z')
        self.save_comments([first, posted])
        self.run_import()
        revised = self.owner_comment(103, '新しい確定文', '2026-01-01T00:50:00Z')
        self.save_comments([first, posted, revised])
        self.run_import()
        events = self.events()
        self.assertEqual(events[-1]['event_type'], 'user_approved')
        self.assertEqual(sum(e['event_type'] == 'published' for e in events), 1)

    def test_edit_is_append_only_and_does_not_reuse_old_posted_report(self):
        final = self.owner_comment(101, '最初の確定文')
        posted = self.owner_comment(102, '投稿しました', '2026-01-01T00:40:00Z')
        self.save_comments([final, posted])
        self.run_import()
        first_events = self.events()
        final['body'] = '編集した確定文'
        final['updated_at'] = '2026-01-01T00:50:00Z'
        self.save_comments([final, posted])
        self.run_import()
        events = self.events()
        self.assertEqual(events[:len(first_events)], first_events)
        self.assertEqual(events[-1]['event_type'], 'user_approved')
        self.assertEqual(sum(e['event_type'] == 'published' for e in events), 1)

    def test_negative_publication_report_is_not_a_final_or_publication(self):
        final = self.owner_comment(101, '最終版')
        self.save_comments([final])
        self.run_import()
        before = self.log.read_bytes()
        self.save_comments([final, self.owner_comment(102, 'まだ投稿していません')])
        self.run_import()
        self.assertEqual(before, self.log.read_bytes())


if __name__ == "__main__":
    unittest.main()
