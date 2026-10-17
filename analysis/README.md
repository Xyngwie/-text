# 第三段階：判断・価値観・口調の分析

現在の版は **v017（RSS価値観スライド実験実装版）** です。第十六版の164場面・452本人発言、19仮説を保ったまま、通常領域と未実績の政治・社会領域を分けてRSS候補を収集し、条件付き価値観をゼロショット適用した初稿をGitHub Issueへ出すパイプラインを実装しました。本人の確定文だけを校正履歴へ戻します。第三段階は継続中で、第四段階は実装試験開始前です。

今回の中心は [RSS価値観スライド実験の位置付け](v017/rss_agent_spec.md) です。実装とスマホ操作はルートの `docs/RSS_AGENT.md`、適用する判断条件は [価値観が衝突した時の判断](v017/value_conflicts.md) を参照してください。

| 読みたいもの | 文書 |
|---|---|
| 通常枠・政治実験枠・確定ログ化の境界 | [RSS価値観スライド実験](v017/rss_agent_spec.md) |
| 複数の価値が衝突した時の優先・反転条件 | [価値観が衝突した時の判断](v017/value_conflicts.md) |
| 生成時に使う構造化した条件モデル | [decision_policy.json](v017/decision_policy.json) |
| 初稿・本人修整・実投稿を次回へ戻す方法 | [実投稿の校正ループ](v017/publication_feedback_loop.md) |
| 強度2.25・承諾・自動投稿の権限規則 | [本人承諾による公開フロー](v017/publication_workflow.md) |
| 同じ主張の抑制・標準・強め比較 | [発信強度の校正](v017/intensity_calibration.md) |
| 同じ主張の通常・ギャル・お嬢様比較 | [口調モード校正](v017/mode_calibration.md) |
| 多用語、古風語、反復構文と使い方 | [語彙・構文の反復](v017/lexicon_and_constructions.md) |
| 通常・ギャル・お嬢様・武将調の切替規則 | [レジスターモード](v017/register_modes.md) |
| 場面別の口調生成条件と評価基準 | [口調の再現モデル](v017/voice_model.md) |
| 新しい題材へ適用した発信作例 | [発信モデルの校正例](v017/publication_calibration.md) |
| 結論を選び議論を生む編集規則 | [立場を選ぶ発信モデル](v017/publication_model.md) |
| 8つの価値観仮説の読み物 | [会話から見える価値観](v017/values.md) |
| 5つの大きなテーマによる人物像 | [会話から見える判断のしかた](v017/profile.md) |
| 自然な文章による口調の観察 | [会話の調子と言葉の使い方](v017/speech.md) |
| 判断仮説と価値観仮説の技術資料 | [構造化した判断仮説](v017/technical_profile.md) |
| 仮説ごとの独立案件数と再利用 | [根拠の依存性監査](v017/DEPENDENCY_AUDIT.md) |
| 第十六版からの変更 | [変更点](v017/CHANGES.md) |
| 原文リンク付きの164事例 | [根拠ページ](v017/cases.md) |
| 抽出・統合の方法と限界 | [分析方法](v017/METHOD.md) |
| 固定した入力と件数 | [manifest.json](v017/manifest.json) |
| 引き継いだ分析・保留の割り当て | [split.json](v017/split.json) |
| 構造化した事例 | [episodes.jsonl](v017/episodes.jsonl) |
| 根拠・対比・適用条件付きの仮説 | [findings.json](v017/findings.json) |

過去版は `v001` から `v016` まで保存し、後の分析で上書きしていません。別LLMの会話を追加する場合も、原本を別ソースとして登録し、既存版を変えずに次版で比較できます。

現在の参照検証は `python3 tools/validate_analysis.py --version v017` で実行できます。過去版も `--version` を切り替えて検証できます。
