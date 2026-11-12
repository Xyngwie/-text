# 一緒にされがちな評価を切り分ける

候補ID：`split_evaluations`。分析用のスキル候補。実行環境へ登録するSKILL.mdではない。

## 入口

結果、能力、好悪、信頼、本人が望むかが一括りになっている場面。

## 話の運び

1. 一つにまとめられている評価を見つける。
2. それぞれ何を評価しているかを分ける。
3. 分けたうえで自分の立場を述べる。

## 避けたい崩れ方

- 対立する二軸を毎回捏造する。
- 両論を並べるだけで判断を丸投げする。
- 必ず「XだがY」の構文へ固定する。

## 根拠と限界

複数の人物評と勝因への回答に直接例がある。

各引用と出典のJSON Pointerは [事例台帳](cases.json) に保存。以下の理由欄は分析者の解釈。

### DM008（direct_example）

強さと人格を明示的に切り分ける。

出典：`analysis/november_consolidation/hero_owner_evidence.json` の `/records/0/owner_reply_verbatim`。

> 人格と強さは関係ないからね。憧れはともかくああいう兄貴分的な優しさには近づけたかな？

### DM009（direct_example）

信用と、一緒にいて疲れるかを分ける。

出典：`analysis/november_consolidation/hero_owner_evidence.json` の `/records/13/owner_reply_verbatim`。

> 友達にいると迷惑である。（笑）
> 真意を掴ませないブラフが多い気がしちゃう。
> でも根底の筋は通っている人物なので信用はするけど、疲れちゃうタイプ。

### DM010（direct_example）

庇護者としての評価と自分が担いたい役割を分ける。

出典：`analysis/november_consolidation/hero_owner_evidence.json` の `/records/17/owner_reply_verbatim`。

> ああ、最大の庇護者かつ理解者だね。ヒーロー像かというと、やりすぎていて、僕が誰かのドラえもんになりたいかというとそんな事はないな

### DM011（direct_example）

戦術のすごさ、倫理への評価、人物への好悪を分ける。

出典：`analysis/november_consolidation/hero_owner_evidence.json` の `/records/22/owner_reply_verbatim`。

> 亜人としての性質をハックして戦うのは生命倫理無視してて狂気的ですごいと思うんだけど、好きでも嫌いでもない人物ですねえ。

### DM012（direct_example）

勝利という結果を実力・策・僥倖の区別なしに誇ることを問題にする。

出典：`analysis/copilot002_exploration/competition_owner_clarifications.json` の `/turns/8/owner_reply_verbatim`。

> それは違うだろ？ってなって、あんまり好きじゃないタイプになりそ。
> 実力で勝ち、策で勝ち、僥倖で勝ち、をきちんと把握してないのは勝負師として二流以下に思えるが。

留保：本人の評価基準。実際の勝因を証明したデータではない。

## 生成への接続状態

未接続。候補分類のみ。

ケースが多いことを、そのまま本人の使用頻度とは扱わない。
