# -text（会話ログ・Xアーカイブ・判断分析・創作基盤）

## 目的

長期のLLM壁打ちログ、Xの公式アーカイブ、GitHub Issue上の本人応答を**改変不能な原典**として構造化し、「神宮（@Xyngwie）がニュースや出来事のどこに注目し、どう判断し、どんな口調で感想を述べるか」を根拠付きで分析・検証するリポジトリです。

ログから得られる傾向は本人の完全な人格モデルではなく、特定の文脈内で観察された仮説として扱います。AIによる自動学習や本人名義での自動SNS投稿は行いません。

---

## 最初に読む入口（クイックマップ）

| 知りたいこと | 入口ファイル | 概要 |
|---|---|---|
| 現在の全体進捗 | [PROGRESS.md](PROGRESS.md) | 会話原本・Xアーカイブ・第3/4段階の最新件数 |
| テーマ別に会話を読む | [INDEX.md](INDEX.md) | 14テーマ別索引（1,930件・634セグメント） |
| 最新の分析結果（正本） | [analysis/README.md](analysis/README.md) | 第3段階の正式版（現在 **v040**）と補足・探索メモ |
| テーマごとの読み物観察 | [observations/README.md](observations/README.md) | バッチ観察を読みやすい文章に再整理したもの |
| 原本一覧と保管ルール | [sources/README.md](sources/README.md) | 会話原本3件・Xアーカイブ（22,462件）・Issue原典 |
| 分類ルール・作業基準書 | [GUIDELINES.md](GUIDELINES.md) | 倫理原則、著者性判定、バッチ分類・検証の公式手順 |
| ニュースから拾う短編 | [stories/README.md](stories/README.md) | 価値観スライドとは別系統の短編創作パイプライン |

---

## 4段階の作業構成と現在地

1. **第1段階：参照可能な索引（完了）**
   * 原本を `sources/<source_id>/` に固定し、全発言にID・話者・原文行番号・SHA-256ハッシュを付与。
   * 登録済み原本の本文は変更しない。追加原本は [原本の追加手順](docs/ADDING_CONVERSATIONS.md) に従って別ソースとして登録する。
2. **第2段階：文脈を読んだ意味分類（会話原本は完了 / X原本は自動進行中）**
   * 会話原本3件（`copilot-001`・`codex-dialogue-001`・`copilot-002`、計1,930件）は完了。
   * X公式アーカイブ（`x-archive-001`、22,462件）は別台帳で管理し、5分間隔の自動分類が進行中（[X原本の自動分類](docs/X_CLASSIFICATION_ACTION.md)）。
3. **第3段階：テーマ横断の判断・口調分析（進行中：現在 v040）**
   * 正式版は [analysis/README.md](analysis/README.md)（`v001`〜`v040` を上書きせず保全）。
   * チャットに加え、[Issueでの第三段階壁打ち](docs/STAGE3_DIALOGUE_ACTION.md) でも暫定分析と本人確認を並行運用（正式版やRSS生成へは自動反映しない）。
4. **第4段階：ニュース反応の試作・校正・検証（校正ループ稼働中）**
   * [RSSエージェント運用手順](docs/RSS_AGENT.md) により17分野から1日最大6件を Issue 化。
   * 本人の採用・修整・不採用（Close）・実投稿申告を追記型台帳（[実投稿の取込手順](docs/PUBLICATION_FEEDBACK.md)）へ記録。未見題材での前向き検証はこれから。

---

## 稼働中の自動ワークフロー（GitHub Actions）

