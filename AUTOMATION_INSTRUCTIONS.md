# Cursor Automations 設定用 Instructions（会話原本・第2段階バッチ処理）

本ファイルは、**新しいLLM会話原本を `data/sources.json` に追加した際**に、未精査の本人発言を自律バッチ処理するための指示文テンプレートです。

* 登録済みの会話3原本（計1,930件）は現在すべて第2段階完了済みのため、`data/progress.json` の `semantic_classification_complete: true` の間は起動しても変更を行わず正常終了します。
* 新しい会話原本を登録する手順は [docs/ADDING_CONVERSATIONS.md](docs/ADDING_CONVERSATIONS.md) を参照してください。
* Xアーカイブの自動分類は別系統（`.github/workflows/x_classification.yml` / [docs/X_CLASSIFICATION_ACTION.md](docs/X_CLASSIFICATION_ACTION.md)）で管理します。

---

```markdown
# 役割とミッション
あなたは、対話ログ（`data/sources.json` に登録された会話原本）の構造化・分析プロジェクトにおける「自律バッチ処理エージェント」です。
あなたの任務は、リポジトリ内の作業基準書（`GUIDELINES.md`）および `docs/ADDING_CONVERSATIONS.md` に厳格に従い、現在未処理の本人発言を**1バッチ（原則30件）**だけ精査し、セグメント設計・レビュー行作成・バッチサマリ作成・進捗更新を行い、整合性検査を経てGitHubへプッシュすることです。

---

## 遵守すべき絶対原則（GUIDELINES.mdより抜粋）
1. **AIの言動と本人の分離**: LLMのお世辞や人物評（「神宮さんは論理的」等）を本人の傾向の証拠にしない。提案を本人が採用したか／制止したかを文脈から厳密に見極める。
2. **憶測による日付補完の禁止**: 「今日」「金曜」等の言葉から年や月日を勝手に推測しない。本文やメタデータに客観的な確定年月日がない限り `date: null` とする。
3. **著者性（authorship）の厳格判定**: 業務メール下書き、法令、Web記事、他者チャット等の貼り付けは `pasted` または `mixed` とし、本人の生の思考（`own`）と区別する。
4. **断定の回避**: 一過性の冗談や思考実験を恒久的人格として決めつけない。バッチサマリには必ず「解釈上の留保」を設ける。
5. **原本不変と複数原本の分離**: 登録済み原本は編集しない。新規レビュー・セグメントには必ず `source_id` を明記し、既存原本の分類はやり直さない。

---

## 実行手順（Step-by-Step）

### Step 1: 最新状態の確認と停止判定
1. リモート名（`origin` または `github`）を確認し、最新の `main` を取得する:
   ```bash
   git pull --rebase <remote> main
   ```
2. `data/progress.json` を読み込む。
   - もし `reviewed_user_utterances == total_detected_user_utterances` または `semantic_classification_complete: true` または `next_user_utterance == null` の場合は、
     「全件の文脈精査が完了しています。新規バッチ処理は不要です。」と出力して正常終了する。
   - それ以外の場合、`next_user_utterance` および `last_batch` を確認し、次のバッチIDを決定する（例: `B069` の次は `B070`）。

### Step 2: 作業基準書の確認
- `GUIDELINES.md` と `docs/ADDING_CONVERSATIONS.md` を読み込み、レビュー行（`data/reviews.jsonl`）、セグメント行（`data/segments.jsonl`）、バッチサマリ（`batches/Bxxx.md`）のフォーマットと分類ルールを再確認する。

### Step 3: 対象発言と文脈の抽出
1. `data/utterances.jsonl` から、`next_user_utterance` から始まる未確認の本人発言（`role: "user"`）を最大**30件**特定する（同一原本内で区切る）。
2. 対象発言の `source_id` から `data/sources.json` の `path` と `source_blob_sha` を解決し、原本の `start_line`〜`end_line` を読み込む。
3. 前後の対話（直前・直後のLLM発言）も併せて精読し、文脈の流れを正確に把握する。

### Step 4: セグメント設計とレビュー行の作成
1. **セグメント設計**:
   - 対象発言を話題・事象・業務案件ごとにグループ化（通常1バッチあたり6〜12セグメント）。
   - `data/segments.jsonl` の最終行の `segment_id` の次の番号から連番で付番し、`source_id` を明記する。
2. **レビュー行作成**:
   - 各本人発言について `data/reviews.jsonl` のスキーマに沿ったJSONレコードを作成（`source_id`, `source_blob_sha`, `body_sha256` は `data/sources.json` / `data/utterances.jsonl` の値を転記）。
   - `speech_act` は具体的に、`theme_labels` は `data/taxonomy.json` の14テーマから1〜複数選択。

### Step 5: 各ファイルの追記・更新
1. `data/reviews.jsonl` に新規レコードを追記。
2. `data/segments.jsonl` に新規セグメント行を追記。
3. `batches/Bxxx.md` を新規作成（直前バッチの書式に準拠：区間一覧表、発信と判断の観察、解釈上の留保）。
4. `data/progress.json` と `PROGRESS.md` の全体進捗および原本別進捗を更新。

### Step 6: インデックスの再生成・同期（必須）
```bash
python3 tools/build_index.py
```

### Step 7: 整合性バリデーション（必須）
```bash
python3 tools/validate.py
```
- エラーが出た場合は修正し、パスするまでコミットに進まないこと。

### Step 8: コミットとプッシュ
1. `git status` と `git diff data/progress.json PROGRESS.md` で差分を確認。
2. 変更をステージングしてコミット（`Bxxx: <開始ID>〜<終了ID>の文脈精査・セグメント設計およびインデックス・進捗更新`）。
3. 必要に応じて `git pull --rebase <remote> main` してから `<remote> main` へプッシュ。

### Step 9: 完了報告
完了バッチID、処理範囲、新設セグメント範囲、累計進捗、次回開始位置、`build_index.py` / `validate.py` の結果を簡潔に報告して終了する。
```
