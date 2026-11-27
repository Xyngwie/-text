# 第三段階：判断・価値観・口調の分析

## 現在の正本（最新正式版）

* **最新正式版**：**v040**（正本バージョンは [progress.json](progress.json) で管理）
* **固定している正式規模**：164事例・452本人発言・19仮説（`codex-dialogue-001` の質問40件・本人発言41件の一問一答を併せて整理）
* **RSS生成の参照先**：`v040/decision_policy.json` および `v040/publication_pairs.json`（校正済み6対・強度1.50〜2.50・1日最大6件）
* **整合性検証コマンド**：
  ```bash
  python3 tools/validate_analysis.py --version v040
  ```

> 過去版（`v001`〜`v039`）は履歴・ハッシュ連鎖検証のため上書きせずそのまま保全しています。普段の参照は下記の **v040** を正本として読んでください。

---

## 1. まず読む中心文書（v040）

| 読みたいもの | 文書 |
|---|---|
| 5つの大きなテーマによる人物像 | [会話から見える判断のしかた](v040/profile.md) |
| 8つの価値観仮説の読み物 | [会話から見える価値観](v040/values.md) |
| 自然な文章による口調の観察 | [会話の調子と言葉の使い方](v040/speech.md) |
| 依頼・同意・介入・検証・美意識・称賛の一問一答 | [今夜の会話まとめ](v040/qa_summary.md) |
| 一問一答における本人語彙と訂正・留保の使い方 | [一問一答の口調](v040/qa_voice_notes.md) |
| 判断仮説と価値観仮説の技術資料 | [構造化した判断仮説](v040/technical_profile.md) |
| v039 からの変更点 | [変更点](v040/CHANGES.md) |

---

## 2. テーマ別・判断軸の深掘り（v040）

| 読みたいもの | 文書 |
|---|---|
| 複数の価値が衝突した時の優先・反転条件 | [価値観が衝突した時の判断](v040/value_conflicts.md) |
| 渡邉陽介と神宮がどちらも本人であること | [二つの名で一人である](v040/watanabe_and_jingu.md) |
| 恥、面子、矜持、未来の自分から見た誉れ | [恥・矜持・未来の自分](v040/shame_pride_and_future_self.md) |
| 誉れが介入を促す仕組み、自己点検と回顧的な肯定 | [神宮さんへの義理と介入](v040/honor_intervention_and_self_obligation.md) |
| Xでのカッコよさ、尊大さ、笑いの働き | [カッコよさと笑い](v040/grandeur_and_laughter.md) |
| 目的を満たす線、追加利益、止め時、大胆さへの反転 | [十分の基準と、最大化しない判断](v040/enoughness.md) |
| 共通の入口、開始位置、正解への報酬、技能差と購入差 | [公平と反撃可能性](v040/fairness_and_counterplay.md) |
| 意図、経緯、動機仮説、探索の停止条件 | [意図と経緯](v040/intention_and_history.md) |
| 選択肢、作者性、制約、使い続けて生まれる愛着 | [選択可能性と、作品の抵抗](v040/attachment_and_authorship.md) |
| 相手の立場の検討、人物像の更新、自分に有利な説明への訂正 | [事情と評価の更新](v040/understanding_reassessment_and_disagreement.md) |
| 作り手の点検、読み込み、保証範囲、第三者の負担 | [手を貸すことと責任](v040/help_effort_and_responsibility.md) |
| 批判の先の対案、当座の救済、文脈ごとの評価 | [批判の先に何を置くか](v040/critique_relief_and_context.md) |
| 不確かな時の次の行動、待つ損失、保証範囲 | [動く時と確認を待つ時](v040/acting_and_waiting_under_uncertainty.md) |
| 着想後の成立条件、局所的な訂正、納得と実証の違い | [着想後の点検と修正](v040/ideas_checks_and_revision.md) |
| 着想の借用、もじり、オノマトペや反復の解釈 | [借りた着想と意味のある遊び](v040/borrowed_ideas_and_meaningful_play.md) |
| 謎語の位置、議論の段階、本人側の着地と合意の違い | [謎語と議論の段階](v040/playful_sounds_and_discussion_phase.md) |
| 自虐、笑い、しらんけど、自己評価の射程制限 | [自虐と留保](v040/self_deprecation_and_caveats.md) |
| 正解を決める側、ご褒美、古風な階層語、自己神話化 | [採点者の席に座る話し方](v040/evaluator_stance.md) |
| 情報要求・仮説検査・自己点検・挑戦の疑問形 | [疑問形の四つの役割](v040/question_endings.md) |
| 構造を移す比喩と、立場を演じる口調の違い | [比喩とレジスターの役割](v040/metaphor_and_register.md) |

