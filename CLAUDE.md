# CLAUDE.md

このリポジトリで作業するClaude向けのメモ。

## リポジトリの入口

- 目的と全体像は [README.md](README.md)。
- 作業基準と分類のルールは [GUIDELINES.md](GUIDELINES.md)。作業前に読む。
- 原本（`sources/` 以下）は登録後に編集しない。分類や分析は別ファイルで管理する。

## Xの投稿を読むとき

- XのURL（`x.com` / `twitter.com`）を渡されたら、ブラウザを開かず、`api.fxtwitter.com` をcurlで叩いて読む。
- 手順は `.claude/skills/read-x-post/SKILL.md` にまとめてある。
- fxtwitterは非公式サービス。応答しないときは、取れなかったことを正直に伝え、内容を推測で埋めない。
