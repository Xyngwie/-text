# テーマ別索引

神宮氏とLLMの対話ログを、出典を区別してテーマ別に参照できるように整理した索引です。
第2段階（文脈精査・セグメント設計）の確定レビュー結果および未精査のキーワード仮候補を反映しています。

## 進捗サマリ

- **検出本人発言総数**: 1,930件
- **文脈確認済み（確定）**: 1,879件 (97.4%)
- **未確認発言（残り）**: 51件 (2.6%)
- **設計済みセグメント数**: 618セグメント
- **LLM発言総数**: 1,925件

## テーマ別索引一覧

| テーマ | 確定発言数 | 確定セグメント数 | 未確認候補数 | 索引ファイル |
|---|---:|---:|---:|---|
| [政治・行政・制度](themes/politics.md) | 5 | 4 | 1 | [themes/politics.md](themes/politics.md) |
| [国際情勢・外交・紛争](themes/world.md) | 19 | 8 | 1 | [themes/world.md](themes/world.md) |
| [経済・企業・労働](themes/economy.md) | 173 | 69 | 3 | [themes/economy.md](themes/economy.md) |
| [社会・事件・情報環境](themes/society.md) | 203 | 90 | 2 | [themes/society.md](themes/society.md) |
| [AI・対話・エージェント](themes/ai.md) | 229 | 87 | 5 | [themes/ai.md](themes/ai.md) |
| [開発・ソフトウェア・運用](themes/software.md) | 356 | 140 | 3 | [themes/software.md](themes/software.md) |
| [測量・土地・登記](themes/survey.md) | 301 | 144 | 7 | [themes/survey.md](themes/survey.md) |
| [ゲーム・設計・パズル](themes/games.md) | 321 | 114 | 2 | [themes/games.md](themes/games.md) |
| [ポーカー・確率・戦略](themes/poker.md) | 174 | 63 | 1 | [themes/poker.md](themes/poker.md) |
| [科学・工学・仕組み](themes/science.md) | 93 | 43 | 3 | [themes/science.md](themes/science.md) |
| [音楽・表現・文化](themes/culture.md) | 316 | 117 | 2 | [themes/culture.md](themes/culture.md) |
| [食・街歩き・旅行](themes/food.md) | 83 | 29 | 1 | [themes/food.md](themes/food.md) |
| [生活・身体・機器](themes/life.md) | 396 | 163 | 2 | [themes/life.md](themes/life.md) |
| [思考・価値観・自己理解](themes/thinking.md) | 691 | 333 | 5 | [themes/thinking.md](themes/thinking.md) |
| [未分類・未精査](themes/unclassified.md) | - | - | 38 | [themes/unclassified.md](themes/unclassified.md) |

※1つの発言やセグメントに複数テーマが付与される場合があるため、各テーマの確定発言数の合計は確認済み発言数と一致しません。

## 関連リソース

- 原本（copilot-001 / Copilot）: [sources/copilot-001/こぴちーお引越し.txt](https://github.com/Xyngwie/-text/blob/972b45c4b6eea00b13b8c54fcd9e0d3c185c1f74/%E3%81%93%E3%81%B4%E3%81%A1%E3%83%BC%E3%81%8A%E5%BC%95%E8%B6%8A%E3%81%97.txt)（固定コミットリンク）
- 原本（codex-dialogue-001 / Codex）: [sources/codex-dialogue-001/conversation.txt](https://github.com/Xyngwie/-text/blob/70a20f9741c8f3ea6102ca76cc8fe66d4d3e3d54/sources/codex-dialogue-001/conversation.txt)（固定コミットリンク）
- 原本（copilot-002 / Copilot）: [sources/copilot-002/10月6日以降のこぴちーとの会話.txt](https://github.com/Xyngwie/-text/blob/40e5dc4506d693a8cd7d65862265635773a44a84/sources/copilot-002/10%E6%9C%886%E6%97%A5%E4%BB%A5%E9%99%8D%E3%81%AE%E3%81%93%E3%81%B4%E3%81%A1%E3%83%BC%E3%81%A8%E3%81%AE%E4%BC%9A%E8%A9%B1.txt)（固定コミットリンク）
- [進捗詳細 (PROGRESS.md)](PROGRESS.md)
- [第三段階：判断・口調の分析](analysis/README.md)
- [作業ガイドライン (GUIDELINES.md)](GUIDELINES.md)
- [自動化エージェント指示文 (AUTOMATION_INSTRUCTIONS.md)](AUTOMATION_INSTRUCTIONS.md)
- 発言インデックス: `data/utterances.jsonl`
- 確定レビューデータ: `data/reviews.jsonl`
- 確定セグメント一覧: `data/segments.jsonl`

## 発信と判断の観察（読み直し）

バッチサマリの観察文を、テーマごとに読める文章へまとめ直したものです。`observations/` は索引の再生成では上書きしません。

- [政治・行政・制度](observations/politics.md)
- [国際情勢・外交・紛争](observations/world.md)
- [経済・企業・労働](observations/economy.md)
- [社会・事件・情報環境](observations/society.md)
- [AI・対話・エージェント](observations/ai.md)
- [開発・ソフトウェア・運用](observations/software.md)
- [測量・土地・登記](observations/survey.md)
- [ゲーム・設計・パズル](observations/games.md)
- [ポーカー・確率・戦略](observations/poker.md)
- [科学・工学・仕組み](observations/science.md)
- [音楽・表現・文化](observations/culture.md)
- [食・街歩き・旅行](observations/food.md)
- [生活・身体・機器](observations/life.md)
- [思考・価値観・自己理解](observations/thinking.md)

