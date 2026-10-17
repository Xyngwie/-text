"""Unit tests for RSS filtering and Issue feedback import."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
        self.assertIn("Closeを合図に校正履歴へ取り込まれる", issue["body"])
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


if __name__ == "__main__":
    unittest.main()
