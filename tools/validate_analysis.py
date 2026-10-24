#!/usr/bin/env python3
"""Validate analysis provenance against its pinned classification snapshot."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(version='v001', root=ROOT):
    assert re.fullmatch(r'v\d{3}', version), 'Invalid version'
    folder = root / 'analysis' / version
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['version'] == version
    commit = manifest['base_commit']
    assert re.fullmatch(r'[0-9a-f]{40}', commit), 'Snapshot must be pinned'

    def pinned(path, revision=commit):
        return subprocess.check_output(['git', 'show', f'{revision}:{path}'], cwd=root)

    def jsonl(raw):
        return [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]

    inputs = {}
    for path, digest in manifest['input_files'].items():
        data = pinned(path)
        assert hashlib.sha256(data).hexdigest() == digest, f'Snapshot mismatch: {path}'
        inputs[path] = data
    required = {'data/sources.json', 'data/reviews.jsonl', 'data/segments.jsonl',
                'data/utterances.jsonl', 'data/taxonomy.json'}
    assert set(inputs) == required, 'Missing snapshot input'
    for path, digest in manifest.get('supplemental_input_files', {}).items():
        assert hashlib.sha256(pinned(path)).hexdigest() == digest, f'Supplemental snapshot mismatch: {path}'
    artifact = manifest.get('calibration_artifact')
    if artifact:
        assert hashlib.sha256((root / artifact['path']).read_bytes()).hexdigest() == artifact['sha256'], 'Calibration artifact mismatch'
    sources = {s['source_id']: s for s in manifest['sources']}
    assert manifest['sources'] == json.loads(inputs['data/sources.json'])['sources']
    archives = {}
    for sid, s in sources.items():
        raw = pinned(s.get('source_commit_path', s['path']), s['source_commit'])
        assert hashlib.sha256(raw).hexdigest() == s['source_sha256'], f'Source mismatch: {sid}'
        blob = subprocess.check_output(['git', 'hash-object', '--stdin'], input=raw, cwd=root).decode().strip()
        assert blob == s['source_blob_sha'], f'Blob mismatch: {sid}'
        archives[sid] = raw.decode('utf-8').splitlines()
    reviews = jsonl(inputs['data/reviews.jsonl'])
    segments = jsonl(inputs['data/segments.jsonl'])
    utterances = jsonl(inputs['data/utterances.jsonl'])
    smap = {s['segment_id']: s for s in segments}
    umap = {u['id']: u for u in utterances}
    rmap = {r['utterance_id']: r for r in reviews}
    assert manifest['classified_user_utterances'] == len(reviews)
    assert manifest['classified_segments'] == len(segments)

    split = json.loads((folder / 'split.json').read_text(encoding='utf-8'))
    assert split['version'] == version
    grouped = {}
    group_ids = set()
    for group in split['groups']:
        assert group['group_id'] not in group_ids
        group_ids.add(group['group_id'])
        assert group['partition'] in {'analysis_pool', 'reuse_reserve'}
        assert group['is_unseen'] is False, 'Retrospective reserve cannot be unseen'
        for sid in group['segment_ids']:
            assert sid in smap and sid not in grouped, f'Unknown or repeated segment: {sid}'
            grouped[sid] = group
    assert set(grouped) == set(smap), 'Split must cover entire snapshot'
    for s in segments:
        for rel in s.get('related_segment_ids', []):
            if rel in smap:
                assert grouped[rel]['group_id'] == grouped[s['segment_id']]['group_id'], 'Related case split'
    for link in split['manual_links']:
        assert len({grouped[sid]['group_id'] for sid in link['segment_ids']}) == 1, 'Manual link split'
    for part, key in [('analysis_pool', 'analysis_pool_segment_count'), ('reuse_reserve', 'reserve_segment_count')]:
        assert sum(g['partition'] == part for g in grouped.values()) == manifest[key]

    episodes = jsonl((folder / 'episodes.jsonl').read_bytes())
    emap = {e['episode_id']: e for e in episodes}
    assert len(emap) == len(episodes) == manifest['episode_count']
    coded_ids, coded_segments = set(), set()
    uidseg = {uid: s['segment_id'] for s in segments for uid in s['user_utterance_ids']}
    for e in episodes:
        assert e['source_id'] in sources
        assert e['assistant'] == sources[e['source_id']]['assistant']
        assert e['evidence'] and e['segment_ids']
        assert e['coding_status'] in {'included', 'excluded_ambiguous_question'}
        for sid in e['segment_ids']:
            assert grouped[sid]['partition'] == 'analysis_pool', f'Reserved evidence: {sid}'
            assert grouped[sid]['group_id'] == e['group_id']
            coded_segments.add(sid)
        for ref in e['evidence']:
            uid = ref['utterance_id']
            assert uid in rmap and uid in umap
            u, r = umap[uid], rmap[uid]
            assert u['role'] == 'user' and r['authorship'] == ref['authorship'] == 'own'
            assert u['source_id'] == e['source_id'] and uidseg[uid] in e['segment_ids']
            assert ref['body_sha256'] == u['body_sha256']
            assert ref['source_blob_sha'] == sources[e['source_id']]['source_blob_sha']
            assert ref['lines'] == [u['start_line'] + 1, u['end_line']]
            raw_lines = archives[e['source_id']]
            body = '\n'.join(raw_lines[u['start_line']:u['end_line']]).strip()
            assert hashlib.sha256(body.encode()).hexdigest() == ref['body_sha256']
            assert ref['quote'] and ref['quote'] in body, f'Quote mismatch: {uid}'
            coded_ids.add(uid)
        expected_themes = {t for ref in e['evidence'] for t in rmap[ref['utterance_id']]['theme_labels']}
        assert set(e['theme_labels']) == expected_themes
        for cid in e['context_ids']:
            assert cid in umap and umap[cid]['source_id'] == e['source_id']
            if cid in uidseg:
                assert grouped[uidseg[cid]]['partition'] == 'analysis_pool', f'Reserved context: {cid}'
    assert len(coded_ids) == manifest['coded_utterance_count']
    assert len(coded_segments) == manifest['coded_segment_count']
    assert set(manifest['reviewed_utterance_ids']) == coded_ids
    assert set(manifest['reviewed_segment_ids']) == coded_segments

    if 'parent_version' in manifest:
        parent = manifest['parent_version']
        assert re.fullmatch(r'v\d{3}', parent) and parent < version, 'Invalid parent version'
        assert manifest.get('parent_artifacts'), 'Missing parent provenance'
        for path, digest in manifest['parent_artifacts'].items():
            assert Path(path).parent.as_posix() == f'analysis/{parent}', 'Invalid parent artifact path'
            assert hashlib.sha256(pinned(path)).hexdigest() == digest, f'Parent snapshot mismatch: {path}'
            assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, f'Historical version changed: {path}'
        original = jsonl(pinned(f'analysis/{parent}/episodes.jsonl'))
        for original_episode in original:
            assert emap.get(original_episode['episode_id']) == original_episode, 'Historical episode changed'
        parent_split = json.loads(pinned(f'analysis/{parent}/split.json'))
        old_assignment = {sid: g['partition'] for g in parent_split['groups'] for sid in g['segment_ids']}
        new_assignment = {sid: g['partition'] for sid, g in grouped.items()}
        assert old_assignment == {sid: new_assignment.get(sid) for sid in old_assignment}, 'Historical reserve changed'
        assert set(new_assignment) - set(old_assignment) == set(manifest.get('added_segment_ids', [])), 'Undocumented added segments'
        actual_added = set(emap) - {e['episode_id'] for e in original}
        assert set(manifest['added_episode_ids']) == actual_added, 'Added episode count mismatch'

    findings = json.loads((folder / 'findings.json').read_text(encoding='utf-8'))
    assert findings['version'] == version
    fids = set()
    for f in findings['findings']:
        assert f['finding_id'] not in fids
        fids.add(f['finding_id'])
        assert f['support_episodes'] and f['qualification_episodes']
        for eid in f['support_episodes'] + f['qualification_episodes']:
            assert eid in emap, f'Unknown episode: {eid}'
            assert emap[eid]['coding_status'] == 'included', f'Excluded episode used in finding: {eid}'
        for key in ('scope', 'boundary', 'evidence_strength', 'alternative_explanation', 'next_check'):
            assert f[key], f'Missing condition: {key}'
    # Check human-facing relative links and episode anchors as well.
    for path in [root / 'analysis/README.md', *folder.glob('*.md')]:
        text = path.read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^)]+)\)', text):
            if link.startswith(('https://', 'http://')):
                continue
            target, _, anchor = link.partition('#')
            assert (path.parent / target).exists(), f'Broken link: {path} / {link}'
            if anchor and target == 'cases.md':
                assert anchor.upper() in emap, f'Unknown episode anchor: {anchor}'
    return dict(version=version, episodes=len(episodes), coded_utterances=len(coded_ids),
                findings=len(fids), reserve_segments=manifest['reserve_segment_count'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='v001')
    args = parser.parse_args()
    print('Analysis validation successful: ' + json.dumps(validate(args.version), ensure_ascii=False))


if __name__ == '__main__':
    main()
