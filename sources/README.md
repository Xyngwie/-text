# 原本の保管場所

原本ごとに `sources/<source_id>/` を作り、取得時の内容をそのまま保存します。

```text
sources/
  copilot-001/
    こぴちーお引越し.txt
  copilot-002/
    10月6日以降のこぴちーとの会話.txt
  x-archive-001/
    tweets.zip
  codex-dialogue-001/
    conversation.txt
  <新しい原本ID>/
    <原本ファイル>
```

会話の登録簿は [data/sources.json](../data/sources.json)、会話ログの登録手順は [原本の追加手順](../docs/ADDING_CONVERSATIONS.md) です。フォルダへ置くだけでは自動で登録・分類されません。追加原本は登録後に索引を再生成し、未精査から分類します。Xのtweets ZIPは別形式として専用の登録簿・パーサーで扱います。[X原本と第一段階の結果](x-archive-001/README.md)を参照してください。

登録済み原本の本文は編集しません。配置を移す場合は、登録簿の `path` のみ現在の保存先へ変更し、`source_commit_path` に固定コミット内の元のパスを保持します。`source_id`、発言IDの接頭辞、固定コミット、原本ハッシュ、話者ラベルは変えません。`source_commit_path` がない原本は `path` を固定コミット内でも使用します。

最初のCopilot原本はルートからこのフォルダへ移しましたが、証拠リンクは取得時の固定コミットの旧パスを引き続き参照します。過去の分析版は移動に合わせて書き換えません。