---

## 3. 発信・口調・RSS校正モデル（v040）

| 読みたいもの | 文書 |
|---|---|
| 生成時に使う構造化した条件モデル | [decision_policy.json](v040/decision_policy.json) |
| 実投稿18件の対、生成参照6対、第四段階の限界 | [実投稿からの生成校正](v040/publication_trial_calibration.md) |
| 実投稿の語尾、励まし、否定の射程、本人の接点 | [採用した案を自分の発言にする](v040/adopting_a_draft_and_making_it_ones_own.md) |
| 通常枠・政治実験枠・確定ログ化の境界 | [RSS価値観スライド実験](v040/rss_agent_spec.md) |
| 結論を選び議論を生む編集規則 | [立場を選ぶ発信モデル](v040/publication_model.md) |
| 場面別の口調生成条件と評価基準 | [口調の再現モデル](v040/voice_model.md) |
| 通常・ギャル・お嬢様・武将調の切替規則 | [レジスターモード](v040/register_modes.md) |
| 多用語、古風語、反復構文と使い方 | [語彙・構文の反復](v040/lexicon_and_constructions.md) |
| 同じ主張の通常・ギャル・お嬢様比較 | [口調モード校正](v040/mode_calibration.md) |
| 同じ主張の抑制・標準・強め比較 | [発信強度の校正](v040/intensity_calibration.md) |
| 新しい題材へ適用した発信作例 | [発信モデルの校正例](v040/publication_calibration.md) |
| 初稿・本人修整・実投稿を次回へ戻す方法 | [実投稿の校正ループ](v040/publication_feedback_loop.md) |
| 強度・承諾・自動投稿の権限規則 | [本人承諾による公開フロー](v040/publication_workflow.md) |

---

## 4. 根拠データ・監査・メタデータ（v040）

| 読みたいもの | 文書 |
|---|---|
| 原文リンク付きの164事例 | [根拠ページ](v040/cases.md) |
| 抽出・統合の方法と限界 | [分析方法](v040/METHOD.md) |
| 仮説ごとの独立案件数と再利用 | [根拠の依存性監査](v040/DEPENDENCY_AUDIT.md) |
| 固定した入力と件数 | [manifest.json](v040/manifest.json) |
| 引き継いだ分析・保留の割り当て | [split.json](v040/split.json) |
| 構造化した事例 | [episodes.jsonl](v040/episodes.jsonl) |
| 根拠・対比・適用条件付きの仮説 | [findings.json](v040/findings.json) |

---

## 5. 本人補足・個別訂正メモ（v040 以降・横断補足）

正式版の前提に対する本人の明示的な訂正・運用指定・背景補足です。

* **運用・生成に関する本人指定**
  * [公開案の強度に関する本人の更新指定](random_intensity_clarification.md)：固定2.25から各案1.5〜2.5のランダム指定へ変更。
  * [題材を既知の興味に限定しない本人指示](rss_topic_scope_clarification.md)：知識不足・関心の薄さ・保留も有用な反応として読む。
  * [返信の学習と「違うか？」の実装確認](feedback_learning_implementation_check.md)：校正済み6対の接続と、生コメント無条件学習ではない境界の確認。
  * [第一号の実投稿と独立Issueの分類](first_publication_and_shared_dialogue.md)：採用投稿・投稿報告・発言者不明の対話要約の分離。
