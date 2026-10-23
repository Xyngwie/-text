#!/usr/bin/env python3
"""Preserve owner Issue comments with context; never infer approval or publication."""

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / 'sources/github-issues-001/snapshots.jsonl'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def api(path):
    # --paginate emits consecutive JSON values, also on older gh versions.
    raw = subprocess.check_output(['gh', 'api', '--paginate', path], text=True)
    pages, decoder = [], json.JSONDecoder()
    while raw.strip():
        value, end = decoder.raw_decode(raw.lstrip())
        pages.append(value)
        raw = raw.lstrip()[end:]
    if pages and isinstance(pages[0], list):
        return [item for page in pages for item in page]
    if len(pages) != 1:
        raise ValueError('Expected one API object')
    return pages[0]


def text_record(item, owner):
    login = item.get('user', {}).get('login') or ''
    return {
        'id': item['id'], 'author_login': login,
        'speaker_role': 'owner' if login.casefold() == owner.casefold() else 'other',
        'body': item.get('body'), 'url': item.get('html_url'),
        'created_at': item.get('created_at'), 'updated_at': item.get('updated_at'),
    }


def snapshot(repo, owner, issue, comments):
    if 'pull_request' in issue:
        return None
    ordered = sorted(comments, key=lambda c: (c.get('created_at') or '', c['id']))
    if not any((c.get('user', {}).get('login') or '').casefold() == owner.casefold()
               for c in ordered):
        return None
    context = {
        'repository': repo, 'authorized_owner': owner,
        'issue': dict(text_record(issue, owner), number=issue['number'],
                      title=issue.get('title'), state=issue.get('state'),
                      labels=sorted(label['name'] for label in issue.get('labels', []))),
        'comments': [text_record(c, owner) for c in ordered],
    }
    return dict(schema_version=1, source_id='github-issues-001',
                snapshot_sha256=digest(context), context=context,
                interpretation_status='unclassified_not_approval_or_publication')


def validate(rows):
    seen = set()
    for row in rows:
        sha = row['snapshot_sha256']
        if sha != digest(row['context']) or sha in seen:
            raise ValueError('Invalid or duplicate Issue snapshot hash')
        seen.add(sha)
        if row['interpretation_status'] != 'unclassified_not_approval_or_publication':
            raise ValueError('Archive must not infer final text or approval')
        context = row['context']
        owner = context['authorized_owner'].casefold()
        for item in [context['issue'], *context['comments']]:
            expected = 'owner' if item['author_login'].casefold() == owner else 'other'
            if item['speaker_role'] != expected:
                raise ValueError('Incorrect speaker attribution')
        if not any(c['speaker_role'] == 'owner' for c in context['comments']):
            raise ValueError('Snapshot contains no owner comment')


def append_snapshots(path, snapshots):
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    validate(rows)
    seen = {row['snapshot_sha256'] for row in rows}
    added = []
    for row in snapshots:
        if row is not None and row['snapshot_sha256'] not in seen:
            row = dict(row, captured_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'))
            added.append(row)
            seen.add(row['snapshot_sha256'])
    validate(rows + added)
    if added:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as out:
            for row in added:
                out.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    return len(added)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--authorized-login', required=True)
    parser.add_argument('--issue-number', type=int)
    parser.add_argument('--output', type=Path, default=DEFAULT_ARCHIVE)
    args = parser.parse_args()
    if args.issue_number is not None and args.issue_number <= 0:
        parser.error('Issue number must be positive')
    issues = ([api(f'repos/{args.repo}/issues/{args.issue_number}')] if args.issue_number
              else api(f'repos/{args.repo}/issues?state=all&per_page=100'))
    snapshots = []
    for issue in issues:
        if 'pull_request' in issue or not issue.get('comments'):
            continue
        comments = api(f"repos/{args.repo}/issues/{issue['number']}/comments?per_page=100")
        snapshots.append(snapshot(args.repo, args.authorized_login, issue, comments))
    added = append_snapshots(args.output, snapshots)
    print(json.dumps({'issues_checked': len(issues), 'snapshots_added': added}, ensure_ascii=False))


if __name__ == '__main__':
    main()
