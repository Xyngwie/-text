#!/usr/bin/env python3
"""Pick news candidates for short stories and record which ones were used.

This is separate from the RSS value-slide agent: it reads
config/story_rss_sources.json, never creates Issues, and keeps its own
append-only registry at stories/registry.jsonl.

  python3 tools/story_candidates.py candidates [--max-items 8]
  python3 tools/story_candidates.py register --candidate-id rss-... --story stories/2026/11/xxx.md
  python3 tools/story_candidates.py check
"""

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rss_agent import balanced_candidates, collect  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/story_rss_sources.json'
REGISTRY = ROOT / 'stories/registry.jsonl'
DISCLAIMER = '※この物語は、下記のニュース記事から着想を得たフィクションです。登場人物や場面は創作であり、実在の人物とは関係ありません。'
POST_BLOCK = re.compile(r'^## 投稿用\n\n```text\n(.*?)\n```', re.MULTILINE | re.DOTALL)


def post_problems(text, link):
    """The copy-paste block must end with the fiction disclaimer and the source URL."""
    match = POST_BLOCK.search(text)
    if not match:
        return ['missing "## 投稿用" text block']
    lines = match.group(1).rstrip('\n').split('\n')
    problems = []
    if len(lines) < 4:
        problems.append('post block too short')
    elif lines[-2] != DISCLAIMER:
        problems.append('post block must end with the fiction disclaimer line')
    if lines[-1] != f'元記事：{link}':
        problems.append('post block must end with "元記事：<URL>"')
    return problems


def load_registry(path=REGISTRY):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def apply_excluded_terms(candidates, terms):
    kept = []
    for row in candidates:
        text = (row['title'] + ' ' + row['description']).casefold()
        if not any(term.casefold() in text for term in terms):
            kept.append(row)
    return kept


def pick(config, registry, max_items, timeout=20, fetcher=None):
    kwargs = {'fetcher': fetcher} if fetcher else {}
    result = collect(config, timeout, **kwargs)
    candidates = apply_excluded_terms(result['candidates'], config.get('excluded_terms', []))
    used = {row['candidate_id'] for row in registry}
    used_titles = {row.get('title') for row in registry}
    candidates = [row for row in candidates if row['title'] not in used_titles]
    last_seen = {}
    for row in registry:
        category = row.get('category')
        if category:
            last_seen[category] = max(last_seen.get(category, ''), row.get('recorded_at', ''))
    chosen = balanced_candidates(candidates, max_items, config.get('category_order', []), used, last_seen)
    return {'candidates': chosen, 'errors': result['errors'],
            'source_diagnostics': result['source_diagnostics'],
            'category_last_used_at': last_seen}


def register(registry_path, candidate, story_path):
    rows = load_registry(registry_path)
    if any(row['candidate_id'] == candidate['candidate_id'] for row in rows):
        raise SystemExit(f"already registered: {candidate['candidate_id']}")
    if not (ROOT / story_path).exists():
        raise SystemExit(f'story file not found: {story_path}')
    problems = post_problems((ROOT / story_path).read_text(encoding='utf-8'), candidate['link'])
    if problems:
        raise SystemExit(f'{story_path}: ' + '; '.join(problems))
    entry = {
        'candidate_id': candidate['candidate_id'],
        'category': candidate.get('category'),
        'title': candidate['title'],
        'publisher': candidate.get('publisher'),
        'link': candidate['link'],
        'published_at': candidate.get('published_at'),
        'story_path': str(story_path),
        'recorded_at': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry


def check(registry_path=REGISTRY):
    rows = load_registry(registry_path)
    ids = [row['candidate_id'] for row in rows]
    problems = []
    if len(ids) != len(set(ids)):
        problems.append('duplicate candidate_id in registry')
    for row in rows:
        path = ROOT / row['story_path']
        if not path.exists():
            problems.append(f"missing story file: {row['story_path']}")
            continue
        problems.extend(f"{row['story_path']}: {problem}"
                        for problem in post_problems(path.read_text(encoding='utf-8'), row['link']))
    return problems


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    c = sub.add_parser('candidates')
    c.add_argument('--max-items', type=int, default=8)
    c.add_argument('--timeout', type=int, default=20)
    c.add_argument('--output', type=Path)
    r = sub.add_parser('register')
    r.add_argument('--candidates', type=Path, required=True, help='JSON written by the candidates command')
    r.add_argument('--candidate-id', required=True)
    r.add_argument('--story', type=Path, required=True, help='story file path relative to the repository root')
    sub.add_parser('check')
    args = parser.parse_args()

    if args.command == 'candidates':
        config = json.loads(CONFIG.read_text(encoding='utf-8'))
        result = pick(config, load_registry(), args.max_items, args.timeout)
        encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding='utf-8')
        else:
            sys.stdout.write(encoded)
        if not result['candidates']:
            raise SystemExit(1)
    elif args.command == 'register':
        data = json.loads(args.candidates.read_text(encoding='utf-8'))
        match = [row for row in data['candidates'] if row['candidate_id'] == args.candidate_id]
        if not match:
            raise SystemExit(f'candidate not in {args.candidates}: {args.candidate_id}')
        print(json.dumps(register(REGISTRY, match[0], args.story), ensure_ascii=False))
    else:
        problems = check()
        for problem in problems:
            print(problem)
        if problems:
            raise SystemExit(1)
        print('stories registry OK')


if __name__ == '__main__':
    main()
