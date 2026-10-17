# 第三段階：判断・価値観・口調の分析

現在の版は **v018（比喩・レジスター探索版）** です。第十七版の164場面・452本人発言、19仮説を保ったまま、未使用7場面から、比喩が構造の検査、立場の演出、現代的なオチへの着地にどう使われるかを整理しました。第三段階の分析と、第四段階のRSS実地校正を並行します。

今回の中心は [比喩とレジスターの役割](v018/metaphor_and_register.md) です。RSS実験の位置付けは [RSS価値観スライド実験](v018/rss_agent_spec.md)、適用する判断条件は [価値観が衝突した時の判断](v018/value_conflicts.md) を参照してください。

| 読みたいもの | 文書 |
|---|---|
| 構造を移す比喩と、立場を演じる口調の違い | [比喩とレジスターの役割](v018/metaphor_and_register.md) |
| 通常枠・政治実験枠・確定ログ化の境界 | [RSS価値観スライド実験](v018/rss_agent_spec.md) |
| 複数の価値が衝突した時の優先・反転条件 | [価値観が衝突した時の判断](v018/value_conflicts.md) |
| 生成時に使う構造化した条件モデル | [decision_policy.json](v018/decision_policy.json) |
| 初稿・本人修整・実投稿を次回へ戻す方法 | [実投稿の校正ループ](v018/publication_feedback_loop.md) |
| 強度2.25・承諾・自動投稿の権限規則 | [本人承諾による公開フロー](v018/publication_workflow.md) |
| 同じ主張の抑制・標準・強め比較 | [発信強度の校正](v018/intensity_calibration.md) |
| 同じ主張の通常・ギャル・お嬢様比較 | [口調モード校正](v018/mode_calibration.md) |
| 多用語、古風語、反復構文と使い方 | [語彙・構文の反復](v018/lexicon_and_constructions.md) |
| 通常・ギャル・お嬢様・武将調の切替規則 | [レジスターモード](v018/register_modes.md) |
| 場面別の口調生成条件と評価基準 | [口調の再現モデル](v018/voice_model.md) |
| 新しい題材へ適用した発信作例 | [発信モデルの校正例](v018/publication_calibration.md) |
| 結論を選び議論を生む編集規則 | [立場を選ぶ発信モデル](v018/publication_model.md) |
| 8つの価値観仮説の読み物 | [会話から見える価値観](v018/values.md) |
| 5つの大きなテーマによる人物像 | [会話から見える判断のしかた](v018/profile.md) |
| 自然な文章による口調の観察 | [会話の調子と言葉の使い方](v018/speech.md) |
| 判断仮説と価値観仮説の技術資料 | [構造化した判断仮説](v018/technical_profile.md) |
| 仮説ごとの独立案件数と再利用 | [根拠の依存性監査](v018/DEPENDENCY_AUDIT.md) |
| 第十六版からの変更 | [変更点](v018/CHANGES.md) |
| 原文リンク付きの164事例 | [根拠ページ](v018/cases.md) |
| 抽出・統合の方法と限界 | [分析方法](v018/METHOD.md) |
| 固定した入力と件数 | [manifest.json](v018/manifest.json) |
| 引き継いだ分析・保留の割り当て | [split.json](v018/split.json) |
| 構造化した事例 | [episodes.jsonl](v018/episodes.jsonl) |
| 根拠・対比・適用条件付きの仮説 | [findings.json](v018/findings.json) |

過去版は `v001` から `v017` まで保存し、後の分析で上書きしていません。別LLMの会話を追加する場合も、原本を別ソースとして登録し、既存版を変えずに次版で比較できます。

現在の参照検証は `python3 tools/validate_analysis.py --version v018` で実行できます。過去版も `--version` を切り替えて検証できます。
