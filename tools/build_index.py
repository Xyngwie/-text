#!/usr/bin/env python3
"""Build traceable, integrated indexes reflecting confirmed reviews and provisional candidates.

Never edit the source archive. Uses only the Python standard library and git.
"""
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from source_catalog import parse_sources

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT

THEMES = {
    'politics': ('政治・行政・制度', ['政治', '選挙', '政党', '首相', '議員', '政権', '政府', '国会', '官僚', '民主主義']),
    'world': ('国際情勢・外交・紛争', ['戦争', '外交', 'ウクライナ', 'ロシア', 'イスラエル', '台湾', 'トランプ', '軍事', '関税']),
    'economy': ('経済・企業・労働', ['経済', '物価', '株価', '賃金', '雇用', '退職', '会社', '企業', '税金', 'ビジネス']),
    'society': ('社会・事件・情報環境', ['報道', 'ニュース', '事件', '犯罪', '詐欺', 'フィッシング', '炎上', '差別', 'SNS', 'メディア']),
    'ai': ('AI・対話・エージェント', ['AI', 'LLM', 'Copilot', 'こぴちー', 'ChatGPT', 'Grok', 'Claude', 'エージェント', 'A2A', 'プロンプト']),
    'software': ('開発・ソフトウェア・運用', ['GitHub', 'Github', 'コード', 'プログラム', 'デプロイ', 'JSON', 'API', 'アプリ', 'ブラウザ', 'サーバー']),
    'survey': ('測量・土地・登記', ['測量', '登記', '境界', '地目', '換地', '土地', '筆界', '建物', '調査士']),
    'games': ('ゲーム・設計・パズル', ['ゲーム', 'パズル', 'EXPLORE', 'SORT', 'TRADE', 'INVADE', 'RESTORE', 'HUB', 'Unity', '盤面']),
    'poker': ('ポーカー・確率・戦略', ['ポーカー', 'ソルバー', 'ポット', 'ベット', 'ブラフ', 'GTO', '1BB', 'オールイン', 'ハンド']),
    'science': ('科学・工学・仕組み', ['科学', '物理', '数学', '宇宙', '量子', 'エネルギー', '化学', '実験', '確率']),
    'culture': ('音楽・表現・文化', ['音楽', '歌', 'オタマトーン', 'アニメ', '漫画', '映画', '芸術', '創作', 'SUNO']),
    'food': ('食・街歩き・旅行', ['ラーメン', '担々麺', '激辛', 'そば', 'ニンニク', '昼食', '飲食', '旅行', '神田', '五反田']),
    'life': ('生活・身体・機器', ['身体', '健康', '睡眠', '除毛', 'スマホ', 'イヤホン', 'ヘッドホン', 'ガジェット', 'PC']),
    'thinking': ('思考・価値観・自己理解', ['思考', '価値観', '構造', '判断', '倫理', '哲学', '人格', '自分', '私について']),
}

