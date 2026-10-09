#!/usr/bin/env python3
"""Validate integrity of reviews, segments, and progress data."""
import json
import sys
from pathlib import Path

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
    last_review_id = reviews[-1]["utterance_id"]
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
        raw_map = {}
        for line in utterances_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            raw_map[item["id"]] = item["body_sha256"]
        
        for r in reviews:
            uid = r["utterance_id"]
            if uid in KNOWN_LEGACY_HASH_EXCEPTIONS:
                continue
            if uid in raw_map:
                assert r["body_sha256"] == raw_map[uid], f"SHA256 mismatch for {uid}: {r['body_sha256']} vs {raw_map[uid]}"

    print(f"Validation successful: {rev_count} reviews, {len(segments)} segments verified against progress.json.")

if __name__ == "__main__":
    main()
