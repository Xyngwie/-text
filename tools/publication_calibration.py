#!/usr/bin/env python3
"""Build auditable draft/final pairs; load only manually selected frozen examples."""
import argparse
import collections
import difflib
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES = [
    '※実験政治枠（本人の意見ではなく価値観スライドによるゼロショット仮説）',
    '（実験政治枠：価値観スライドによるゼロショット仮説）',
    '実験政治枠（価値観スライドによるゼロショット仮説）。',
    '実験政治枠（価値観スライドによるゼロショット仮説）：',
    '（※価値観スライドによるゼロショット仮説）',
    '（価値観スライドによるゼロショット仮説）',
    '【価値観スライドによるゼロショット仮説】',
    '※価値観スライドによるゼロショット仮説',
]


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def comparison_text(text):
    # This is for measuring edits only; raw saved publications are never changed.
    text = re.sub(r'https?://\S+', '', text)
    for note in NOTES:
        text = text.replace(note, '')
    return re.sub(r'\s+', '', text)


def build_pairs(events, snapshots):
    groups = collections.defaultdict(list)
    for event in events:
        groups[event['record_id']].append(event)
    pairs = []
    for rid, rows in groups.items():
        pubs = [e for e in rows if e['event_type'] == 'published'
                and e.get('publication_evidence') == 'owner_report']
        if not pubs:
            continue
        publication = pubs[-1]
        draft = next(e for e in rows if e['event_type'] == 'draft_created')
        number, final = draft['issue_number'], publication['posted_content']
        matches = [(s, c) for s in snapshots if s['context']['issue']['number'] == number
                   for c in s['context']['comments']
                   if c['speaker_role'] == 'owner' and c['body'] == final]
        if not matches:
            raise ValueError(f'No owner source comment for published final in Issue {number}')
        source, comment = matches[-1]
        if not any(c['id'] == publication['issue_comment_id'] and c['speaker_role'] == 'owner'
                   for s in snapshots if s['context']['issue']['number'] == number
                   for c in s['context']['comments']):
            raise ValueError('Publication report is absent from captured originals')
        before, after = comparison_text(draft['content']), comparison_text(final)
        edits = [dict(operation=tag, before=before[i:j], after=after[k:l])
                 for tag, i, j, k, l in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
                 if tag != 'equal']
        pairs.append(dict(record_id=rid, issue_number=number, draft=draft['content'], final=final,
                          draft_sha256=sha(draft['content']), final_sha256=sha(final),
                          source_comment_id=comment['id'], source_comment_url=comment['url'],
                          source_snapshot_sha256=source['snapshot_sha256'],
                          publication_report_url=publication['post_reference'],
                          reported_at=publication['recorded_at'],
                          evidence_status='owner_report_not_independently_fetched',
                          authorship='mixed_ai_draft_owner_adopted_and_edited',
                          normalized_draft=before, normalized_final=after, text_edits=edits,
                          draft_has_chigauka='違うか？' in before,
                          final_has_chigauka='違うか？' in after,
                          draft_paragraphs=len(re.split(r'\n\s*\n', draft['content'].strip())),
                          final_paragraphs=len(re.split(r'\n\s*\n', final.strip()))))
    return sorted(pairs, key=lambda p: (p['reported_at'], p['issue_number']))


def validate_pairs(data):
    seen = set()
    for pair in data['pairs']:
        if pair['record_id'] in seen:
            raise ValueError('Duplicate publication pair')
        seen.add(pair['record_id'])
        for key in ('draft', 'final'):
            if sha(pair[key]) != pair[key + '_sha256']:
                raise ValueError('Calibration text hash mismatch')
        if pair['evidence_status'] != 'owner_report_not_independently_fetched':
            raise ValueError('Unexpected publication evidence')
        for key in ('draft', 'final'):
            if comparison_text(pair[key]) != pair['normalized_' + key]:
                raise ValueError('Changed normalization')
    selected = data['selected_example_issues']
    if len(selected) != len(set(selected)) or len(selected) > 6:
        raise ValueError('Expected at most six distinct manually selected examples')
    if not set(selected) <= {p['issue_number'] for p in data['pairs']}:
        raise ValueError('Unknown selected example')


def load_examples(path):
    data = json.loads(path.read_text())
    validate_pairs(data)
    lookup = {p['issue_number']: p for p in data['pairs']}
    return dict(
        status='retrospective_owner_adopted_examples_not_model_training_or_unseen_test',
        selection_note=data['selection_note'], sample_count=len(data['pairs']),
        observed_metrics=data['metrics'],
        examples=[{k: lookup[n][k] for k in ('issue_number', 'draft', 'final', 'source_comment_url',
                                            'publication_report_url', 'authorship', 'evidence_status')}
                  for n in data['selected_example_issues']])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inputs = ['data/publication_events.jsonl', 'sources/github-issues-001/snapshots.jsonl']
    events, snapshots = [[json.loads(s) for s in (ROOT / name).read_text().splitlines()] for name in inputs]
    pairs = build_pairs(events, snapshots)
    with_phrase = [p for p in pairs if p['draft_has_chigauka']]
    metrics = dict(pair_count=len(pairs), drafts_with_chigauka=len(with_phrase),
                   removed_chigauka=sum(not p['final_has_chigauka'] for p in with_phrase),
                   retained_chigauka=sum(p['final_has_chigauka'] for p in with_phrase),
                   final_with_chigauka=sum(p['final_has_chigauka'] for p in pairs),
                   finals_with_blank_line=sum('\n\n' in p['final'] for p in pairs),
                   finals_with_source_url=sum(bool(re.search(r'https?://', p['final'])) for p in pairs))
    data = dict(schema_version=1, status='retrospective_calibration_not_unseen_validation',
                input_files={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in inputs},
                normalization=dict(removed_for_comparison_only=['URLs', 'whitespace', 'listed editorial notes'],
                                   editorial_notes=NOTES), metrics=metrics, pairs=pairs,
                selected_example_issues=[125, 111, 123, 117, 130, 134],
                selection_note='Manual contrast set: rhetorical question, retained 違うか, encouragement, scope-limited correction, personal context, and unchanged body. Not a frequency sample.')
    validate_pairs(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('Refusing to overwrite a frozen calibration snapshot')
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(metrics, ensure_ascii=False))


if __name__ == '__main__':
    main()