# 過去レビューにおける表記揺れ・派生タグの正規化マップ
THEME_ALIASES = {
    'hardware': 'life',
    'game': 'games',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def escape_md_cell(text):
    if not text:
        return ''
    return str(text).replace('|', '\\|').replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;').replace('`', '\\`').strip()


def hits(text):
    found = {}
    for key, (_, words) in THEMES.items():
        terms = []
        for word in words:
            # ASCII abbreviations must be standalone; SORT must not match assorted.
            pattern = r'(?<![A-Za-z0-9_])' + re.escape(word) + r'(?![A-Za-z0-9_])' if word.isascii() else re.escape(word)
            if re.search(pattern, text, re.IGNORECASE):
                terms.append(word)
        if terms:
            found[key] = terms
    return found


def normalize_theme_label(label):
    return THEME_ALIASES.get(label, label)


def load_jsonl(path):
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def main():
    parsed_sources = parse_sources(ROOT)
    source_urls = {source['source_id']: source['source_url'] for source, _ in parsed_sources}

    # レビュー・セグメント・進捗データの読み込み
    reviews_list = load_jsonl(OUT / 'data' / 'reviews.jsonl')
    segments_list = load_jsonl(OUT / 'data' / 'segments.jsonl')
    reviews_map = {r['utterance_id']: r for r in reviews_list}

    # セグメント逆引きマップ (user_utterance_id -> segment)
    seg_map = {}
    for seg in segments_list:
        for uid in seg.get('user_utterance_ids', []):
            seg_map[uid] = seg

    # 発言レコードの生成
    records = []
    for source, utterances in parsed_sources:
        for utterance in utterances:
            uid = utterance['id']
            role = utterance['role']
            body = utterance.pop('_body')
            is_user = (role == 'user')
            is_reviewed = is_user and (uid in reviews_map)

            row = {
                **utterance,
                'theme_candidates': hits(body) if is_user else {},
                'review_status': 'reviewed' if is_reviewed else 'unreviewed',
                'date': reviews_map[uid].get('date') if is_reviewed else None,
            }

            if is_reviewed:
                rev = reviews_map[uid]
                row['theme_confirmed'] = rev.get('theme_labels', [])
                row['speech_act'] = rev.get('speech_act')
                row['news_relation'] = rev.get('news_relation')
                row['authorship'] = rev.get('authorship')
                row['batch_id'] = rev.get('batch_id')
                if uid in seg_map:
                    row['segment_id'] = seg_map[uid]['segment_id']

            records.append(row)

    # Reject stale or foreign reviews before writing any generated data.
    indexed = {r['id']: r for r in records}
    legacy = {f'U{i:05d}' for i in range(1079, 1198, 2)}
    for rev in reviews_list:
        uid = rev['utterance_id']
        if uid not in indexed or indexed[uid]['role'] != 'user':
            raise ValueError(f'Unknown/non-user review: {uid}')
        row = indexed[uid]
        if rev.get('source_id', 'copilot-001') != row['source_id'] or rev['source_blob_sha'] != row['source_blob_sha']:
            raise ValueError(f'Review source mismatch: {uid}')
        if uid not in legacy and rev['body_sha256'] != row['body_sha256']:
            raise ValueError(f'Review hash mismatch: {uid}')

    # 構造検証
    assert len({r['id'] for r in records}) == len(records)
    assert all(r['role'] == 'user' or not r['theme_candidates'] for r in records)

    (OUT / 'data').mkdir(exist_ok=True)
    (OUT / 'themes').mkdir(exist_ok=True)

    # 1. data/utterances.jsonl
    with (OUT / 'data' / 'utterances.jsonl').open('w', encoding='utf-8') as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')

    # 2. data/taxonomy.json
    dump(OUT / 'data' / 'taxonomy.json', {
        'status': 'integrated',
        'method': 'confirmed_reviews_and_literal_keyword_candidates',
        'themes': {k: {'label': label, 'keywords': words} for k, (label, words) in THEMES.items()},
    })

    # 3. 集計
    counts = Counter(r['role'] for r in records)
    user_records = [r for r in records if r['role'] == 'user']
    reviewed_records = [r for r in user_records if r['review_status'] == 'reviewed']
    unreviewed_records = [r for r in user_records if r['review_status'] == 'unreviewed']
    unclassified_unreviewed = [r for r in unreviewed_records if not r['theme_candidates']]

    # 4. data/source_manifest.json
    manifests = []
    for source, _ in parsed_sources:
        source_records = [r for r in records if r['source_id'] == source['source_id']]
        users = [r for r in source_records if r['role'] == 'user']
        reviewed = sum(r['review_status'] == 'reviewed' for r in users)
        manifests.append({**source, 'utterance_counts': dict(Counter(r['role'] for r in source_records)),
                          'reviewed_user_utterances': reviewed,
                          'unreviewed_user_utterances': len(users) - reviewed,
                          'semantic_classification_complete': reviewed == len(users)})
    dump(OUT / 'data' / 'source_manifest.json', {
        **manifests[0], 'source_path': manifests[0]['path'],
        'schema_version': 2, 'sources': manifests,
        'reviewed_user_utterances': len(reviewed_records),
        'unreviewed_user_utterances': len(unreviewed_records),
        'unclassified_user_utterances': len(unclassified_unreviewed),
        'date_policy': 'Unknown: no year inferred from relative or incomplete dates.',
        'parser_caveat': 'Exact speaker labels inside pasted text may be mistaken for boundaries; manual review required.',
    })
    progress_path = OUT / 'data' / 'progress.json'
    progress = json.loads(progress_path.read_text(encoding='utf-8'))
    progress.update(total_detected_user_utterances=len(user_records),
                    reviewed_user_utterances=len(reviewed_records),
                    reviewed_through=reviews_list[-1]['utterance_id'] if reviews_list else None,
                    next_user_utterance=unreviewed_records[0]['id'] if unreviewed_records else None,
                    semantic_classification_complete=not unreviewed_records,
                    sources={m['source_id']: {k: m[k] for k in
                             ('assistant', 'utterance_counts', 'reviewed_user_utterances',
                              'unreviewed_user_utterances', 'semantic_classification_complete')}
                             for m in manifests})
    dump(progress_path, progress)
    analysis_path = OUT / 'analysis' / 'progress.json'
    analysis = json.loads(analysis_path.read_text(encoding='utf-8')) if analysis_path.exists() else None
    stage4_summary = ('RSS・Issue・確定ログ取込パイプライン実装済み、本人試行を継続中。'
                      if analysis and analysis.get('stage4_status', '').startswith('pipeline_implemented')
                      else '未着手。')
    analysis_summary = (f"第3段階：分析継続中（{analysis['current_version']}）。[判断・口調の分析](analysis/README.md)。第4段階：{stage4_summary}"
                        if analysis else '第3段階以降のテーマ横断プロファイルとニュース反応モデルは未完了。')
    progress_md = [
        '# 分類の進捗', '',
        f'- 検出本人発言：{len(user_records):,}件。',
        f'- 文脈確認済み：{len(reviewed_records):,}件。未確認：{len(unreviewed_records):,}件。',
        f"- 最新バッチ：{progress.get('last_batch', 'なし')}。",
        f"- 次の開始位置：{progress['next_user_utterance'] or 'なし'}。",
        '- ' + analysis_summary,
        '', '## 原本ごとの進捗', '',
        '| 原本ID | LLM | 本人発言 | 確認済み | 未確認 | 第2段階 |',
        '|---|---|---:|---:|---:|---|',
    ]
    for m in manifests:
        progress_md.append(f"| {m['source_id']} | {escape_md_cell(m['assistant'])} | {m['utterance_counts'].get('user', 0)} | {m['reviewed_user_utterances']} | {m['unreviewed_user_utterances']} | {'完了' if m['semantic_classification_complete'] else '未完了'} |")
    progress_md.extend(['', '未解決の参照：' + '・'.join(progress.get('unresolved_references', [])),
                        '', '[原本の追加手順](docs/ADDING_CONVERSATIONS.md)。詳細は `data/progress.json`、`data/reviews.jsonl`、`data/segments.jsonl`。', ''])
    (OUT / 'PROGRESS.md').write_text('\n'.join(progress_md), encoding='utf-8')

    # 5. テーマごとの発言分類
    # theme_key -> list of confirmed records
    theme_confirmed = {k: [] for k in THEMES}
    # theme_key -> set of segment_ids
    theme_segments = {k: set() for k in THEMES}
    # theme_key -> list of unreviewed candidate records
    theme_candidates = {k: [] for k in THEMES}

    for r in user_records:
        uid = r['id']
        if r['review_status'] == 'reviewed':
            labels = r.get('theme_confirmed', [])
            for lbl in labels:
                norm_lbl = normalize_theme_label(lbl)
                if norm_lbl in theme_confirmed:
                    theme_confirmed[norm_lbl].append(r)
                    if 'segment_id' in r:
                        theme_segments[norm_lbl].add(r['segment_id'])
        else:
            for k in r['theme_candidates']:
                if k in theme_candidates:
                    theme_candidates[k].append(r)

    # 6. 各 themes/{key}.md の出力
    for key, (label, _) in THEMES.items():
        conf_list = theme_confirmed[key]
        cand_list = theme_candidates[key]
        seg_set = theme_segments[key]

        md = [
            f'# {label}',
            '',
            '原本リンクには出典ごとの固定コミットと行範囲を使用。',
            '前後のLLM回答も含めた文脈精査に基づく確定分類と、未精査のキーワード候補を掲載しています。',
            '',
            f'- **確定発言数**: {len(conf_list)}件',
            f'- **関連セグメント数**: {len(seg_set)}セグメント',
            f'- **未確認候補数**: {len(cand_list)}件',
            '',
            '## 1. 文脈確認済み発言（確定分類）',
            '',
        ]

        if conf_list:
            md.extend([
                '| 発言ID | 原文 | セグメント | 発言行為 (speech_act) | 区分 | 著者性 | 本人発言の冒頭抜粋 |',
                '|---|---|---|---|---|---|---|',
            ])
            for r in conf_list:
                uid = r['id']
                seg_info = ''
                if uid in seg_map:
                    seg = seg_map[uid]
                    sid = seg['segment_id']
                    bid = seg.get('batch_id', '')
                    title = escape_md_cell(seg.get('title', ''))
                    batch_link = f'../batches/{bid}.md' if bid else ''
                    seg_info = f'[{sid}: {title}]({batch_link})' if batch_link else f'{sid}: {title}'

                speech_act = escape_md_cell(r.get('speech_act', ''))
                news_rel = escape_md_cell(r.get('news_relation', ''))
                authorship = escape_md_cell(r.get('authorship', ''))
                preview = escape_md_cell(r['preview'])
                line_link = f"[L{r['start_line']}–{r['end_line']}]({source_urls[r['source_id']]}#L{r['start_line']}-L{r['end_line']})"
                md.append(f'| {uid} | {line_link} | {seg_info} | {speech_act} | {news_rel} | {authorship} | {preview} |')
        else:
            md.append('（現在、このテーマに確定された発言はありません。）')

        md.extend([
            '',
            '## 2. 未精査のキーワード候補（仮候補）',
            '',
        ])

        if cand_list:
            md.extend([
                '| 発言ID | 原文 | 一致語 | 本人発言の冒頭抜粋 |',
                '|---|---|---|---|',
            ])
            for r in cand_list:
                preview = escape_md_cell(r['preview'])
                words = ', '.join(r['theme_candidates'].get(key, []))
                line_link = f"[L{r['start_line']}–{r['end_line']}]({source_urls[r['source_id']]}#L{r['start_line']}-L{r['end_line']})"
                md.append(f'| {r["id"]} | {line_link} | {words} | {preview} |')
        else:
            md.append('（現在、未精査のキーワード候補はありません。）')

        (OUT / 'themes' / f'{key}.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # 7. themes/unclassified.md の出力
    md_unclass = [
        '# 未精査・未分類の本人発言',
        '',
        '文脈精査がまだ行われておらず、かつキーワード一致による仮テーマ候補も持たない本人発言の一覧です。',
        '（次回以降のバッチ処理で文脈を精査して分類します）',
        '',
        f'- **残件数**: {len(unclassified_unreviewed)}件（本人発言全{counts["user"]}件中）',
    ]
    if unclassified_unreviewed:
        md_unclass.append(f'- **対象発言ID範囲**: {unclassified_unreviewed[0]["id"]} 〜 {unclassified_unreviewed[-1]["id"]}')
        md_unclass.extend([
            '',
            '| 発言ID | 原文 | 本人発言の冒頭抜粋 |',
            '|---|---|---|',
        ])
        for r in unclassified_unreviewed:
            preview = escape_md_cell(r['preview'])
            line_link = f"[L{r['start_line']}–{r['end_line']}]({source_urls[r['source_id']]}#L{r['start_line']}-L{r['end_line']})"
            md_unclass.append(f'| {r["id"]} | {line_link} | {preview} |')
    else:
        md_unclass.extend(['', '全件の文脈精査が完了したため、未分類・未精査の発言はありません。'])

    (OUT / 'themes' / 'unclassified.md').write_text('\n'.join(md_unclass) + '\n', encoding='utf-8')

    # 8. INDEX.md の出力
    pct_reviewed = (len(reviewed_records) / counts['user'] * 100) if counts['user'] else 0
    summary = [
        '# テーマ別索引',
        '',
        '神宮氏とLLMの対話ログを、出典を区別してテーマ別に参照できるように整理した索引です。',
        '第2段階（文脈精査・セグメント設計）の確定レビュー結果および未精査のキーワード仮候補を反映しています。',
        '',
        '## 進捗サマリ',
        '',
        f'- **検出本人発言総数**: {counts["user"]:,}件',
        f'- **文脈確認済み（確定）**: {len(reviewed_records):,}件 ({pct_reviewed:.1f}%)',
        f'- **未確認発言（残り）**: {len(unreviewed_records):,}件 ({100 - pct_reviewed:.1f}%)',
        f'- **設計済みセグメント数**: {len(segments_list):,}セグメント',
        f'- **LLM発言総数**: {sum(v for k, v in counts.items() if k != "user"):,}件',
        '',
        '## テーマ別索引一覧',
        '',
        '| テーマ | 確定発言数 | 確定セグメント数 | 未確認候補数 | 索引ファイル |',
        '|---|---:|---:|---:|---|',
    ]

    for key, (label, _) in THEMES.items():
        conf_count = len(theme_confirmed[key])
        seg_count = len(theme_segments[key])
        cand_count = len(theme_candidates[key])
        summary.append(f'| [{label}](themes/{key}.md) | {conf_count:,} | {seg_count:,} | {cand_count:,} | [themes/{key}.md](themes/{key}.md) |')

    summary.extend([
        f'| [未分類・未精査](themes/unclassified.md) | - | - | {len(unclassified_unreviewed):,} | [themes/unclassified.md](themes/unclassified.md) |',
        '',
        '※1つの発言やセグメントに複数テーマが付与される場合があるため、各テーマの確定発言数の合計は確認済み発言数と一致しません。',
        '',
        '## 関連リソース',
        '',
        *[f"- 原本（{m['source_id']} / {m['assistant']}）: [{m['path']}]({m['source_url']})（固定コミットリンク）" for m in manifests],
        '- [進捗詳細 (PROGRESS.md)](PROGRESS.md)',
        *(['- [第三段階：判断・口調の分析](analysis/README.md)'] if (OUT / 'analysis' / 'README.md').exists() else []),
        '- [作業ガイドライン (GUIDELINES.md)](GUIDELINES.md)',
        '- [自動化エージェント指示文 (AUTOMATION_INSTRUCTIONS.md)](AUTOMATION_INSTRUCTIONS.md)',
        '- 発言インデックス: `data/utterances.jsonl`',
        '- 確定レビューデータ: `data/reviews.jsonl`',
        '- 確定セグメント一覧: `data/segments.jsonl`',
        '',
        '## 発信と判断の観察（読み直し）',
        '',
        'バッチサマリの観察文を、テーマごとに読める文章へまとめ直したものです。`observations/` は索引の再生成では上書きしません。',
        '',
    ])
    for key, (label, _) in THEMES.items():
        obs = OUT / 'observations' / f'{key}.md'
        if obs.exists():
            summary.append(f'- [{label}](observations/{key}.md)')
    summary.append('')

    (OUT / 'INDEX.md').write_text('\n'.join(summary) + '\n', encoding='utf-8')

    print(json.dumps({
        'user_count': counts['user'],
        'copilot_count': counts['copilot'],
        'reviewed': len(reviewed_records),
        'unreviewed': len(unreviewed_records),
        'unclassified_unreviewed': len(unclassified_unreviewed),
        'segments': len(segments_list),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
