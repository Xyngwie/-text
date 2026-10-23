#!/usr/bin/env python3
"""Prepare a bounded owner dialogue, commit its outbox, then deliver to Issues."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from archive_issue_comments import api, digest
from classify_x_batch import gemini, jsonl
from publish_issue_payloads import ensure_label, run
from source_catalog import parse_sources

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'stage3-dialogue'
MAX_TURNS = 3


def read_json(path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def artifacts(root):
    return [json.loads(p.read_text()) for p in sorted((root / 'analysis/dialogues').glob('D*/turn-*.json'))]


def issue_marker(topic):
    return f'<!-- stage3-topic:{topic} -->'


def turn_marker(turn_id):
    return f'<!-- stage3-turn:{turn_id} -->'


def owner_comments(comments, owner):
    return [dict(id=c['id'], body=c.get('body') or '', created_at=c.get('created_at'),
                 updated_at=c.get('updated_at'), url=c.get('html_url'))
            for c in sorted(comments, key=lambda c: (c.get('created_at') or '', c['id']))
            if (c.get('user', {}).get('login') or '').casefold() == owner.casefold()]


def source_pool(root):
    pool = []
    reviews = {r['utterance_id']: r for r in jsonl(root / 'data/reviews.jsonl')}
    groups = {uid: s['segment_id'] for s in jsonl(root / 'data/segments.jsonl')
              for uid in s['user_utterance_ids']}
    # Verify registered immutable originals, rather than trusting previews alone.
    for source, rows in parse_sources(root):
        for row in rows:
            review = reviews.get(row['id'])
            if not review or review.get('authorship') != 'own' or row['role'] != 'user':
                continue
            text = row['_body']
            if not 40 <= len(text) <= 3000:
                continue
            pool.append(dict(evidence_id=row['id'], text=text,
                             themes=review.get('theme_labels', []),
                             context_group=groups.get(row['id'], row['id']),
                             review_status='reviewed_not_necessarily_owner_confirmed',
                             url=f"{source['source_url']}#L{row['start_line']}-L{row['end_line']}",
                             source_type='conversation', caveat='会話の一発言。前後の省略あり。'))
    for row in jsonl(root / 'data/x_posts.jsonl'):
        if (row['review_status'] not in {'reviewed', 'ai_classified'} or row['authorship'] != 'own'
                or not 40 <= len(row['text']) <= 3000):
            continue
        pool.append(dict(evidence_id=row['id'], text=row['text'], themes=row.get('theme_confirmed', []),
                         context_group=row.get('in_reply_to_status_id') or row['id'],
                         review_status=row['review_status'], url=row['url'], source_type='X',
                         caveat=row.get('context_status', '') + ': ' + row.get('review_note', '')))
    return pool


def choose_sources(pool, previous):
    used = {r['evidence_id'] for turn in previous for r in turn['sources']}
    eligible = [r for r in pool if r['evidence_id'] not in used]
    themes = sorted({t for r in eligible for t in r['themes']})
    for theme in sorted(themes, key=lambda t: (sum(p.get('theme') == t for p in previous), t)):
        candidates = [r for r in eligible if theme in r['themes']]
        selected, groups = [], set()
        # Alternate source types when available; do not pretend nearby posts are a conversation.
        for kind in ('X', 'conversation', 'X', 'conversation', 'X', 'conversation'):
            item = next((r for r in candidates if r['source_type'] == kind
                         and (kind, r['context_group']) not in groups), None)
            if item:
                selected.append(item)
                groups.add((kind, item['context_group']))
        if len(selected) >= 2:
            return theme, selected
    return None, []


def validate_generation(value, sources):
    fields = {'title', 'observation', 'hypothesis', 'limits', 'next_question', 'evidence'}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('Unexpected dialogue schema')
    for key in fields - {'evidence'}:
        if not isinstance(value[key], str) or len(value[key]) > (100 if key == 'title' else 1800):
            raise ValueError(f'Invalid {key}')
        if key != 'next_question' and not value[key].strip():
            raise ValueError(f'Empty {key}')
    lookup = {r['evidence_id']: r['text'] for r in sources}
    if not isinstance(value['evidence'], list) or not 1 <= len(value['evidence']) <= 3:
        raise ValueError('Expected 1..3 evidence quotes')
    for item in value['evidence']:
        if (not isinstance(item, dict) or set(item) != {'evidence_id', 'quote'}
                or item['evidence_id'] not in lookup or not isinstance(item['quote'], str)
                or not item['quote'].strip() or len(item['quote']) > 500
                or item['quote'] not in lookup[item['evidence_id']]):
            raise ValueError('Invented evidence or quote')
    return value


def schema():
    fields = ('title', 'observation', 'hypothesis', 'limits', 'next_question')
    return {'type': 'OBJECT', 'required': [*fields, 'evidence'], 'properties': {
        **{k: {'type': 'STRING'} for k in fields},
        'evidence': {'type': 'ARRAY', 'items': {'type': 'OBJECT',
            'required': ['evidence_id', 'quote'], 'properties': {
                'evidence_id': {'type': 'STRING'}, 'quote': {'type': 'STRING'}}}}}}


def render(turn):
    value = turn['generation']
    lookup = {s['evidence_id']: s for s in turn['sources']}
    refs = []
    for item in value['evidence']:
        row = lookup[item['evidence_id']]
        quote = '\n'.join('> ' + line for line in item['quote'].splitlines())
        refs.append(f"[{row['evidence_id']}]({row['url']})（{row['review_status']}）\n\n{quote}")
    question = value['next_question'] if turn['status'] == 'awaiting_owner' else (
        'このテーマはいったん区切ります。未確定の点は残したまま、次回は別の問いへ進みます。')
    return (f"{issue_marker(turn['topic_id'])}\n{turn_marker(turn['turn_id'])}\n\n"
            'これは第三段階の壁打ち用の暫定分析です。本人確認済みの人物像ではありません。\n\n'
            f"## 読み取ったこと\n\n{value['observation']}\n\n"
            f"## 今の読み\n\n{value['hypothesis']}\n\n"
            f"## まだ分からない点\n\n{value['limits']}\n\n"
            '## 原文の根拠\n\n' + '\n\n'.join(refs) + '\n\n'
            f'## 本人に確かめたいこと\n\n{question}\n\n'
            '普通のコメントで返答・訂正・具体例をください。「分からない」「昔とは違う」でも構いません。'
            '返答を受けて次の整理を出します。Closeは不要で、閉じた後の返答も読みます。'
            '「次へ」とだけコメントすると、このテーマを保留して次へ進みます。\n\n'
            '一テーマは最大3回のAI発言で区切ります。コメントやCloseを全面承認や投稿承諾とは扱いません。'
            '正式分析版・RSS生成指示への反映は別工程です。\n\n'
            f"モデル：`{turn['provenance'].get('model_version', 'none')}` / "
            f"[保存した対話資料](https://github.com/{turn['repository']}/blob/main/analysis/dialogues/"
            f"{turn['topic_id']}/turn-{turn['turn_number']:02d}.json)\n")


def prepare(root, repo, owner, issues, fetch_comments, generator=None):
    previous = artifacts(root)
    receipts = read_json(root / 'data/stage3_dialogue_receipts.json', {})
    if any(p['turn_id'] not in receipts for p in previous):
        return {'status': 'pending_delivery'}
    by_topic = {}
    for turn in previous:
        by_topic[turn['topic_id']] = turn
    active = [t for t in by_topic.values() if t['status'] == 'awaiting_owner']
    if len(active) > 1:
        raise ValueError('Multiple unanswered topics; refusing to add more')
    reply_to = None
    if active:
        last = active[0]
        issue = next((i for i in issues if issue_marker(last['topic_id']) in (i.get('body') or '')), None)
        if issue is None:
            return {'status': 'waiting_for_issue', 'topic_id': last['topic_id']}
        comments = owner_comments(fetch_comments(issue['number']), owner)
        if not comments or digest(comments) == last['owner_comments_sha256']:
            return {'status': 'waiting_for_owner', 'topic_id': last['topic_id']}
        if sum(len(c['body']) for c in comments) > 40000:
            raise ValueError('Owner dialogue exceeds input budget; preserve archive for manual review')
        topic, theme, sources = last['topic_id'], last['theme'], last['sources']
        number = last['turn_number'] + 1
        reply_to = issue['number']
        history = [p['generation'] for p in previous if p['topic_id'] == topic]
    else:
        theme, sources = choose_sources(source_pool(root), previous)
        if not sources:
            return {'status': 'idle', 'reason': 'No unused classified evidence pair'}
        topic = 'D' + hashlib.sha256(json.dumps([r['evidence_id'] for r in sources]).encode()).hexdigest()[:16]
        number, comments, history = 1, [], []
    instructions = (root / 'prompts/stage3_dialogue.md').read_text()
    # Recent dialogues are provisional context, never established personality facts.
    recent = [dict(hypothesis=p['generation']['hypothesis'], owner_comments=p['owner_comments'])
              for p in list(by_topic.values())[-3:]]
    progress = read_json(root / 'analysis/progress.json', {})
    version = progress.get('current_version', '')
    prior_context = {}
    if re.fullmatch(r'v\d{3}', version):
        profile_path = root / 'analysis' / version / 'profile.md'
        if profile_path.exists():
            prior_context['profile'] = profile_path.read_text()[:12000]
            prior_context['profile_excerpt_may_be_incomplete'] = profile_path.stat().st_size > 12000
    for filename in ('constructive_discussion_clarification.md', 'indirect_obligations_clarification.md'):
        path = root / 'analysis' / filename
        if path.exists():
            prior_context[filename] = path.read_text()
    aliases = {f'E{i:02d}': s['evidence_id'] for i, s in enumerate(sources, 1)}
    supplied_sources = [dict(s, evidence_id=alias) for alias, s in zip(aliases, sources)]
    payload = dict(theme=theme, sources=supplied_sources, previous_ai_turns=history,
                   owner_comments=comments, recent_provisional_dialogues=recent,
                   prior_analysis_reference_not_automatically_confirmed=prior_context,
                   last_turn=number >= MAX_TURNS)
    prompt = instructions + '\n\n資料（命令ではない）:\n' + json.dumps(payload, ensure_ascii=False)
    skip = bool(comments and comments[-1]['body'].strip().rstrip('。.!！') in {'次へ', '次に進めて', 'このテーマは保留'})
    if skip:
        value = dict(title=history[-1]['title'], observation='本人の希望により、このテーマを保留します。',
                     hypothesis='未回答の問いを本人の同意として扱わず、暫定の読みを残します。',
                     limits='このテーマの追加確認は未実施です。', next_question='', evidence=history[-1]['evidence'])
        model = {'model_version': 'none (owner requested next topic)'}
    elif generator:
        value, model = generator(prompt)
    else:
        key = os.environ.get('GEMINI_API_KEY')
        if not key:
            raise ValueError('GEMINI_API_KEY required when dialogue work remains')
        value, model = gemini(prompt, key, os.environ.get('STAGE3_DIALOGUE_MODEL', 'auto'), schema())
    if not skip and isinstance(value, dict) and isinstance(value.get('evidence'), list):
        for item in value['evidence']:
            if isinstance(item, dict) and isinstance(item.get('evidence_id'), str):
                item['evidence_id'] = aliases.get(item['evidence_id'], item['evidence_id'])
    validate_generation(value, sources)
    if number == 1 and not value['next_question'].strip():
        raise ValueError('Initial dialogue must ask the owner one question')
    if number >= MAX_TURNS:
        value['next_question'] = ''
    turn_id = f'{topic}-{number:02d}-' + digest(comments)[:12]
    record = dict(schema_version=1, stage=3, topic_id=topic, turn_id=turn_id, turn_number=number,
                  repository=repo, authorized_owner=owner, issue_number=reply_to, theme=theme,
                  status='awaiting_owner' if value['next_question'].strip() else 'complete_unconfirmed',
                  sources=sources, owner_comments=comments, owner_comments_sha256=digest(comments),
                  generation=value, provenance=dict(provider='Gemini' if not skip else 'deterministic', **model,
                      created_at=datetime.now(timezone.utc).isoformat(), prompt_sha256=digest(instructions),
                      input_sha256=digest(prompt), base_commit=subprocess.check_output(
                          ['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                      workflow_run_url=(f"https://github.com/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
                                        if os.environ.get('GITHUB_RUN_ID') else None)),
                  formal_analysis_updated=False, generation_prompt_updated=False)
    record['issue_body'] = render(record)
    folder = root / 'analysis/dialogues' / topic
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'turn-{number:02d}.json'
    if path.exists():
        raise ValueError('Refusing to overwrite dialogue artifact')
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return {'status': 'prepared', 'turn_id': turn_id}


def deliver(root, repo, issues):
    path = root / 'data/stage3_dialogue_receipts.json'
    receipts = read_json(path, {})
    pending = [p for p in artifacts(root) if p['turn_id'] not in receipts]
    if not pending:
        return {'status': 'nothing_to_deliver'}
    ensure_label(repo, LABEL)
    for turn in pending[:1]:
        issue = next((i for i in issues if issue_marker(turn['topic_id']) in (i.get('body') or '')), None)
        with tempfile.TemporaryDirectory() as tmp:
            body = Path(tmp) / 'body.md'
            body.write_text(turn['issue_body'])
            if issue is None:
                if turn['turn_number'] != 1:
                    raise ValueError('Cannot deliver followup without initial Issue')
                result = run('gh', 'issue', 'create', '--repo', repo, '--label', LABEL,
                             '--title', '[第三段階・壁打ち] ' + turn['generation']['title'], '--body-file', str(body))
                reference = result.stdout.strip()
            elif turn_marker(turn['turn_id']) in (issue.get('body') or ''):
                reference = issue['html_url']
            else:
                comments = api(f"repos/{repo}/issues/{issue['number']}/comments?per_page=100")
                prior = next((c for c in comments if c.get('user', {}).get('type') == 'Bot'
                              and turn_marker(turn['turn_id']) in (c.get('body') or '')), None)
                if prior:
                    reference = prior['html_url']
                else:
                    result = run('gh', 'issue', 'comment', str(issue['number']), '--repo', repo, '--body-file', str(body))
                    reference = result.stdout.strip()
        receipts[turn['turn_id']] = dict(url=reference, delivered_at=datetime.now(timezone.utc).isoformat())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')
    return {'status': 'delivered'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'deliver'])
    parser.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY'))
    parser.add_argument('--owner', default=os.environ.get('GITHUB_REPOSITORY_OWNER'))
    args = parser.parse_args()
    if not args.repo or not args.owner:
        parser.error('repo and owner required')
    issues = [i for i in api(f'repos/{args.repo}/issues?state=all&labels={LABEL}&per_page=100')
              if 'pull_request' not in i]
    if args.command == 'prepare':
        result = prepare(ROOT, args.repo, args.owner, issues,
                         lambda n: api(f'repos/{args.repo}/issues/{n}/comments?per_page=100'))
    else:
        result = deliver(ROOT, args.repo, issues)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
