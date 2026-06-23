# メンバーシップ推論による DP 監査: distinguishing game と経験的下界

> 技術解説ページ（モードA）。[REPORT.md](content/REPORT.md) §2.1・§2.3・§2.4 から参照される補助資料。図ラベルは英語、本文は日本語。事実は出典タグ `[n]`（末尾の対応表）、筆者の補足は 🔎。

## 1. DP 監査とは何か

DP 監査は、機構が**主張通りのプライバシーを実際に満たすか**を経験的に検証する営みである[A12]。形式的な証明（理論上界）が正しくても、実装にバグ（ドメイン漏洩・浮動小数点脆弱性など）があれば実際の漏洩はそれより大きくなりうる。監査は理論を信じる代わりに「攻撃を実際に走らせて漏洩の**経験的下界**を測り、主張された DP パラメータと比較する」[A1][A12]。

- 理論上界（claimed）より経験的下界が**大きければ** → 主張違反の証拠[A1]。
- 経験的下界が理論上界に**ほぼ届けば** → 監査が tight（実装と解析が整合）[1]。
- 経験的下界が**ゼロに潰れる** → 監査が緩い／攻撃が弱い／設定が不適切（実装が安全とは言い切れない）[1]。

## 2. distinguishing game（区別ゲーム）

DP の定義そのものが区別ゲームである。監査はこれを次の手続きで具体化する[A1][1]:

1. **チャレンジャ**が 2 つの隣接データセット x（out）と x'（in。標的レコードを 1 件足したもの）を用意する。
2. ランダム化機構 M を、各データセットで**多数回 独立に学習**する（本手法では計 10,000 モデル＝各 5,000）[1]。
3. 各学習の出力（合成データ・noisy marginals）を**敵対者**に渡す。
4. 敵対者は各出力について「in か out か」を当てる。
5. 当たり外れから **FPR（out を in と誤判定）** と **FNR（in を out と見逃し）** を測り、トレードオフ曲線上の点を得る[1]。

この (FPR, FNR) を理論フロンティアと比較し、μ-GDP の経験的 μ に変換する[1]（→ [methods/gdp-and-tradeoff.md](methods/gdp-and-tradeoff.md)）。

## 3. 強敵対者モデル（strong adversary）

DP の保証は**強敵対者**（機構 M と 2 つの隣接データセット x, x' を知り、ただ「どちらが使われたか」だけを知らない敵）に対して成り立つことを要求する[A19]。監査もこの強敵対者を模す。本手法の敵対者は hybrid black/white-box である[1]:

- **黒箱特徴**: 合成データに対し離散ドメインの**全クエリ**を評価したカウント（Query-based MIA [A17] に従う）[1]。
- **白箱特徴**: モデル内部の **noisy one-way marginal counts**[1]。

両特徴を連結し、攻撃分類器（本手法では XGBoost[1]／移植コードでは GradientBoosting[survey]）に食わせて in/out を判別する。

> 🔎 **直感**: 強敵対者を仮定するほど経験的下界は上がり（tight に近づき）、現実的な弱い敵を仮定するほど下界は緩む。監査は「保証が壊れていないか」を厳しく問うため、あえて強敵対者を使う。

## 4. worst-case カナリア（標的レコード）

tight な監査には、標的レコードの影響を**最大化する worst-case 構成**がしばしば必要である[A1][A15][A16]。本手法では[1]:

- `Dout` = 同一レコード `[0,0,0]` を 10 件。
- `Din` = そこに標的（canary）`[1,1,1]` を 1 件追加。

この canary は全ての one-way marginal に最大の影響を与えるため、検出可能性（=漏洩）が最大化され、攻撃が理論境界に届きやすくなる[1]。

## 5. 攻撃 → FPR/FNR → 経験的下界

test 上の予測から TPR・FPR を計算し、**joint Bayesian アプローチ**（Zanella-Béguelin ら [A18] に着想）で、対応する μ-GDP 領域が**事後質量 90%** を含むような下界 μ_emp を導出する[1]。

重要な注意: これは**ベイズ下界**であり、Nasr ら [A16] が指摘するとおり**頻度論的被覆を必ずしも持たない**（経験的にはより tight なことが多い）[1]。「保証された下界」と混同してはならない。

公平性・リーク防止の要として、**閾値は validation のみで選び、test は 1 回だけ評価**する[1]。これを崩すと test 性能が楽観的に膨らみ、μ_emp が過大になる。

## 6. なぜ tight が難しいか／従来研究が μ_emp=0 だった理由

強プライバシー領域（ε=1 など）では信号（漏洩）が小さく、攻撃の (FPR,FNR) が理論境界に届きにくい。従来研究は MST に対し、同領域で**緩い、しばしばゼロの経験的推定**しか得られなかった[1][A1]。

本手法はその主因を**閾値選択の不安定さ**と特定する[1]: 推定 μ̂ を validation で最大化するような不安定な基準を使うと、**過度に小さい閾値**が選ばれて FPR が過大になり、経験的下界が**ゼロに潰れる**[1]。これが従来の μ_emp=0 の原因と説明される。これに対し、advantage（TPR−FPR）を最大化する基準は閾値に対して滑らかで安定に振る舞い、tight な下界を与える[1]。

> 🔎 **再現の焦点**: 本追試（縮小版）は、(1) μ_emp が implied μ=0.45 の近傍に来ること、(2) 閾値選択基準を不安定なものに変えると μ_emp が 0 に潰れること、という 2 つの**傾向**の再現を目標にする[計画]。数値完全一致は狙わない。

## 7. まとめ（このページの主張）

- DP 監査は理論を仮定せず、攻撃を走らせて**経験的下界**を測り主張と比較する[A1][A12]。
- 区別ゲーム＋強敵対者＋worst-case カナリアが tight な監査の三要素[1][A15][A16]。
- 経験的下界はベイズ下界であり頻度論的被覆を持つとは限らない[1][A16]。
- 従来の μ_emp=0 は**不安定な閾値選択**が主因であり、安定な advantage 基準で tight 化できる[1]。

---

## 出典対応表（本ページ）

> 採番は REPORT.md の References と共通。

- **[1]** = [本文全般]: Ganev, Annamalai, Kulynych. *Tight Auditing of Differential Privacy in MST and AIM*. TPDP 2026. arXiv:2604.18352.
- **[R1]** = [A1]: Annamalai, Ganev, De Cristofaro. *Experimenting with Tight Auditing of DP Synthetic Data Generation*. USENIX Security, 2024.（採用した監査枠組み・従来の μ_emp=0）
- **[R12]** = [A12]: Annamalai et al. *SoK: The Hitchhiker Guide to Efficient, End-to-End, and Tight DP Auditing*. IEEE SaTML, 2026.（DP 監査総説）
- **[R15]** = [A15]: Nasr et al. *Adversary Instantiation*. IEEE S&P, 2021.（worst-case 構成）
- **[R16]** = [A16]: Nasr et al. *Tight Auditing of DP Machine Learning*. USENIX Security, 2023.（ベイズ下界の被覆に関する注意）
- **[R17]** = [A17]: Houssiau et al. *TAPAS*. NeurIPS Workshop, 2022.（Query-based MIA）
- **[R18]** = [A18]: Zanella-Béguelin et al. *Bayesian Estimation of Differential Privacy*. ICML, 2023.（joint Bayesian 下界）
- **[R19]** = [A19]: Dong, Roth, Su. *Gaussian Differential Privacy*. JRSSB, 2022.（強敵対者・仮説検定の視点）