| ワークフロー | 役割 | 詳細ドキュメント |
|---|---|---|
| `.github/workflows/x_classification.yml` | Xアーカイブの索引検証・AI第2段階分類（5分間隔・最大30件） | [docs/X_CLASSIFICATION_ACTION.md](docs/X_CLASSIFICATION_ACTION.md) |
| `.github/workflows/rss_ai_agent.yml` | 17分野のRSS収集・投稿案Issue生成（1日1回・最大6件） | [docs/RSS_AGENT.md](docs/RSS_AGENT.md) |
| `.github/workflows/import_rss_feedback.yml` | RSS Issueの本人コメント・Close採否・実投稿報告の取込 | [docs/RSS_AGENT.md](docs/RSS_AGENT.md) / [docs/PUBLICATION_FEEDBACK.md](docs/PUBLICATION_FEEDBACK.md) |
| `.github/workflows/stage3_dialogue.yml` | 第3段階の問い出し・本人コメントへの暫定分析（毎時） | [docs/STAGE3_DIALOGUE_ACTION.md](docs/STAGE3_DIALOGUE_ACTION.md) |
| `.github/workflows/archive_issue_comments.yml` | GitHub Issue上の本人コメント原典を文脈付きで保全 | [sources/github-issues-001/README.md](sources/github-issues-001/README.md) |
| `.github/workflows/issue_analysis.yml` | 保全済みIssueコメントの分類・分析案を蓄積（毎時） | [analysis/november_consolidation/issue_analysis_operation.md](analysis/november_consolidation/issue_analysis_operation.md) |

---

## 分類の原則

1. **複数テーマを許可する**：横断的な会話には該当するテーマをすべて付ける。
2. **前後の文脈から判定する**：短い相槌や指示語は前後の応答を含めて確認し、自動で前のテーマへ押し込まない。
3. **AIのお世辞・誘導を根拠にしない**：Copilot等の人物評や長文解説を本人の傾向の証拠にしない。
4. **著者性（`authorship`）を厳格に区別する**：貼り付け記事・下書き・AI生成文・メモリ一覧は `pasted` / `mixed` として本人意見（`own`）と分離する。
5. **発話の働き（`speech_act`）を分ける**：質問・仮説・冗談・感想・否定・同意を区別し、質問しただけで支持扱いしない。
6. **話題の性質（`news_relation`）を分ける**：`news` / `general` / `personal` / `unknown` をキーワード一致だけで決めない。
7. **不明を推測で埋めない**：日付不明・話者境界不明・意図不明はそのまま残す。

---

## 主なデータ・ツール一覧

### データ台帳（`data/`）
* `data/sources.json` / `data/source_manifest.json`：会話原本の登録簿・固定コミット・ハッシュ
* `data/utterances.jsonl` / `data/taxonomy.json`：発言索引と14テーマ定義
* `data/reviews.jsonl` / `data/segments.jsonl`：文脈確認済みレビューとトピック区間（自動生成で上書きしない）
* `data/publication_events.jsonl` / `data/rss_draft_dispositions.jsonl`：RSS初稿・修整・承諾・実投稿・採否の追記型履歴
* `data/x_manifest.json` / `data/x_reviews.jsonl` / `data/x_ai_reviews.jsonl`：Xアーカイブの進捗・精査記録・AI分類案

### 主なスクリプト（`tools/`）
* `tools/build_index.py`：レビュー・セグメントから `INDEX.md`・`themes/*.md`・`data/utterances.jsonl` を再生成
* `tools/validate.py`：会話分類・セグメント・ハッシュ・進捗の整合性検証
* `tools/validate_analysis.py`：第3段階分析（`analysis/vNNN`）の根拠・リンク・不変性検証
* `tools/rss_agent.py` / `tools/generate_rss_issues.py` / `tools/import_issue_feedback.py`：RSS収集・Issue生成・フィードバック取込
* `tools/publication_feedback.py`：実投稿フィードバックの登録・承諾照合
* その他、バッチ自動化用プロンプトは [AUTOMATION_INSTRUCTIONS.md](AUTOMATION_INSTRUCTIONS.md) を参照

---

## 再生成と検証コマンド

Python標準ライブラリとGitのみで動作します。原本と手動レビューは書き換えません。

```bash
python3 tools/build_index.py
python3 tools/validate.py
python3 tools/validate_analysis.py --version v040
python3 -m unittest discover -s tests -v
```
