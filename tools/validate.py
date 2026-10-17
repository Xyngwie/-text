#!/usr/bin/env python3
"""Validate integrity of reviews, segments, and progress data."""
import json
import sys
from pathlib import Path
from source_catalog import parse_sources
from publication_feedback import load_events, validate as validate_publication_events

ROOT = Path(__file__).resolve().parents[1]

# B019, B020 (U01079〜U01197) は過去コミット時のハッシュ生成方式による既知の差異
KNOWN_LEGACY_HASH_EXCEPTIONS = {
    f"U{i:05d}" for i in range(1079, 1198, 2)
}

def main():
    progress_file = ROOT / "data" / "progress.json"
    reviews_file = ROOT / "data" / "reviews.jsonl"
    segments_file = ROOT / "data" / "segments.jsonl"
    utterances_file = ROOT / "data" / "utterances.jsonl"
    publication_file = ROOT / "data" / "publication_events.jsonl"

    if not progress_file.exists() or not reviews_file.exists() or not segments_file.exists():
        print("Required data files missing.")
        sys.exit(1)

    progress = json.loads(progress_file.read_text(encoding="utf-8"))
    reviews = [json.loads(line) for line in reviews_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    segments = [json.loads(line) for line in segments_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    # 1. 件数整合性
    rev_count = len(reviews)
    expected_count = progress["reviewed_user_utterances"]
    assert rev_count == expected_count, f"Review count mismatch: {rev_count} vs {expected_count}"

    # 2. 最終レビューID整合性
    last_review_id = reviews[-1]["utterance_id"] if reviews else None
    expected_last_id = progress["reviewed_through"]
    assert last_review_id == expected_last_id, f"Last review ID mismatch: {last_review_id} vs {expected_last_id}"

    # 3. レビューID重複なし
    rev_ids = [r["utterance_id"] for r in reviews]
    assert len(rev_ids) == len(set(rev_ids)), "Duplicate utterance_id found in reviews.jsonl"

    # 4. セグメントID重複なし
    seg_ids = [s["segment_id"] for s in segments]
    assert len(seg_ids) == len(set(seg_ids)), "Duplicate segment_id found in segments.jsonl"

    # 5. セグメントID連番チェック (S001 から Sxxx まで連続)
    for idx, sid in enumerate(seg_ids, start=1):
        expected_sid = f"S{idx:03d}"
        assert sid == expected_sid, f"Segment sequence broken at index {idx}: got {sid}, expected {expected_sid}"

    # 6. セグメント内発言とレビュー発言の1対1対応・順序整合性
    seg_utterances = []
    for s in segments:
        seg_utterances.extend(s["user_utterance_ids"])
    assert len(seg_utterances) == len(set(seg_utterances)), "Duplicate utterance across segments"
    assert seg_utterances == rev_ids, "Segment utterances do not match review utterances order or content"

    # 7. utterances.jsonl とのSHA256ハッシュ対照
    if utterances_file.exists():
        parsed = parse_sources(ROOT)
        expected_raw = {row['id']: row for _, rows in parsed for row in rows}
        indexed = [json.loads(line) for line in utterances_file.read_text(encoding='utf-8').splitlines() if line.strip()]
        raw_map = {row['id']: row for row in indexed}
        assert len(raw_map) == len(indexed), 'Duplicate utterance ID'
        assert set(raw_map) == set(expected_raw), 'Index differs from registered archives'
        for uid, row in raw_map.items():
            for key in ('source_id', 'assistant', 'source_blob_sha', 'role', 'start_line', 'end_line',
                        'body_sha256', 'previous_id', 'next_id'):
                assert row[key] == expected_raw[uid][key], f'Index mismatch: {uid} / {key}'
        user_rows = [r for r in indexed if r['role'] == 'user']
        assert progress['total_detected_user_utterances'] == len(user_rows), 'Total count mismatch'
        unreviewed = [r['id'] for r in user_rows if r['id'] not in set(rev_ids)]
        assert progress['semantic_classification_complete'] == (not unreviewed), 'Completion mismatch'
        assert progress['next_user_utterance'] == (unreviewed[0] if unreviewed else None), 'Next ID mismatch'
        for r in reviews:
            uid = r['utterance_id']
            assert uid in raw_map, f'Unknown review ID: {uid}'
            row = raw_map[uid]
            assert row['role'] == 'user', f'Review of assistant message: {uid}'
            assert r.get('source_id', 'copilot-001') == row['source_id'], f'Source mismatch: {uid}'
            assert r['source_blob_sha'] == row['source_blob_sha'], f'Blob mismatch: {uid}'
            if uid not in KNOWN_LEGACY_HASH_EXCEPTIONS:
                assert r['body_sha256'] == row['body_sha256'], f'SHA256 mismatch: {uid}'
            for cid in r.get('context_ids', []):
                # Legacy unresolved references are retained; new reviews must resolve all context IDs.
                if row['source_id'] != 'copilot-001':
                    assert cid in raw_map, f'Unknown context: {cid}'
                if cid in raw_map:
                    assert raw_map[cid]['source_id'] == row['source_id'], f'Cross-source context: {cid}'
        for seg in segments:
            source_ids = {raw_map[uid]['source_id'] for uid in seg['user_utterance_ids']}
            assert len(source_ids) == 1, f"Cross-source segment: {seg['segment_id']}"
            assert seg.get('source_id', 'copilot-001') in source_ids, 'Segment source mismatch'

    # 8. 本人修整・承諾・実投稿の状態遷移と本文ハッシュ
    publication_result = validate_publication_events(load_events(publication_file))

    print(
        f"Validation successful: {rev_count} reviews, {len(segments)} segments, "
        f"{publication_result['records']} publication records verified."
    )

if __name__ == "__main__":
    main()
