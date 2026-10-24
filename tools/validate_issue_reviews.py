#!/usr/bin/env python3
"""Verify manual Issue classifications against immutable captured snapshots."""
import hashlib
import json
from pathlib import Path
from archive_issue_comments import validate as validate_archive

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    archive = root / 'sources/github-issues-001/snapshots.jsonl'
    rows = [json.loads(line) for line in archive.read_text().splitlines()]
    validate_archive(rows)
    snapshots = {r['snapshot_sha256']: r for r in rows}
    path = root / 'data/issue_reviews.jsonl'
    reviews = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    themes = json.loads((root / 'data/taxonomy.json').read_text())['themes']
    seen = set()
    for review in reviews:
        snapshot = snapshots[review['snapshot_sha256']]['context']
        assert review['source_id'] == 'github-issues-001'
        assert snapshot['issue']['number'] == review['issue_number']
        if review['unit_kind'] == 'issue_body':
            unit = snapshot['issue']
            suffix = f"issue-{review['issue_number']}:body"
        else:
            assert review['unit_kind'] == 'comment'
            unit = next(c for c in snapshot['comments'] if c['id'] == review['comment_id'])
            suffix = f"comment-{unit['id']}"
        assert unit['speaker_role'] == 'owner'
        assert review['unit_id'] == 'github-issues-001:' + suffix
        assert hashlib.sha256((unit['body'] or '').encode()).hexdigest() == review['body_sha256']
        key = review['unit_id'], review['body_sha256']
        assert key not in seen
        seen.add(key)
        assert review['authorship'] in {'own', 'mixed', 'pasted', 'unknown'}
        assert review['theme_labels'] and set(review['theme_labels']) <= set(themes)
        assert review['note'] and review['speech_act']
    return {'classified_issue_units': len(reviews)}


if __name__ == '__main__':
    print(json.dumps(validate(), ensure_ascii=False))
