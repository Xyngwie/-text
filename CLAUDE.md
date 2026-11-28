# CLAUDE.md

プロジェクト全体の現行ルールは下記の運用方針を入口にする。投稿案を作る際は対象の生成指示と判断資料も読む。 [現行の運用方針](analysis/current_rules.md)。

このリポジトリで作業するAIエージェント向けの入口メモ。

## まず確認する正本（Single Source of Truth）

- 全体マップと構成：[README.md](README.md)
- 最新の進捗数値：[PROGRESS.md](PROGRESS.md)（機械用は `data/progress.json` / `data/x_manifest.json`）
- 第3段階の最新正式分析（現在 **v040**）：[analysis/README.md](analysis/README.md)（最新バージョンは `analysis/progress.json`）
- 会話分類の公式基準：[GUIDELINES.md](GUIDELINES.md)（新規原本の追加は [docs/ADDING_CONVERSATIONS.md](docs/ADDING_CONVERSATIONS.md)）
- ニュース短編の制作手順：[stories/README.md](stories/README.md)

## 不変ルール

- 原本（`sources/` 以下）および過去の分析版（`analysis/v001`〜`v039`）は編集・削除しない。
- 分類や分析、本人補足は別ファイル・追記型台帳で管理する。
- 自動ワークフロー（特に `x_classification.yml`）が `main` へ定期コミットするため、プッシュ前は必ず最新 `main` を確認・取り込む。

## Xの投稿を読むとき

- XのURL（`x.com` / `twitter.com`）を渡されたら、ブラウザを開かず、`api.fxtwitter.com` をcurlで叩いて読む。
- 手順は `.claude/skills/read-x-post/SKILL.md` にまとめてある。
- fxtwitterは非公式サービス。応答しないときは公開の埋め込みや出典も確認し、取得できた範囲を伝える。
