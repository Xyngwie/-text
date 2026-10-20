# 第三段階：判断・価値観・口調の分析

現在の版は **v033（謎語と議論の段階の探索版）** です。164事例・452本人発言・19仮説を維持し、文の中の位置と、入口・検討中・本人側の着地という会話の段階を照合しました。

今回の中心は [謎語は、話の入口と本人側の着地に現れるか](v033/playful_sounds_and_discussion_phase.md) です。本人示唆と原本で確認できる位置を分け、意味の未確定な例も残します。

| 読みたいもの | 文書 |
|---|---|
| 謎語の位置、議論の段階、本人側の着地と合意の違い | [謎語と議論の段階](v033/playful_sounds_and_discussion_phase.md) |
| 着想の借用、もじり、オノマトペや反復の解釈 | [借りた着想と意味のある遊び](v033/borrowed_ideas_and_meaningful_play.md) |
| 誉れが介入を促す仕組み、自己点検と回顧的な肯定 | [神宮さんへの義理と介入](v033/honor_intervention_and_self_obligation.md) |
| Xでのカッコよさ、尊大さ、笑いの働き | [カッコよさと笑い](v033/grandeur_and_laughter.md) |
| 渡邉陽介と神宮がどちらも本人であること | [二つの名で一人である](v033/watanabe_and_jingu.md) |
| 恥、面子、矜持、未来の自分から見た誉れ | [恥・矜持・未来の自分](v033/shame_pride_and_future_self.md) |
| 意図、経緯、動機仮説、探索の停止条件 | [意図と経緯](v033/intention_and_history.md) |
| 自虐、笑い、しらんけど、自己評価の射程制限 | [自虐と留保](v033/self_deprecation_and_caveats.md) |
| 正解を決める側、ご褒美、古風な階層語、自己神話化 | [採点者の席に座る話し方](v033/evaluator_stance.md) |
| 共通の入口、開始位置、正解への報酬、技能差と購入差 | [公平と反撃可能性](v033/fairness_and_counterplay.md) |
| 目的を満たす線、追加利益、止め時、大胆さへの反転 | [十分の基準と、最大化しない判断](v033/enoughness.md) |
| 情報要求・仮説検査・自己点検・挑戦の疑問形 | [疑問形の四つの役割](v033/question_endings.md) |
| 選択肢、作者性、制約、使い続けて生まれる愛着 | [選択可能性と、作品の抵抗](v033/attachment_and_authorship.md) |
| 構造を移す比喩と、立場を演じる口調の違い | [比喩とレジスターの役割](v033/metaphor_and_register.md) |
| 通常枠・政治実験枠・確定ログ化の境界 | [RSS価値観スライド実験](v033/rss_agent_spec.md) |
| 複数の価値が衝突した時の優先・反転条件 | [価値観が衝突した時の判断](v033/value_conflicts.md) |
| 生成時に使う構造化した条件モデル | [decision_policy.json](v033/decision_policy.json) |
| 初稿・本人修整・実投稿を次回へ戻す方法 | [実投稿の校正ループ](v033/publication_feedback_loop.md) |
| 強度2.25・承諾・自動投稿の権限規則 | [本人承諾による公開フロー](v033/publication_workflow.md) |
| 同じ主張の抑制・標準・強め比較 | [発信強度の校正](v033/intensity_calibration.md) |
| 同じ主張の通常・ギャル・お嬢様比較 | [口調モード校正](v033/mode_calibration.md) |
| 多用語、古風語、反復構文と使い方 | [語彙・構文の反復](v033/lexicon_and_constructions.md) |
| 通常・ギャル・お嬢様・武将調の切替規則 | [レジスターモード](v033/register_modes.md) |
| 場面別の口調生成条件と評価基準 | [口調の再現モデル](v033/voice_model.md) |
| 新しい題材へ適用した発信作例 | [発信モデルの校正例](v033/publication_calibration.md) |
| 結論を選び議論を生む編集規則 | [立場を選ぶ発信モデル](v033/publication_model.md) |
| 8つの価値観仮説の読み物 | [会話から見える価値観](v033/values.md) |
| 5つの大きなテーマによる人物像 | [会話から見える判断のしかた](v033/profile.md) |
| 自然な文章による口調の観察 | [会話の調子と言葉の使い方](v033/speech.md) |
| 判断仮説と価値観仮説の技術資料 | [構造化した判断仮説](v033/technical_profile.md) |
| 仮説ごとの独立案件数と再利用 | [根拠の依存性監査](v033/DEPENDENCY_AUDIT.md) |
| 第三十二版からの変更 | [変更点](v033/CHANGES.md) |
| 原文リンク付きの164事例 | [根拠ページ](v033/cases.md) |
| 抽出・統合の方法と限界 | [分析方法](v033/METHOD.md) |
| 固定した入力と件数 | [manifest.json](v033/manifest.json) |
| 引き継いだ分析・保留の割り当て | [split.json](v033/split.json) |
| 構造化した事例 | [episodes.jsonl](v033/episodes.jsonl) |
| 根拠・対比・適用条件付きの仮説 | [findings.json](v033/findings.json) |

過去版は `v001` から `v032` まで保存し、後の分析で上書きしていません。別LLMの会話を追加する場合も、原本を別ソースとして登録し、既存版を変えずに次版で比較できます。

現在の参照検証は `python3 tools/validate_analysis.py --version v033` で実行できます。過去版も `--version` を切り替えて検証できます。
