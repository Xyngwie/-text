# テーマ別索引

神宮氏とCopilotの対話ログ（原本: `こぴちーお引越し.txt`）をテーマ別に参照できるように整理した索引です。
第2段階（文脈精査・セグメント設計）の確定レビュー結果および未精査のキーワード仮候補を反映しています。

## 進捗サマリ

- **検出本人発言総数**: 1,721件
- **文脈確認済み（確定）**: 1,590件 (92.4%)
- **未確認発言（残り）**: 131件 (7.6%)
- **設計済みセグメント数**: 522セグメント
- **Copilot発言総数**: 1,717件

## テーマ別索引一覧

| テーマ | 確定発言数 | 確定セグメント数 | 未確認候補数 | 索引ファイル |
|---|---:|---:|---:|---|
| [政治・行政・制度](themes/politics.md) | 0 | 0 | 0 | [themes/politics.md](themes/politics.md) |
| [国際情勢・外交・紛争](themes/world.md) | 5 | 3 | 0 | [themes/world.md](themes/world.md) |
| [経済・企業・労働](themes/economy.md) | 159 | 63 | 1 | [themes/economy.md](themes/economy.md) |
| [社会・事件・情報環境](themes/society.md) | 165 | 77 | 1 | [themes/society.md](themes/society.md) |
| [AI・対話・エージェント](themes/ai.md) | 167 | 56 | 4 | [themes/ai.md](themes/ai.md) |
| [開発・ソフトウェア・運用](themes/software.md) | 291 | 111 | 1 | [themes/software.md](themes/software.md) |
| [測量・土地・登記](themes/survey.md) | 276 | 133 | 1 | [themes/survey.md](themes/survey.md) |
| [ゲーム・設計・パズル](themes/games.md) | 267 | 93 | 0 | [themes/games.md](themes/games.md) |
| [ポーカー・確率・戦略](themes/poker.md) | 155 | 53 | 8 | [themes/poker.md](themes/poker.md) |
| [科学・工学・仕組み](themes/science.md) | 79 | 38 | 2 | [themes/science.md](themes/science.md) |
| [音楽・表現・文化](themes/culture.md) | 289 | 105 | 0 | [themes/culture.md](themes/culture.md) |
| [食・街歩き・旅行](themes/food.md) | 49 | 18 | 1 | [themes/food.md](themes/food.md) |
| [生活・身体・機器](themes/life.md) | 321 | 138 | 1 | [themes/life.md](themes/life.md) |
| [思考・価値観・自己理解](themes/thinking.md) | 550 | 274 | 4 | [themes/thinking.md](themes/thinking.md) |
| [未分類・未精査](themes/unclassified.md) | - | - | 111 | [themes/unclassified.md](themes/unclassified.md) |

※1つの発言やセグメントに複数テーマが付与される場合があるため、各テーマの確定発言数の合計は確認済み発言数と一致しません。

## 関連リソース

- 原本: [こぴちーお引越し.txt](https://github.com/Xyngwie/-text/blob/972b45c4b6eea00b13b8c54fcd9e0d3c185c1f74/%E3%81%93%E3%81%B4%E3%81%A1%E3%83%BC%E3%81%8A%E5%BC%95%E8%B6%8A%E3%81%97.txt)（固定コミットリンク）
- [進捗詳細 (PROGRESS.md)](PROGRESS.md)
- [作業ガイドライン (GUIDELINES.md)](GUIDELINES.md)
- [自動化エージェント指示文 (AUTOMATION_INSTRUCTIONS.md)](AUTOMATION_INSTRUCTIONS.md)
- 発言インデックス: `data/utterances.jsonl`
- 確定レビューデータ: `data/reviews.jsonl`
- 確定セグメント一覧: `data/segments.jsonl`
