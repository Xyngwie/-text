"""Parse immutable conversation archives with source-scoped, stable IDs."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote


def parse_sources(root):
    config = json.loads((root / 'data/sources.json').read_text(encoding='utf-8'))
    if config['schema_version'] != 1:
        raise ValueError('Unsupported sources schema')
    result, ids, paths, hashes, prefixes = [], set(), set(), set(), set()
    for entry in config['sources']:
        source = dict(entry)
        sid, path, prefix = source['source_id'], source['path'], source['id_prefix']
        if not re.fullmatch(r'[a-z][a-z0-9-]*', sid):
            raise ValueError(f'Invalid source_id: {sid}')
        if prefix != sid + ':' and not (sid == 'copilot-001' and prefix == ''):
            raise ValueError(f'Invalid ID namespace: {sid}')
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root.resolve()) or Path(path).is_absolute():
            raise ValueError(f'Archive must be inside repository: {path}')
        if sid in ids or path in paths or prefix in prefixes:
            raise ValueError('Duplicate source ID, path, or namespace')
        ids.add(sid); paths.add(path); prefixes.add(prefix)
        raw = resolved.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != source['source_sha256']:
            raise ValueError(f'Archive changed; register a new source instead: {sid}')
        if digest in hashes:
            raise ValueError(f'Duplicate archive: {sid}')
        hashes.add(digest)
        commit = source['source_commit']
        if not re.fullmatch(r'[0-9a-f]{40}', commit):
            raise ValueError(f'Archive commit must be pinned: {sid}')
        pinned = subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=root)
        blob = subprocess.check_output(['git', 'rev-parse', f'{commit}:{path}'], cwd=root, text=True).strip()
        if pinned != raw or blob != source['source_blob_sha']:
            raise ValueError(f'Pinned archive does not match: {sid}')
        markers = source['speaker_markers']
        if not markers or 'user' not in markers.values() or not set(markers.values()) <= {'user', 'assistant', 'copilot'}:
            raise ValueError(f'Invalid speaker markers: {sid}')
        lines = raw.decode('utf-8').splitlines()
        marks = [(i, markers[line.strip()]) for i, line in enumerate(lines) if line.strip() in markers]
        if not marks:
            raise ValueError(f'No speaker boundaries found: {sid}')
        source.update(bytes=len(raw), line_count=len(lines),
                      preamble_lines=[1, marks[0][0]] if marks[0][0] else None,
                      source_url=f'https://github.com/Xyngwie/-text/blob/{commit}/{quote(path)}')
        rows = []
        for pos, (start, role) in enumerate(marks):
            stop = marks[pos + 1][0] if pos + 1 < len(marks) else len(lines)
            body = '\n'.join(lines[start + 1:stop]).strip()
            rows.append(dict(id=f'{prefix}U{pos + 1:05d}', source_id=sid,
                             assistant=source['assistant'], source_blob_sha=blob,
                             role=role, start_line=start + 1, end_line=stop,
                             body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                             preview=' '.join(body.split())[:160],
                             previous_id=f'{prefix}U{pos:05d}' if pos else None,
                             next_id=f'{prefix}U{pos + 2:05d}' if pos + 1 < len(marks) else None,
                             _body=body))
        result.append((source, rows))
    if not result or result[0][0]['source_id'] != 'copilot-001':
        raise ValueError('Keep legacy archive first')
    return result
