# 第三段階：判断・価値観・口調の分析

現在の版は **v015（本人修整・実投稿フィードバック版）** です。第十四版の164場面・452本人発言、19仮説を保ったまま、AI初稿、本人修整、本人承諾、送信本文、実投稿表示を分離して保存・検証する仕組みを実装しました。本人が実際に直した差分を次回の校正へ戻し、AI自身の文を本人らしさとして自己増幅しない設計です。全567区間の第三段階はまだ完了していません。

今回の中心は [本人修整と実投稿を戻す校正ループ](v015/publication_feedback_loop.md) です。実際の登録方法はルートの `docs/PUBLICATION_FEEDBACK.md`、承諾条件は [本人承諾による公開フロー](v015/publication_workflow.md) を参照してください。

| 読みたいもの | 文書 |
|---|---|
| 初稿・本人修整・実投稿を次回へ戻す方法 | [実投稿の校正ループ](v015/publication_feedback_loop.md) |
| 強度2.25・承諾・自動投稿の権限規則 | [本人承諾による公開フロー](v015/publication_workflow.md) |
| 同じ主張の抑制・標準・強め比較 | [発信強度の校正](v015/intensity_calibration.md) |
| 同じ主張の通常・ギャル・お嬢様比較 | [口調モード校正](v015/mode_calibration.md) |
| 多用語、古風語、反復構文と使い方 | [語彙・構文の反復](v015/lexicon_and_constructions.md) |
| 通常・ギャル・お嬢様・武将調の切替規則 | [レジスターモード](v015/register_modes.md) |
| 場面別の口調生成条件と評価基準 | [口調の再現モデル](v015/voice_model.md) |
| 新しい題材へ適用した発信作例 | [発信モデルの校正例](v015/publication_calibration.md) |
| 結論を選び議論を生む編集規則 | [立場を選ぶ発信モデル](v015/publication_model.md) |
| 8つの価値観仮説の読み物 | [会話から見える価値観](v015/values.md) |
| 5つの大きなテーマによる人物像 | [会話から見える判断のしかた](v015/profile.md) |
| 自然な文章による口調の観察 | [会話の調子と言葉の使い方](v015/speech.md) |
| 判断仮説と価値観仮説の技術資料 | [構造化した判断仮説](v015/technical_profile.md) |
| 仮説ごとの独立案件数と再利用 | [根拠の依存性監査](v015/DEPENDENCY_AUDIT.md) |
| 第十四版からの変更 | [変更点](v015/CHANGES.md) |
| 原文リンク付きの164事例 | [根拠ページ](v015/cases.md) |
| 抽出・統合の方法と限界 | [分析方法](v015/METHOD.md) |
| 固定した入力と件数 | [manifest.json](v015/manifest.json) |
| 引き継いだ分析・保留の割り当て | [split.json](v015/split.json) |
| 構造化した事例 | [episodes.jsonl](v015/episodes.jsonl) |
| 根拠・対比・適用条件付きの仮説 | [findings.json](v015/findings.json) |

過去版は `v001` から `v014` まで保存し、後の分析で上書きしていません。別LLMの会話を追加する場合も、原本を別ソースとして登録し、既存版を変えずに次版で比較できます。

現在の参照検証は `python3 tools/validate_analysis.py --version v015` で実行できます。過去版も `--version` を切り替えて検証できます。
