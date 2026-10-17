#!/usr/bin/env python3
"""Import an authorized /final Issue comment into publication_events.jsonl."""

import argparse
import datetime as dt
import json
import re
from pathlib import Path

from publication_feedback import DEFAULT_LOG, SCHEMA_VERSION, digest, load_events, validate

FINAL_RE = re.compile(
    r"(?:^|\n)/final[ \t]*\r?\n```text\r?\n(?P<text>[\s\S]*?)\r?\n```"
    r"(?:\r?\n/posted[ \t]+(?P<url>https://\S+))?[ \t]*(?:\n|$)",
    re.MULTILINE,
)
MARKER_RE = re.compile(r"<!-- candidate-id:(rss-[0-9a-f]{20}) -->")
DRAFT_SHA_RE = re.compile(r"<!-- draft-sha256:([0-9a-f]{64}) -->")
DRAFT_RE = re.compile(r"## 本人確認前の初稿（強度2\.25）\s+```text\r?\n([\s\S]*?)\r?\n```")


def fail(message):
    raise SystemExit(message)


def atomic_write(path, events):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in events), encoding="utf-8")
    temporary.replace(path)


def event_time(value):
    if not value:
        return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return value


def parse_issue(issue):
    labels = {item["name"] for item in issue.get("labels", [])}
    if "rss-agent" not in labels:
        fail("Issue does not have the rss-agent label")
    body = issue.get("body") or ""
    marker = MARKER_RE.search(body)
    draft_sha = DRAFT_SHA_RE.search(body)
    draft = DRAFT_RE.search(body)
    if not marker or not draft_sha or not draft:
        fail("Issue body is missing fixed RSS agent markers")
    content = draft.group(1)
    if digest(content) != draft_sha.group(1):
        fail("Issue draft does not match its hash marker")
    track = "experimental-politics" if "experimental-politics" in labels else "normal"
    return marker.group(1), content, track


def final_comment(comments, authorized_login):
    matches = []
    for comment in comments:
        if comment.get("user", {}).get("login", "").casefold() != authorized_login.casefold():
            continue
        match = FINAL_RE.search(comment.get("body") or "")
        if match:
            matches.append((comment, match))
    if not matches:
        fail("No authorized /final comment found")
    comment, match = matches[-1]
    content = match.group("text")
    if not content.strip() or len(content) > 10000 or "\x00" in content:
        fail("Final content is empty or outside allowed limits")
    return comment, content, match.group("url")


def build_events(existing, issue, comments, authorized_login, closing_actor):
    if closing_actor.casefold() != authorized_login.casefold():
        fail("Only the authorized user may close and import an RSS agent issue")
    record_id, draft, track = parse_issue(issue)
    if any(event.get("record_id") == record_id for event in existing):
        fail(f"Publication record already exists: {record_id}")
    comment, final, posted_url = final_comment(comments, authorized_login)
    created_at = event_time(issue.get("created_at"))
    approved_at = event_time(issue.get("closed_at") or comment.get("created_at"))
    events = list(existing)
    events.append({
        "schema_version": SCHEMA_VERSION,
        "event_type": "draft_created",
        "record_id": record_id,
        "recorded_at": created_at,
        "content": draft,
        "content_sha256": digest(draft),
        "mode": "normal",
        "intensity": 2.25,
        "generator": "rss-agent",
        "track": track,
        "issue_number": issue["number"],
    })
    current_sha = digest(draft)
    if final != draft:
        events.append({
            "schema_version": SCHEMA_VERSION,
            "event_type": "user_revised",
            "record_id": record_id,
            "recorded_at": event_time(comment.get("created_at")),
            "content": final,
            "content_sha256": digest(final),
            "previous_content_sha256": current_sha,
            "revision_note": "Authorized /final Issue comment",
            "editor": "user",
            "issue_comment_id": comment.get("id"),
        })
        current_sha = digest(final)
    events.append({
        "schema_version": SCHEMA_VERSION,
        "event_type": "user_approved",
        "record_id": record_id,
        "recorded_at": approved_at,
        "approved_content_sha256": current_sha,
        "destination": "manual-social-copy",
        "account_label": "user-selected",
        "execution_time": "manual",
        "attachments": [],
        "approval_text": "Authorized user supplied /final and closed the Issue",
        "issue_number": issue["number"],
    })
    if posted_url:
        events.append({
            "schema_version": SCHEMA_VERSION,
            "event_type": "published",
            "record_id": record_id,
            "recorded_at": approved_at,
            "approved_content_sha256": current_sha,
            "submitted_content": final,
            "submitted_content_sha256": current_sha,
            "posted_content": final,
            "posted_content_sha256": current_sha,
            "platform_transformed": False,
            "destination": "manual-social-copy",
            "account_label": "user-selected",
            "post_reference": posted_url,
            "published_at": approved_at,
        })
    validate(events)
    return events, {"record_id": record_id, "revised": final != draft, "published": bool(posted_url)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-file", type=Path, required=True)
    parser.add_argument("--comments-file", type=Path, required=True)
    parser.add_argument("--authorized-login", required=True)
    parser.add_argument("--closing-actor", required=True)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    args = parser.parse_args()
    issue = json.loads(args.issue_file.read_text(encoding="utf-8"))
    comments = json.loads(args.comments_file.read_text(encoding="utf-8"))
    existing = load_events(args.log)
    events, summary = build_events(existing, issue, comments, args.authorized_login, args.closing_actor)
    atomic_write(args.log, events)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
