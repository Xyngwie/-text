#!/usr/bin/env python3
"""Build traceable, provisional indexes; never edit the source archive."""
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'こぴちーお引越し.txt'
OUT = ROOT
MARKERS = {'あなたの発言': 'user', 'Copilot の発言': 'copilot'}
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

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

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

def main():
    raw = SOURCE.read_bytes()
    lines = raw.decode('utf-8').splitlines()
    blob = git('hash-object', str(SOURCE))
    # Use the last source-file commit so regeneration stays stable after index commits.
    source_commit = git('log', '-1', '--format=%H', '--', SOURCE.name)
    base = f'https://github.com/Xyngwie/-text/blob/{source_commit}/'
    from urllib.parse import quote
    url = base + quote(SOURCE.name)
    marks = [(i, MARKERS[line.strip()]) for i, line in enumerate(lines) if line.strip() in MARKERS]
    records = []
    for pos, (start, role) in enumerate(marks):
        stop = marks[pos + 1][0] if pos + 1 < len(marks) else len(lines)
        body = '\n'.join(lines[start + 1:stop]).strip()
        row = {
            'id': f'U{pos + 1:05d}', 'role': role,
            'start_line': start + 1, 'end_line': stop,
            'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
            'preview': ' '.join(body.split())[:160],
            'previous_id': f'U{pos:05d}' if pos else None,
            'next_id': f'U{pos + 2:05d}' if pos + 1 < len(marks) else None,
            'theme_candidates': hits(body) if role == 'user' else {},
            'review_status': 'unreviewed', 'date': None,
        }
        records.append(row)
    # Structural validation: no source span can disappear or overlap after the first marker.
    assert records and records[-1]['end_line'] == len(lines)
    assert all(a['end_line'] + 1 == b['start_line'] for a, b in zip(records, records[1:]))
    assert len({r['id'] for r in records}) == len(records)
    assert all(r['role'] == 'user' or not r['theme_candidates'] for r in records)
    (OUT / 'data').mkdir(exist_ok=True)
    (OUT / 'themes').mkdir(exist_ok=True)
    with (OUT / 'data' / 'utterances.jsonl').open('w', encoding='utf-8') as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
    dump(OUT / 'data' / 'taxonomy.json', {
        'status': 'provisional', 'method': 'literal_keyword_candidates_user_only',
        'themes': {k: {'label': label, 'keywords': words} for k, (label, words) in THEMES.items()},
    })
    counts = Counter(r['role'] for r in records)
    dump(OUT / 'data' / 'source_manifest.json', {
        'source_path': SOURCE.name, 'source_commit': source_commit, 'source_blob_sha': blob,
        'source_sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
        'line_count': len(lines), 'utterance_counts': dict(counts),
        'preamble_lines': [1, marks[0][0]] if marks[0][0] else None,
        'unclassified_user_utterances': sum(r['role'] == 'user' and not r['theme_candidates'] for r in records),
        'date_policy': 'Unknown: no year inferred from relative or incomplete dates.',
        'parser_caveat': 'Exact speaker labels inside pasted text may be mistaken for boundaries; manual review required.',
    })
    summary = ['# テーマ別索引（仮分類）', '', '本人発言のキーワード一致による候補。確定した話題数・人格分析ではありません。', '',
               '| テーマ | 候補発言数 |', '|---|---:|']
    for key, (label, _) in THEMES.items():
        selected = [r for r in records if key in r['theme_candidates']]
        summary.append(f'| [{label}](themes/{key}.md) | {len(selected)} |')
        md = [f'# {label}（仮候補）', '', '原文リンクには固定コミットと行範囲を使用。前後のCopilot回答も含めて文脈を確認してください。', '',
              '| 発言ID | 原文 | 一致語 | 本人発言の冒頭 |', '|---|---|---|---|']
        for r in selected:
            preview = r['preview'].replace('|', '\\|').replace('<', '&lt;').replace('>', '&gt;').replace('`', '\\`')
            md.append(f"| {r['id']} | [L{r['start_line']}–{r['end_line']}]({url}#L{r['start_line']}-L{r['end_line']}) | {', '.join(r['theme_candidates'][key])} | {preview} |")
        (OUT / 'themes' / f'{key}.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    unclassified = [r for r in records if r['role'] == 'user' and not r['theme_candidates']]
    md = ['# 未分類の本人発言', '', '短い相槌・指示語などは前後を読んで分類します。', '']
    for r in unclassified:
        md.append(f"- [{r['id']} / L{r['start_line']}]({url}#L{r['start_line']}-L{r['end_line']}): {r['preview']}")
    (OUT / 'themes' / 'unclassified.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    summary += ['', f'- 本人発言：{counts["user"]}件／Copilot発言：{counts["copilot"]}件。',
                f'- [未分類](themes/unclassified.md)：{len(unclassified)}件。',
                '- 同一発言に複数テーマを付けるため、候補数の合計は本人発言数と一致しません。',
                '- 話者ラベルは機械抽出。引用内ラベルの誤認・貼り付け資料・画面由来の文字は要確認。']
    (OUT / 'INDEX.md').write_text('\n'.join(summary) + '\n', encoding='utf-8')
    print(json.dumps({'counts': dict(counts), 'unclassified': len(unclassified), 'source_blob': blob}, ensure_ascii=False))

if __name__ == '__main__':
    main()
