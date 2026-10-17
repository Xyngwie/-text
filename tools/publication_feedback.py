#!/usr/bin/env python3
"""Record and validate draft -> revision -> approval -> publication events."""

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "data/publication_events.jsonl"
SCHEMA_VERSION = 1


def fail(message):
    raise SystemExit(message)


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now_utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load_events(path):
    if not path.exists():
        return []
    events = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"Invalid JSON at {path}:{number}: {exc}")
        events.append(event)
    return events


def record_events(events, record_id):
    return [event for event in events if event.get("record_id") == record_id]


def current_content(events, record_id):
    for event in reversed(record_events(events, record_id)):
        if event["event_type"] in {"draft_created", "user_revised"}:
            return event["content"], event["content_sha256"]
    fail(f"Unknown record_id: {record_id}")


def last_event(events, record_id):
    rows = record_events(events, record_id)
    if not rows:
        fail(f"Unknown record_id: {record_id}")
    return rows[-1]


def append_event(path, event):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def base_event(args, event_type):
    return {
        "schema_version": SCHEMA_VERSION,
        "event_type": event_type,
        "record_id": args.record_id,
        "recorded_at": args.recorded_at or now_utc(),
    }


def command_create(args, events, path):
    if record_events(events, args.record_id):
        fail(f"record_id already exists: {args.record_id}")
    content = read_text(args.text_file)
    event = base_event(args, "draft_created")
    event.update({
        "content": content,
        "content_sha256": digest(content),
        "mode": args.mode,
        "intensity": args.intensity,
        "generator": args.generator,
    })
    append_event(path, event)


def command_revise(args, events, path):
    previous, previous_sha = current_content(events, args.record_id)
    content = read_text(args.text_file)
    if digest(content) == previous_sha:
        fail("Revision is identical to current content")
    event = base_event(args, "user_revised")
    event.update({
        "content": content,
        "content_sha256": digest(content),
        "previous_content_sha256": previous_sha,
        "revision_note": args.note,
        "editor": "user",
    })
    append_event(path, event)


def command_approve(args, events, path):
    content, content_sha = current_content(events, args.record_id)
    if args.text_file and digest(read_text(args.text_file)) != content_sha:
        fail("Approval file does not match the current content")
    event = base_event(args, "user_approved")
    event.update({
        "approved_content_sha256": content_sha,
        "destination": args.destination,
        "account_label": args.account_label,
        "execution_time": args.execution_time,
        "attachments": args.attachment,
        "approval_text": args.approval_text,
    })
    append_event(path, event)


def latest_approval(events, record_id):
    rows = record_events(events, record_id)
    for index in range(len(rows) - 1, -1, -1):
        event = rows[index]
        if event["event_type"] == "user_approved":
            later = rows[index + 1:]
            if any(row["event_type"] in {"user_revised", "draft_created"} for row in later):
                fail("Content changed after approval; reapproval is required")
            if any(row["event_type"] == "published" for row in later):
                fail("This approval has already been used")
            return event
    fail("No usable approval found")


def command_post(args, events, path):
    approval = latest_approval(events, args.record_id)
    submitted = read_text(args.submitted_file)
    submitted_sha = digest(submitted)
    if submitted_sha != approval["approved_content_sha256"]:
        fail("Submitted content does not match the approved content")
    posted = read_text(args.posted_file) if args.posted_file else submitted
    event = base_event(args, "published")
    event.update({
        "approved_content_sha256": approval["approved_content_sha256"],
        "submitted_content": submitted,
        "submitted_content_sha256": submitted_sha,
        "posted_content": posted,
        "posted_content_sha256": digest(posted),
        "platform_transformed": digest(posted) != submitted_sha,
        "destination": approval["destination"],
        "account_label": approval["account_label"],
        "post_reference": args.post_reference,
        "published_at": args.published_at or now_utc(),
    })
    append_event(path, event)


