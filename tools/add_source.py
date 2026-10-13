#!/usr/bin/env python3
"""Register a committed UTF-8 conversation archive without changing existing IDs."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from source_catalog import parse_sources

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-id', required=True)
    parser.add_argument('--path', required=True)
    parser.add_argument('--assistant', required=True)
    parser.add_argument('--user-marker', required=True)
    parser.add_argument('--assistant-marker', required=True)
    args = parser.parse_args()
    if args.user_marker == args.assistant_marker:
        parser.error('Speaker markers must differ')
    path = Path(args.path)
    if path.is_absolute() or not (ROOT / path).resolve().is_relative_to(ROOT):
        parser.error('Archive must be inside repository')
    relative = path.as_posix()
    commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', relative], cwd=ROOT, text=True).strip()
    if not commit:
        parser.error('Commit the archive before registration')
    raw = (ROOT / path).read_bytes()
    pinned = subprocess.check_output(['git', 'show', f'{commit}:{relative}'], cwd=ROOT)
    if raw != pinned:
        parser.error('Archive has uncommitted changes')
    blob = subprocess.check_output(['git', 'rev-parse', f'{commit}:{relative}'], cwd=ROOT, text=True).strip()
    registry = ROOT / 'data/sources.json'
    previous = registry.read_bytes()
    config = json.loads(previous)
    config['sources'].append(dict(source_id=args.source_id, path=relative,
                                  assistant=args.assistant, id_prefix=args.source_id + ':',
                                  source_commit=commit, source_blob_sha=blob,
                                  source_sha256=hashlib.sha256(raw).hexdigest(),
                                  speaker_markers={args.user_marker: 'user', args.assistant_marker: 'assistant'}))
    try:
        registry.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        parse_sources(ROOT)
    except Exception:
        registry.write_bytes(previous)
        raise
    print(f'Registered {args.source_id}. Run tools/build_index.py, then tools/validate.py.')


if __name__ == '__main__':
    main()
