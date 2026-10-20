#!/usr/bin/env python3
"""Import plain owner comments and later publication reports as append-only feedback."""

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
POST_URL_RE = re.compile(r'https://(?:www\.)?(?:x\.com|twitter\.com)/[^\s/]+/status/\d+(?:\?[^\s]*)?')
POSTED_RE = re.compile(r'(?:(?:X|Twitter|SNS|ツイッター|エックス)(?:に|へ))?(?:投稿|ポスト)(?:しました|した|したよ|したぞ|しましたよ|済み|済みです)[。.!！\s]*', re.IGNORECASE)


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


def comment_parts(comment):
    body = comment.get('body') or ''
    legacy = FINAL_RE.search(body)
    if legacy:
        return legacy.group('text'), bool(legacy.group('url')), legacy.group('url')
    stripped = body.strip()
    urls = POST_URL_RE.findall(stripped)
    rest = POST_URL_RE.sub('', stripped).strip()
    if POSTED_RE.fullmatch(rest) or (urls and not rest):
        return None, True, urls[0] if urls else None
    if re.fullmatch(r'(?:まだ)?(?:投稿|ポスト)(?:していません|してない|しません|しない)[。.!！\s]*', stripped):
        return None, False, None
    if stripped in {'', 'ありがとう', 'ありがとうございます', '了解', '了解です', '確認しました', 'OK', 'ok'}:
        return None, False, None
    if not body.strip() or len(body) > 10000 or '\x00' in body:
        fail('Final content is empty or outside allowed limits')
    # Preserve copied text exactly, including line breaks and trailing whitespace.
    return body, False, None


def build_events(existing, issue, comments, authorized_login, closing_actor, allow_empty=False):
    if closing_actor.casefold() != authorized_login.casefold():
        fail("Only the authorized user may import RSS feedback")
    record_id, draft, track = parse_issue(issue)
    events = list(existing)
    original_count = len(events)
    record = [e for e in events if e.get('record_id') == record_id]
    if record and (record[0].get('content_sha256') != digest(draft)
                   or record[0].get('issue_number') != issue['number']):
        fail('Existing record does not match this Issue')
    revised = False
    authorized = [c for c in comments if c.get('user', {}).get('login', '').casefold() == authorized_login.casefold()]
    authorized.sort(key=lambda c: (c.get('created_at') or '', c.get('id') or 0))

    def current_record():
        return [e for e in events if e.get('record_id') == record_id]

    def seen(comment, part):
        fingerprint = digest(comment.get('body') or '')
        return any(e.get('issue_comment_id') == comment.get('id')
                   and e.get('issue_comment_sha256') == fingerprint
                   and e.get('feedback_part') == part for e in current_record())

    def append(kind, comment, part, **fields):
        events.append(dict(schema_version=SCHEMA_VERSION, event_type=kind, record_id=record_id,
                           recorded_at=event_time(comment.get('updated_at') or comment.get('created_at')),
                           issue_comment_id=comment.get('id'), issue_comment_sha256=digest(comment.get('body') or ''),
                           feedback_part=part, **fields))

    for comment in authorized:
        final, posted, posted_url = comment_parts(comment)
        if final is not None and not seen(comment, 'final'):
            record = current_record()
            legacy_seen = any(e.get('issue_comment_id') == comment.get('id')
                              and not e.get('issue_comment_sha256') and e.get('content') == final for e in record)
            if not legacy_seen:
                if not record:
                    events.append(dict(schema_version=SCHEMA_VERSION, event_type='draft_created', record_id=record_id,
                                       recorded_at=event_time(issue.get('created_at')), content=draft,
                                       content_sha256=digest(draft), mode='normal', intensity=2.25,
                                       generator='rss-agent', track=track, issue_number=issue['number']))
                    record = current_record()
                latest = next(e for e in reversed(record) if e['event_type'] in {'draft_created', 'user_revised'})
                current_sha = latest['content_sha256']
                if final != latest['content']:
                    append('user_revised', comment, 'final', content=final, content_sha256=digest(final),
                           previous_content_sha256=current_sha, revision_note='Owner supplied final text in Issue comment', editor='user')
                    current_sha = digest(final)
                    revised = True
                # Never infer permission to auto-publish; this records the owner's manual-copy final.
                last = current_record()[-1]
                if last['event_type'] != 'published':
                    append('user_approved', comment, 'final', approved_content_sha256=current_sha,
                           destination='manual-social-copy', account_label='user-selected', execution_time='manual',
                           attachments=[], approval_text='Owner supplied final text for manual copying; not permission for automated posting',
                           issue_number=issue['number'])
        if posted and not seen(comment, 'posted'):
            record = current_record()
            if not record:
                continue
            latest = next(e for e in reversed(record) if e['event_type'] in {'draft_created', 'user_revised'})
            # At most one publication report per currently approved content version.
            tail = record[record.index(latest)+1:]
            if any(e['event_type'] == 'published' for e in tail):
                continue
            approval = next((e for e in reversed(tail) if e['event_type'] == 'user_approved'), None)
            if not approval:
                continue
            if final is None and comment.get('created_at') and comment['created_at'] < approval['recorded_at']:
                continue  # An older report cannot attest a final supplied later.
            content, sha = latest['content'], latest['content_sha256']
            reference = posted_url or comment.get('html_url') or f"{issue.get('html_url', 'issue:' + str(issue['number']))}#issuecomment-{comment.get('id')}"
            append('published', comment, 'posted', approved_content_sha256=sha,
                   submitted_content=content, submitted_content_sha256=sha, posted_content=content,
                   posted_content_sha256=sha, platform_transformed=False, destination='manual-social-copy',
                   account_label='user-selected', post_reference=reference, post_url=posted_url,
                   publication_evidence='owner_report', posted_content_verification='owner_report_not_independently_fetched',
                   published_at=event_time(comment.get('created_at')))
    if not current_record():
        if not allow_empty:
            fail('No authorized final text comment found')
    validate(events)
    return events, dict(record_id=record_id, revised=revised,
                        published=any(e['event_type'] == 'published' for e in current_record()),
                        added_events=len(events)-original_count)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-file", type=Path, required=True)
    parser.add_argument("--comments-file", type=Path, required=True)
    parser.add_argument("--authorized-login", required=True)
    parser.add_argument("--closing-actor", required=True)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument('--allow-empty', action='store_true')
    args = parser.parse_args()
    issue = json.loads(args.issue_file.read_text(encoding="utf-8"))
    comments = json.loads(args.comments_file.read_text(encoding="utf-8"))
    existing = load_events(args.log)
    events, summary = build_events(existing, issue, comments, args.authorized_login, args.closing_actor, args.allow_empty)
    atomic_write(args.log, events)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