def validate(events):
    errors = []
    by_record = {}
    for number, event in enumerate(events, 1):
        required = {"schema_version", "event_type", "record_id", "recorded_at"}
        missing = sorted(required - event.keys())
        if missing:
            errors.append(f"event {number}: missing {', '.join(missing)}")
            continue
        if event["schema_version"] != SCHEMA_VERSION:
            errors.append(f"event {number}: unsupported schema_version")
        by_record.setdefault(event["record_id"], []).append((number, event))

    for record_id, rows in by_record.items():
        content_sha = None
        approval = None
        published = False
        for number, event in rows:
            kind = event["event_type"]
            if kind == "draft_created":
                if content_sha is not None:
                    errors.append(f"event {number}: duplicate draft for {record_id}")
                content_sha = event.get("content_sha256")
                if content_sha != digest(event.get("content", "")):
                    errors.append(f"event {number}: draft hash mismatch")
            elif kind == "user_revised":
                if content_sha is None:
                    errors.append(f"event {number}: revision before draft")
                if event.get("previous_content_sha256") != content_sha:
                    errors.append(f"event {number}: revision does not follow current content")
                if event.get("content_sha256") != digest(event.get("content", "")):
                    errors.append(f"event {number}: revision hash mismatch")
                content_sha = event.get("content_sha256")
                approval = None
                published = False
            elif kind == "user_approved":
                if event.get("approved_content_sha256") != content_sha:
                    errors.append(f"event {number}: approval does not match current content")
                approval = event
            elif kind == "published":
                if approval is None:
                    errors.append(f"event {number}: publication without current approval")
                if published:
                    errors.append(f"event {number}: approval reused")
                if event.get("submitted_content_sha256") != content_sha:
                    errors.append(f"event {number}: submitted content differs from approval")
                if event.get("submitted_content_sha256") != digest(event.get("submitted_content", "")):
                    errors.append(f"event {number}: submitted hash mismatch")
                if event.get("posted_content_sha256") != digest(event.get("posted_content", "")):
                    errors.append(f"event {number}: posted hash mismatch")
                transformed = event.get("posted_content_sha256") != event.get("submitted_content_sha256")
                if event.get("platform_transformed") != transformed:
                    errors.append(f"event {number}: platform transformation flag mismatch")
                published = True
            else:
                errors.append(f"event {number}: unknown event_type {kind}")
    if errors:
        fail("\n".join(errors))
    return {"records": len(by_record), "events": len(events)}


def command_validate(events):
    print(json.dumps(validate(events), ensure_ascii=False))


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(name):
        item = sub.add_parser(name)
        item.add_argument("--record-id", required=True)
        item.add_argument("--recorded-at")
        return item

    create = common("create")
    create.add_argument("--text-file", required=True)
    create.add_argument("--mode", default="normal")
    create.add_argument("--intensity", type=float, default=2.25)
    create.add_argument("--generator", default="unknown")

    revise = common("revise")
    revise.add_argument("--text-file", required=True)
    revise.add_argument("--note", default="")

    approve = common("approve")
    approve.add_argument("--text-file")
    approve.add_argument("--destination", required=True)
    approve.add_argument("--account-label", required=True)
    approve.add_argument("--execution-time", default="immediate")
    approve.add_argument("--attachment", action="append", default=[])
    approve.add_argument("--approval-text", required=True)

    post = common("post")
    post.add_argument("--submitted-file", required=True)
    post.add_argument("--posted-file")
    post.add_argument("--post-reference", required=True)
    post.add_argument("--published-at")

    sub.add_parser("validate")
    return parser


def main():
    args = build_parser().parse_args()
    path = args.log if args.log.is_absolute() else ROOT / args.log
    events = load_events(path)
    if args.command == "create":
        command_create(args, events, path)
    elif args.command == "revise":
        command_revise(args, events, path)
    elif args.command == "approve":
        command_approve(args, events, path)
    elif args.command == "post":
        command_post(args, events, path)
    elif args.command == "validate":
        command_validate(events)
    else:
        fail("Unknown command")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
