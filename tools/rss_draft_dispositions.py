"""Owner-defined RSS close decisions, separate from publication events."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / 'data/rss_draft_dispositions.jsonl'


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def decision(issue, comments, owner, actor, verdict_keys=None):
    from import_issue_feedback import parse_issue, comment_parts
    from reviewed_feedback import load_verdict_keys, is_verdict_comment
    if actor.casefold() != owner.casefold():
        raise ValueError('Only the authorized owner may record RSS decisions')
    candidate, draft, _ = parse_issue(issue)
    state = issue.get('state')
    if state not in {'open', 'closed'}:
        return None
    keys = load_verdict_keys() if verdict_keys is None else verdict_keys
    owned = sorted((c for c in comments
                    if (c.get('user', {}).get('login') or '').casefold() == owner.casefold()),
                   key=lambda c: (c.get('created_at') or '', c['id']))
    manuscripts = []
    for comment in owned:
        final, _, _ = comment_parts(comment, is_verdict_comment(keys, issue['number'], comment))
        if final is not None:
            manuscripts.append(dict(comment_id=comment['id'],
                                    comment_body_sha256=digest(comment.get('body') or ''),
                                    content=final, content_sha256=digest(final),
                                    origin='copied_ai_draft' if final == draft else 'owner_supplied_or_revised',
                                    role='owner_adopted_utterance'))
    disposition = 'pending' if state == 'open' else ('adopted' if manuscripts else 'rejected')
    payload = dict(schema_version=1, policy_version='rss-close-v1', candidate_id=candidate,
                   issue_number=issue['number'], issue_state=state,
                   issue_body_sha256=digest(issue.get('body') or ''),
                   disposition=disposition, owner_login=owner,
                   closed_at=issue.get('closed_at'),
                   owner_comment_fingerprints=[dict(id=c['id'], sha256=digest(c.get('body') or '')) for c in owned],
                   manuscripts=manuscripts if disposition == 'adopted' else [],
                   publication_inferred=False,
                   rejection_scope='draft_only_not_news_or_belief' if disposition == 'rejected' else None)
    payload['decision_sha256'] = digest(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def record(path, issue, comments, owner, actor):
    row = decision(issue, comments, owner, actor)
    if row is None:
        return None
    history = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
    latest = next((r for r in reversed(history) if r['candidate_id'] == row['candidate_id']), None)
    # Open Issues have no final disposition; retain a pending revision only after reopening.
    if (not latest and row['disposition'] == 'pending') or (latest and latest['decision_sha256'] == row['decision_sha256']):
        return row['disposition']
    history.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in history))
    temporary.replace(path)
    return row['disposition']


def validate(path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        payload = {k: v for k, v in row.items() if k != 'decision_sha256'}
        assert row['decision_sha256'] == digest(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        assert row['policy_version'] == 'rss-close-v1'
        assert row['disposition'] in {'adopted', 'rejected', 'pending'}
        assert row['publication_inferred'] is False
        assert (row['issue_state'] == 'open') == (row['disposition'] == 'pending')
        assert bool(row['manuscripts']) == (row['disposition'] == 'adopted')
        for manuscript in row['manuscripts']:
            assert manuscript['content_sha256'] == digest(manuscript['content'])
            assert manuscript['role'] == 'owner_adopted_utterance'
