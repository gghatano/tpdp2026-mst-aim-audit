# MST / AIM の仕組み: select-measure-generate と PGM

> 技術解説ページ（モードA）。[REPORT.md](content/REPORT.md) §2.2・§2.6 から参照される補助資料。図ラベルは英語、本文は日本語。事実は出典タグ `[n]`（末尾の対応表）、筆者の補足は 🔎。

## 1. select-measure-generate パラダイム

MST [S5] と AIM [S6] は、いずれも **select-measure-generate**（選択・測定・生成）という共通レシピに従う DP 合成データ生成器である[S3][S5]:

1. **Select（選択）**: データの統計を要約する**低次の周辺分布（marginal）**を選ぶ。どの周辺が情報的かを **指数機構（Exponential mechanism）**[S_exp] で DP に選択する[1]。
2. **Measure（測定）**: 選んだ周辺のカウントを **ガウス機構（Gaussian mechanism）**[S_gauss] で測る（ノイズを加える）[1]。プライバシー予算の大半はここで消費される。
3. **Generate（生成）**: noisy な周辺に整合する合成データを、**グラフィカルモデル推論（PGM, Private-PGM）**[S_pgm] で生成する[1][S3]。

両者とも **one-way marginal（単変量周辺）から出発**する[1]。

> 🔎 **直感**: 「データ全体をそのまま守る」のでなく、「重要な低次統計だけを DP で測り、それを満たす人工データを作る」。低次に絞ることでノイズ予算を効率よく使え、強いプライバシー・有用性トレードオフを得る[1]。

## 2. ガウス機構と μ-GDP の接続

測定に**ガウス機構のみ**を使う構成では、消費するプライバシーが ρ-zCDP で tight に積算でき、ρ から `μ=√(2ρ)` で μ-GDP が直接定まる[1][S19]（→ [methods/gdp-and-tradeoff.md](methods/gdp-and-tradeoff.md)）。これが監査を μ-GDP 枠で解析可能にする鍵である。指数機構による選択ステップが入ると純ガウスでなくなるため、本監査では選択を固定して測定のみに予算を割り当てる構成を採る（§4）。

## 3. MST と AIM の違い

| | MST [S5] | AIM [S6] |
|---|---|---|
| 選択する周辺 | one-way から出発し、**ペア周辺で最大全域木（Maximum Spanning Tree）**を構成[1] | one-way から出発し、推定重要度に基づき**高次周辺を反復的に**選択[1] |
| 選択の戦略 | 一括（木構造を 1 回決める） | 適応的・反復的（adaptive & iterative）[S6] |
| 表現力 | ペアまでの依存を捉える | より高次の依存まで捉えうる |
| 共通点 | select-measure-generate・指数機構で選択・ガウス機構で測定・PGM で生成[1][S3] | 同左 |

要するに MST はペア周辺の木で依存構造を表し、AIM はより高次の周辺を貪欲・適応的に積み増す[1][S5][S6]。

## 4. なぜ one-way 制限で MST = AIM に帰着するか

本監査は MST/AIM を **one-way marginal のみを測定する制限構成**で扱う[1]。このとき:

- 依存グラフは**固定**され、高次（ペア・3-way 等）の周辺は**選択されない**[1]。
- よって MST の「木選択」も AIM の「適応的な高次選択」も**働かず**、両者は**同一の independent-marginal モデル**（各変数を独立に noisy one-way marginal で表すモデル）に帰着する[1]。
- 全予算が one-way 測定（ガウス機構）に割り当てられ、選択ステップの指数機構が消えるため、**ガウス機構のみ**となり μ-GDP 枠で解析できる[1]。
- さらにドメイン圧縮（domain compression）を無効化し、追加のバイアス源を避ける[1][S14]。

> 🔎 **含意（再現上）**: この帰着により、主実験では **MST のみを実装・監査すれば AIM もカバーされる**[1]。公開コードに `aim/` ディレクトリが無く `mst/` のみでも主構成として整合する理由がこれである[survey]。AIM 名義の独立再現が意味を持つのは、制限を緩めた高次 marginal 設定（原論文 付録 A）のみ[1]。

## 5. 高次 marginal への緩和（付録 A、本追試はスコープ外）

原論文 付録 A は制限を緩め、**2-way・3-way marginal**で学習した MST/AIM を監査する[1]。依存グラフは固定したまま予算をガウス測定に全振りするため、依然 μ-GDP 枠で解析できる[1]。結果として高次でも監査は弱まらず、むしろわずかに tight（3-way で μ_emp≈0.44、2-way ブラックボックスで ≈0.43、vs implied μ=0.45）[1]。本追試（スコープ A+B）では未実施である[計画]。

## 6. まとめ（このページの主張）

- MST/AIM は select-measure-generate に従い、指数機構で選択・ガウス機構で測定・PGM で生成する[1][S3][S5][S6]。
- 違いは選択する周辺の構造（MST=ペアの木 / AIM=適応的な高次）[1][S5][S6]。
- one-way 制限では選択が消え、両者が同一の independent-marginal モデルに帰着し、ガウス機構のみとなって μ-GDP 解析が可能になる[1]。
- ゆえに主構成では MST のみの監査で AIM もカバーされる[1]。

---

## 出典対応表（本ページ）

> 本ページの出典タグ（[S3] など）はこの表の各項目へリンクする。末尾の「REPORT の [Rn]」は本体レポートの References の対応番号。

- **[1]** Ganev, Annamalai, Kulynych. *Tight Auditing of Differential Privacy in MST and AIM*. TPDP 2026. arXiv:2604.18352.（本文全般。REPORT の [1]）
- **[S3]** McKenna, Liu. *A Simple Recipe for Private Synthetic Data Generation*. DifferentialPrivacy.org, 2022.（select-measure-generate。REPORT の [R3]）
- **[S5]** McKenna, Miklau, Sheldon. *Winning the NIST Contest* (MST). JPC, 2021.（REPORT の [R5]）
- **[S6]** McKenna, Mullins, Sheldon, Miklau. *AIM*. PVLDB, 2022.（REPORT の [R6]）
- **[S19]** Dong, Roth, Su. *Gaussian Differential Privacy*. JRSSB, 2022.（ρ→μ。REPORT の [R19]）
- **[S_exp]** McSherry, Talwar. *Mechanism Design via Differential Privacy* (指数機構). FOCS, 2007.（原論文 [30]）／ Dwork et al. *Our data, ourselves* も参照（原論文 [12]）
- **[S_gauss]** ガウス機構（原論文では McSherry & Talwar / Dwork & Roth の文脈で参照）
- **[S_pgm]** McKenna, Sheldon, Miklau. *Graphical-Model Based Estimation and Inference for DP* (Private-PGM). ICML, 2019.（原論文 [27]）
- **[S14]** Ganev, Oprisanu, De Cristofaro. *Robin Hood and Matthew Effects*. ICML, 2022.（ドメイン圧縮のバイアス。原論文 [14]）
