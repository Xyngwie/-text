#!/usr/bin/env python3
"""Index an immutable X tweets export without executing its JavaScript wrapper."""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
JST = timezone(timedelta(hours=9))


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_archive(path, members):
    posts, ids, member_hashes = [], set(), {}
    with zipfile.ZipFile(path) as archive:
        for member in members:
            # Read only named members; never extract arbitrary paths or execute JS.
            raw = archive.read(member)
            member_hashes[member] = sha256(raw)
            text = raw.decode('utf-8-sig')
            match = re.match(r'\s*window\.YTD\.tweets\.part\d+\s*=\s*', text)
            if not match:
                raise ValueError(f'Unexpected tweets wrapper: {member}')
            payload = text[match.end():].strip()
            if payload.endswith(';'):
                payload = payload[:-1].rstrip()
            entries = json.loads(payload)
            if not isinstance(entries, list):
                raise ValueError('Expected tweet array')
            for ordinal, entry in enumerate(entries, 1):
                tweet = entry['tweet']
                pid = tweet['id_str']
                if not isinstance(pid, str) or not re.fullmatch(r'\d+', pid) or pid in ids:
                    raise ValueError(f'Invalid or duplicate tweet ID: {pid}')
                ids.add(pid)
                body = tweet['full_text']
                if not isinstance(body, str):
                    raise ValueError(f'Invalid tweet text: {pid}')
                created = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y')
                posts.append((tweet, created, member, ordinal))
    return posts, member_hashes


def build(root=ROOT):
    config = json.loads((root / 'data/x_sources.json').read_text())
    review_path = root / 'data/x_reviews.jsonl'
    reviews = [json.loads(line) for line in review_path.read_text().splitlines() if line.strip()] if review_path.exists() else []
    review_map = {review['post_id']: review for review in reviews}
    if len(review_map) != len(reviews):
        raise ValueError('Duplicate X review')
    rows, summaries, global_ids = [], [], set()
    for source in config['sources']:
        path = (root / source['path']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Archive must be inside repository')
        if sha256(path.read_bytes()) != source['archive_sha256']:
            raise ValueError('X archive changed')
        posts, hashes = read_archive(path, source['members'])
        if hashes != source['member_sha256']:
            raise ValueError('X export member changed')
        years, kinds, year_kinds = Counter(), Counter(), {}
        local_rows = []
        for tweet, created, member, ordinal in posts:
            pid = tweet['id_str']
            identity = source['account_handle'].lower() + ':' + pid
            if identity in global_ids:
                raise ValueError(f'Overlapping X archives require explicit reconciliation: {pid}')
            global_ids.add(identity)
            body = tweet['full_text']
            rt = body.startswith('RT @')
            reply = tweet.get('in_reply_to_status_id_str')
            kind = 'repost_candidate' if rt else ('reply' if reply else 'post_or_quote')
            years[created.astimezone(JST).year] += 1
            kinds[kind] += 1
            year_kinds.setdefault(created.astimezone(JST).year, Counter())[kind] += 1
            row = dict(id=f"{source['source_id']}:{pid}", source_id=source['source_id'],
                       platform='X', account_handle=source['account_handle'], post_id=pid,
                       url=f"https://x.com/{source['account_handle']}/status/{pid}",
                       archive_member=member, archive_entry=ordinal,
                       created_at=created.astimezone(timezone.utc).isoformat(),
                       created_at_jst=created.astimezone(JST).isoformat(),
                       text=body, text_sha256=sha256(body.encode('utf-8')),
                       kind=kind, in_reply_to_status_id=reply,
                       in_reply_to_user_id=tweet.get('in_reply_to_user_id_str'),
                       in_reply_to_screen_name=tweet.get('in_reply_to_screen_name'),
                       entities=tweet.get('entities', {}),
                       edit_info=tweet.get('edit_info'), truncated=tweet.get('truncated', False),
                       authorship='unreviewed', review_status='unreviewed')
            local_rows.append(row)
        local_rows.sort(key=lambda row: (row['created_at'], int(row['post_id'])))
        for row in local_rows:
            review = review_map.get(row['post_id'])
            if review is None:
                continue
            if (review['source_id'] != source['source_id'] or review['text_sha256'] != row['text_sha256']
                    or review['review_status'] != 'reviewed'
                    or review['authorship'] not in {'own', 'mixed', 'pasted', 'unknown'}):
                raise ValueError(f"X review mismatch: {row['post_id']}")
            for key in ('authorship', 'review_status', 'theme_confirmed', 'speech_act',
                        'review_note', 'batch_id', 'context_status'):
                row[key] = review[key]
        reviewed = sum(row['review_status'] == 'reviewed' for row in local_rows)
        rows.extend(local_rows)
        summaries.append(dict(source_id=source['source_id'], post_count=len(local_rows),
                              first_at_jst=local_rows[0]['created_at_jst'] if local_rows else None,
                              last_at_jst=local_rows[-1]['created_at_jst'] if local_rows else None,
                              year_counts_jst=dict(sorted(years.items())), kind_counts=dict(kinds),
                              year_kind_counts_jst={year: dict(counts) for year, counts in sorted(year_kinds.items())},
                              semantic_classification_complete=reviewed == len(local_rows),
                              reviewed_posts=reviewed, unreviewed_posts=len(local_rows) - reviewed))
    if set(review_map) - {row['post_id'] for row in rows}:
        raise ValueError('Unknown X review post')
    # All input validation completes before generated files are replaced.
    (root / 'data/x_posts.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in rows))
    reviewed = sum(source['reviewed_posts'] for source in summaries)
    pending = [row for row in rows if row['review_status'] == 'unreviewed']
    summary = dict(schema_version=1, sources=summaries, post_count=len(rows),
                   stage=2 if reviewed else 1,
                   status=('semantic_classification_in_progress' if pending else 'semantic_classification_complete') if reviewed else 'indexed_not_semantically_classified',
                   reviewed_posts=reviewed, unreviewed_posts=len(pending),
                   next_post_id=pending[0]['id'] if pending else None,
                   completeness='Only supplied export; deleted or omitted posts and external context are not guaranteed.')
    (root / 'data/x_manifest.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(build(), ensure_ascii=False, indent=2))
