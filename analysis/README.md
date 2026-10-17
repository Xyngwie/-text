# 第三段階：判断・価値観・口調の分析

現在の版は **v019（作者性・愛着の校正版）** です。第十八版の164場面・452本人発言、19仮説を保ったまま、最初のRSS校正差分と未使用6場面から、道具の管理可能性と作品の固有性を分けました。第三段階の分析と、第四段階のRSS実地校正を並行します。

今回の中心は [選択可能性と、作品の抵抗](v019/attachment_and_authorship.md) です。前版の [比喩とレジスター](v019/metaphor_and_register.md) と合わせて、RSS初稿の判断と口調を校正します。

| 読みたいもの | 文書 |
|---|---|
| 選択肢、作者性、制約、使い続けて生まれる愛着 | [選択可能性と、作品の抵抗](v019/attachment_and_authorship.md) |
| 構造を移す比喩と、立場を演じる口調の違い | [比喩とレジスターの役割](v019/metaphor_and_register.md) |
| 通常枠・政治実験枠・確定ログ化の境界 | [RSS価値観スライド実験](v019/rss_agent_spec.md) |
| 複数の価値が衝突した時の優先・反転条件 | [価値観が衝突した時の判断](v019/value_conflicts.md) |
| 生成時に使う構造化した条件モデル | [decision_policy.json](v019/decision_policy.json) |
| 初稿・本人修整・実投稿を次回へ戻す方法 | [実投稿の校正ループ](v019/publication_feedback_loop.md) |
| 強度2.25・承諾・自動投稿の権限規則 | [本人承諾による公開フロー](v019/publication_workflow.md) |
| 同じ主張の抑制・標準・強め比較 | [発信強度の校正](v019/intensity_calibration.md) |
| 同じ主張の通常・ギャル・お嬢様比較 | [口調モード校正](v019/mode_calibration.md) |
| 多用語、古風語、反復構文と使い方 | [語彙・構文の反復](v019/lexicon_and_constructions.md) |
| 通常・ギャル・お嬢様・武将調の切替規則 | [レジスターモード](v019/register_modes.md) |
| 場面別の口調生成条件と評価基準 | [口調の再現モデル](v019/voice_model.md) |
| 新しい題材へ適用した発信作例 | [発信モデルの校正例](v019/publication_calibration.md) |
| 結論を選び議論を生む編集規則 | [立場を選ぶ発信モデル](v019/publication_model.md) |
| 8つの価値観仮説の読み物 | [会話から見える価値観](v019/values.md) |
| 5つの大きなテーマによる人物像 | [会話から見える判断のしかた](v019/profile.md) |
| 自然な文章による口調の観察 | [会話の調子と言葉の使い方](v019/speech.md) |
| 判断仮説と価値観仮説の技術資料 | [構造化した判断仮説](v019/technical_profile.md) |
| 仮説ごとの独立案件数と再利用 | [根拠の依存性監査](v019/DEPENDENCY_AUDIT.md) |
| 第十八版からの変更 | [変更点](v019/CHANGES.md) |
| 原文リンク付きの164事例 | [根拠ページ](v019/cases.md) |
| 抽出・統合の方法と限界 | [分析方法](v019/METHOD.md) |
| 固定した入力と件数 | [manifest.json](v019/manifest.json) |
| 引き継いだ分析・保留の割り当て | [split.json](v019/split.json) |
| 構造化した事例 | [episodes.jsonl](v019/episodes.jsonl) |
| 根拠・対比・適用条件付きの仮説 | [findings.json](v019/findings.json) |

過去版は `v001` から `v018` まで保存し、後の分析で上書きしていません。別LLMの会話を追加する場合も、原本を別ソースとして登録し、既存版を変えずに次版で比較できます。

現在の参照検証は `python3 tools/validate_analysis.py --version v019` で実行できます。過去版も `--version` を切り替えて検証できます。