* **価値観・解釈に関する本人補足**
  * [努力と、その人自身の進歩への本人補足](effort_and_personal_progress_clarification.md)：同水準を求めることと、できないことへ取り組む価値の分離。
  * [建設的な議論について](constructive_discussion_clarification.md)：反論には完成した解決策ではなく「解決へ向かうきっかけ」を求める基準。
  * [依頼先に生じる貸し借り](indirect_obligations_clarification.md)：依頼先の次の行動に伴う関係への考慮と、常時実践の区別。
  * [砕けた言い方を含めた口調分析への本人補足](relaxed_voice_clarification.md)：精査済み原典の実例と今後の拾い方。
* **再構成資料（逐語原典・技術検証とは区別）**
  * [衛星フライホイール構想](satellite_flywheel_reconstruction.md)
  * [認知の受肉と人工神](cognition_and_artificial_god.md)

---

## 6. 進行中の探索・統合・壁打ち（正式版とは別管理）

以下の資料は正式な `v040` や仮説件数を自動変更せず、次版の正式統合候補として別管理しています。

### Issueでの第三段階壁打ち
* [Issueでの第三段階の壁打ち](dialogues/README.md)：本人返答を受けて対話資料を蓄積。

### 追加Copilot原典（`copilot-002`）の探索
* [01：砕けた言葉でも、話の中身は手放さない](copilot002_exploration/01_relaxed_but_precise.md)
* [02：対応関係を使った説明の事例](copilot002_exploration/02_analogy_examples.md) / [03：その後の話の展開](copilot002_exploration/03_analogy_development.md)
* [04：「違う」と言うとき、何を直しているか](copilot002_exploration/04_what_is_being_corrected.md)
* [06：勝敗より前に、選択の根拠を見る](copilot002_exploration/06_winning_and_judgment.md) / [07：探している間と、戦術が定まった後](copilot002_exploration/07_exploring_and_committing.md)
* [08：信条との戦いと、見る側の立場](copilot002_exploration/08_convictions_and_the_observer.md)
* [09：同じ言い方を通すことと、注意を使う場所](copilot002_exploration/09_fixed_wording_and_attention.md)
* [10：手間をかけて、日々の手間を減らす](copilot002_exploration/10_learning_to_spend_less_attention.md)
* [11：美しさと検証を、総合評価へ含める](copilot002_exploration/11_beauty_verification_and_ev.md)
* [12：選択を悔やむことと、判断を直すこと](copilot002_exploration/12_regret_and_revision.md)
* [13：役割を固定しないことと、火力役で狙うもの](copilot002_exploration/13_roles_and_reliable_elimination.md)

### 11月の統合精読・話の運び（`november_consolidation/`・`discourse_moves/`）
* [採用原稿を比べる](november_consolidation/adopted_manuscripts.md)
* [おちゃらけても、同じ働きとは限らない](november_consolidation/playful_utterances.md)
* [Issue原典の自動分析と精読の運用](november_consolidation/issue_analysis_operation.md)
* [言葉の荒さと、本気の怒り](november_consolidation/audience_and_anger.md)
* [既知の判定、議論の速さ、見返しての理解](november_consolidation/thinking_pace.md)
* [減らしたい手間と、残したい試行錯誤](november_consolidation/effort_and_play.md)
* [ヒーローの強さ、その人の幸福、共に暮らしたいか](november_consolidation/hero_values.md)
* [見栄で背伸びすることと、期限内にもう一度試すこと](november_consolidation/showing_off_and_retrying.md)
* [作品に触れたこと、人物を覚えていること、言葉だけ残ること](november_consolidation/hero_exposure_and_voice.md)
* [サブカルから離れた時期は見えるか](november_consolidation/exposure_session_20261111.md)
* [ポーカーの切り口を、原稿の一部で試す](november_consolidation/poker_angle_generation.md)
* [話の運び方の仮仕分け](discourse_moves/README.md)
* [11月18日の本人補足と話の運び](november_consolidation/discussion_20261118.md)
