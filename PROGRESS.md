# 分類の進捗

- 検出本人発言：1,930件。
- 文脈確認済み：1,930件。未確認：0件。
- 最新バッチ：B069。
- 次の開始位置：なし。
- 第3段階：分析継続中（v040）。[判断・口調の分析](analysis/README.md)。第4段階：本人申告の実投稿18件を校正し、生成時の参照例を追加。未見の題材での検証はこれから。

## 原本ごとの進捗

| 原本ID | LLM | 本人発言 | 確認済み | 未確認 | 第2段階 |
|---|---|---:|---:|---:|---|
| copilot-001 | Copilot | 1721 | 1721 | 0 | 完了 |
| codex-dialogue-001 | Codex | 41 | 41 | 0 | 完了 |
| copilot-002 | Copilot | 168 | 168 | 0 | 完了 |

未解決の参照：U00118・U00128・U00143・U00263・U00375・U00393・U00639・U00919・U00921

[原本の追加手順](docs/ADDING_CONVERSATIONS.md)。詳細は `data/progress.json`、`data/reviews.jsonl`、`data/segments.jsonl`。

## X原本（会話原本とは別集計）

- 索引：22,462件。精査記録：64件。AI分類案：1,170件。
- 次の投稿：x-archive-001:1024067619974828032。
- [X原本の観察](observations/x/activity_and_first_batch.md)。分類進捗は `data/x_manifest.json`。
