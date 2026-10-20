# 実投稿を校正データとして取り込む

`tools/publication_feedback.py` は、AIの初稿、本人の修整、本人承諾、送信内容、プラットフォーム上の実表示を別々のイベントとして `data/publication_events.jsonl` へ追記します。

RSSのIssueでは、最終文をそのままコメントし、投稿後に別コメントで「投稿しました」と知らせるだけで取り込めます。タグやクローズは不要です。詳細は[RSSのスマホ操作](RSS_AGENT.md#スマホでの操作)を参照してください。Issue経由の `published` は `publication_evidence: owner_report` を付け、本人申告であることと外部表示を独立検証していないことを記録します。以下のコマンド操作による直接登録とは区別します。

## 基本手順

初稿を登録します。

```bash
python3 tools/publication_feedback.py create \
  --record-id P0001 \
  --text-file work/draft.txt \
  --mode normal \
  --intensity 2.25 \
  --generator codex
```

本人が直した文面を登録します。複数回修整した場合は、その都度 `revise` を実行します。

```bash
python3 tools/publication_feedback.py revise \
  --record-id P0001 \
  --text-file work/revised.txt \
  --note '結論と語尾を本人が修整'
```

本人が最終文面と公開条件を確認した後、承諾を記録します。

```bash
python3 tools/publication_feedback.py approve \
  --record-id P0001 \
  --text-file work/revised.txt \
  --destination example-social \
  --account-label main \
  --execution-time immediate \
  --approval-text 'この文面で投稿して'
```

実行後、承諾どおり送信した本文と、サービス上で実際に表示された本文を登録します。リンク短縮などがなければ `--posted-file` は省略できます。

```bash
python3 tools/publication_feedback.py post \
  --record-id P0001 \
  --submitted-file work/revised.txt \
  --posted-file work/posted.txt \
  --post-reference 'https://example.invalid/post/123'
```

履歴全体を検証します。

```bash
python3 tools/publication_feedback.py validate
```

## 記録上の区別

- `draft_created`：AIが生成した初稿。本人らしさの根拠にはしない。
- `user_revised`：本人が実際に直した文面。初稿との差分を高価値の校正材料にする。
- `user_approved`：その文面と公開条件への承諾。語彙傾向の根拠ではなく、実行権限の根拠にする。
- `published`：承諾版として送信した内容と実際の表示。リンク短縮などのサービス側変換を分離する。

承諾後の修整は承諾を無効にし、再承諾がない限り `post` は失敗します。承諾済み本文と異なるファイルも送信記録として受け付けません。

## 分析へ戻す時の原則

本人による修整差分は、次のように扱います。

- 誤字訂正や固有名詞修正は、口調学習へ使わない。
- 事実訂正は、判断モデルではなく事実確認工程の改善へ使う。
- 結論の強弱変更は、発信強度の校正へ使う。
- 語彙、語尾、構文、モードの変更は、口調モデルの候補にする。
- 段落の削除・追加は、情報量と論点選択の校正へ使う。
- サービス側の自動変換は、本人の修整として数えない。

一回の修整を恒久的な口癖へ昇格させません。同じ方向の修整が複数の独立した投稿で繰り返されるか、本人が明示的に一般規則として指定した場合に、次版のモデルへ反映します。

## 機密情報

APIキー、アクセストークン、Cookie、実アカウントの秘密情報は記録しません。`account_label` には分析用の呼称だけを入れます。非公開投稿や限定公開文をリポジトリへ保存する場合は、リポジトリ自体の公開範囲を先に確認してください。
