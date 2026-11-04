"""Exact manual review exclusions; original comments and events remain intact."""
import hashlib
import json
from pathlib import Path

DEFAULT_REVIEWS = Path(__file__).resolve().parents[1] / 'data/issue_reviews.jsonl'


def load_verdict_keys(path=DEFAULT_REVIEWS):
    # No model/keyword inference: a review applies only to this exact revision.
    if not path.exists():
        return set()
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    return {(r['issue_number'], r['comment_id'], r['body_sha256']) for r in rows
            if r.get('unit_kind') == 'comment' and r.get('feedback_kind') == 'draft_verdict'}


def is_verdict_comment(keys, issue_number, comment):
    digest = hashlib.sha256((comment.get('body') or '').encode('utf-8')).hexdigest()
    return (issue_number, comment.get('id'), digest) in keys


def is_verdict_event(keys, issue_number, event):
    return (issue_number, event.get('issue_comment_id'), event.get('issue_comment_sha256')) in keys
