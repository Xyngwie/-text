"""Checks for the approved-publication feedback event log."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/publication_feedback.py"


class PublicationFeedbackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.log = self.folder / "events.jsonl"
        self.draft = self.folder / "draft.txt"
        self.revised = self.folder / "revised.txt"
        self.posted = self.folder / "posted.txt"
        self.draft.write_text("最初の案", encoding="utf-8")
        self.revised.write_text("本人が直した最終案", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *args, success=True):
        result = subprocess.run(
            ["python3", str(TOOL), "--log", str(self.log), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def create_and_revise(self):
        self.run_tool(
            "create", "--record-id", "P001", "--text-file", str(self.draft),
            "--mode", "normal", "--intensity", "2.25", "--generator", "test",
        )
        self.run_tool(
            "revise", "--record-id", "P001", "--text-file", str(self.revised),
            "--note", "語尾を本人が修正",
        )

    def approve(self):
        self.run_tool(
            "approve", "--record-id", "P001", "--text-file", str(self.revised),
            "--destination", "example-social", "--account-label", "main",
            "--approval-text", "この文面で投稿して",
        )

    def test_complete_flow_keeps_user_revision_and_platform_result_separate(self):
        self.create_and_revise()
        self.approve()
        self.posted.write_text("本人が直した最終案\nhttps://short.example/x", encoding="utf-8")
        self.run_tool(
            "post", "--record-id", "P001", "--submitted-file", str(self.revised),
            "--posted-file", str(self.posted), "--post-reference", "post-123",
        )
        result = self.run_tool("validate")
        self.assertEqual(json.loads(result.stdout), {"records": 1, "events": 4})
        events = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual([event["event_type"] for event in events], [
            "draft_created", "user_revised", "user_approved", "published"
        ])
        self.assertTrue(events[-1]["platform_transformed"])
        self.assertEqual(events[1]["editor"], "user")

    def test_revision_after_approval_requires_reapproval(self):
        self.create_and_revise()
        self.approve()
        changed = self.folder / "changed.txt"
        changed.write_text("承諾後に変えた案", encoding="utf-8")
        self.run_tool("revise", "--record-id", "P001", "--text-file", str(changed))
        self.run_tool(
            "post", "--record-id", "P001", "--submitted-file", str(changed),
            "--post-reference", "post-456", success=False,
        )

    def test_post_rejects_content_different_from_approval(self):
        self.create_and_revise()
        self.approve()
        changed = self.folder / "changed.txt"
        changed.write_text("無断で変えた案", encoding="utf-8")
        self.run_tool(
            "post", "--record-id", "P001", "--submitted-file", str(changed),
            "--post-reference", "post-789", success=False,
        )


if __name__ == "__main__":
    unittest.main()
