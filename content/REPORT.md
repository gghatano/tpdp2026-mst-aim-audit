# MST / AIM の差分プライバシーを GDP で tight に監査する：論文 arXiv:2604.18352 の縮小追試

> 対象 = MST / AIM（DP 合成データ生成器） ／ 対象論文 = *Tight Auditing of Differential Privacy in MST and AIM*（[arXiv:2604.18352](https://arxiv.org/abs/2604.18352), TPDP 2026）[1] ／ リポジトリ = <https://github.com/gghatano/tpdp2026-mst-aim-audit> ／ 最終更新 = 2026-06-19

> ⚠️ **ステータス注記**: 本レポートは**進行中の中間報告**である。実験スコープは A（dpmm 単体での MST/AIM 合成デモ）＋ B（監査の縮小再現）に限定し[計画]、数値完全一致でなく**傾向の再現**を目標とする。本文に記載する数値は**測定済みのもののみ**とし、未実施・未取得の箇所は「未測定」と明記、または TODO のプレースホルダとする。完全再現 C・AIM/高次 marginal（付録 A 相当）は当面スコープ外である[計画]。

---

## Abstract

差分プライバシー（DP）合成データ生成器のうち MST [R5] と AIM [R6] は、強いプライバシー・有用性トレードオフと NIST コンペ優勝・公的統計での採用実績から広く普及している[1]。一方で、その**プライバシー保証を tight に監査する**こと——すなわち実装が主張通りの保証を満たすかを経験的に検証すること——は依然として難しく、特に **強プライバシー領域（ε=1 など）では従来の監査が緩い／ゼロの下界しか与えられなかった**[1]。

本追試は、原論文の **Gaussian Differential Privacy（GDP）ベースの監査フレームワーク**を縮小規模で再現する。プライバシーを単一の (ε,δ) 値ではなく、強敵対者によるメンバーシップ推論攻撃（MIA）の **FPR–FNR トレードオフ全体**として測り、μ-GDP の単一パラメータ μ に要約する[1]。worst-case 隣接データセット（標的レコードを 1 件だけ加える構成）と hybrid black/white-box 脅威モデルのもとで、distinguishing game により経験的下界 μ_emp を推定する[1]。

主要結果（縮小再現）:

<!-- TODO: 実験後に埋める（E1 / B）— (ε,δ)=(1,10⁻²) における経験的 μ_emp と理論 μ=0.45 の比較値、および閾値選択基準を不安定なものに変えると μ_emp が 0 に潰れるかどうかの傾向。原論文は μ_emp≈0.43 vs μ=0.45 を報告 [1]。 -->

結論（暫定）:

<!-- TODO: 実験後に埋める — μ_emp が理論 μ の近傍に来たか（gap が小さいか）、および従来の μ_emp=0 の原因とされる不安定な閾値選択の現象が縮小規模でも観察されたかを、傾向として記述する。 -->

---

## 1. はじめに

### 1.1 背景

DP 合成データは、形式的保証のもとで機微なテーブルデータを共有する有望な手段であり、生成モデルを慎重に較正したノイズとともに学習し、その出力（モデルパラメータ・生成サンプル）を任意のレコードの有無に対して近似的に区別不能にする（典型的にはパラメータ (ε,δ) で形式化）[1]。中でも **MST** [R5] と **AIM** [R6] は select-measure-generate パラダイム（低次の周辺を選択し、ガウスノイズで測定し、それを保つよう合成する）[R3][R5] に従い、NIST コンペ優勝 [R8]、主要ライブラリへの統合 [R2][R10][R11]、英国センサスデータ公開での採用 [R9] など、実運用での採用が進んでいる[1]。

重要かつ広く使われるからこそ、その DP 保証を**経験的に検証**する必要がある。これが **DP 監査**[R12] を動機づける。DP 監査は、評価を DP 定義に整合する distinguishing game として枠付け、しばしばメンバーシップ推論攻撃（MIA）[R13][R14] により実現して、漏洩推定値を主張された DP パラメータと比較する[1]。

しかし MST に対する従来の監査 [R1][R2] には課題が残る[1]:
- 第一に、既存監査は **強プライバシー領域（例: ε=1）で限られた知見しか与えず**、ドメイン漏洩や浮動小数点脆弱性のような実装上の問題がない限り、**緩い／ゼロの結果**しか得られなかった[1]。
- 第二に、従来研究は **単一の (ε,δ) 設定**での結果を報告するにとどまり、プライバシーのトレードオフ全体を特徴づけられず、不完全あるいは誤解を招く結論につながりうる[1][R7]。

### 1.2 研究課題（RQ）

本追試が（縮小規模で）問うのは以下である:

1. **RQ1**: (ε,δ)=(1,10⁻²) の強プライバシー領域において、MST 実装の経験的下界 μ_emp は理論上界 μ（≈0.45）にどれだけ近いか（gap は小さいか）。
2. **RQ2**: トレードオフを単一の (ε,δ) でなく **FPR–FNR 曲線**として測ることで、複数の DP 概念（(ε,δ)-DP / ρ-zCDP / μ-GDP）を共通の曲線上で比較できるか。
3. **RQ3**: 閾値選択基準・信頼区間方式・脅威モデル等の**監査設定**を変えると経験的下界はどう変わるか。特に「不安定な閾値選択が μ_emp を 0 に潰す」という原論文の説明 [1] は縮小規模でも再現するか。

### 1.3 本追試の貢献

- **(C1)** 原論文の GDP 中心の監査手法（FPR–FNR トレードオフを μ-GDP に要約する枠組み）を、上流監査コード [R2] を移植・縮小して再現可能な形で実装し直す。
- **(C2)** (ε,δ)=(1,10⁻²) での経験的 μ_emp と理論 μ の比較を、縮小試行・固定シードのもとで提示する（傾向の再現）。
- **(C3)** 監査設定のアブレーション（閾値選択・信頼区間・脅威モデル等）を行い、結果が「設定」でなく「実装のプライバシー」を反映していることの確認を試みる。
- **(C4)** 縮小規模・単一実装・少数シードに由来する**限界を正直に明記**し、完全再現との差分を文書化する。

> 🔎 **考察（位置づけ）**: 本追試は原論文の主張を否定／肯定する確証実験ではなく、「公開コードと論文の細部差（分類器が GradientBoosting vs XGBoost、合成サイズ 25 vs 50 等[survey]）と縮小試行のもとで、主要な**傾向**——μ_emp が μ=0.45 近傍に来ること、および閾値基準を不安定にすると 0 に潰れること——が再現されるか」を確認する追試である[計画]。

---

## 2. 方法

> 本章では、原論文 [1] および上流コード [R2] から読み取れる**仕様・設計**を出典タグ [n] 付きで述べ、本追試固有の**設計判断**（縮小条件・実装差）は 🔎 ブロックで明示する。技術的な定義の詳細は付録 B のリンク先（methods/）に分離する。

### 2.1 監査フレームワーク（GDP・FPR–FNR トレードオフ）

本追試は、Annamalai ら [R1] の経験的 DP 監査フレームワークを採用する。これはプライバシー監査を MIA による仮説検定とみなすものである[1]。チャレンジャがランダム化機構を 2 つの隣接データセットで多数回独立に学習し、その出力を敵対者に与え、敵対者がどちらのデータセットが使われたかを区別しようとする[1]。結果の false-positive 率（FPR）と false-negative 率（FNR）が (ε,δ) トレードオフ曲線上の 1 点を定め、理論フロンティアと比較したうえで μ-GDP のもとでの経験的 μ に変換される[1]。

プライバシーを単一の (ε,δ) でなく **FPR–FNR トレードオフ全体**として測り、μ-GDP の単一パラメータ μ に要約することが本枠組みの中核である[1]。(ε,δ)-DP・ρ-zCDP・μ-GDP の相互関係と、なぜ単一値でなく曲線で見るのかは付録 B → [methods/gdp-and-tradeoff.md](gdp-and-tradeoff.html) で解説する。

### 2.2 worst-case 隣接データと標的レコード

worst-case 構成を用いる: Dout は同一レコード [0,0,0] を **10 件**含み、Din はそこに標的レコード [1,1,1] を **1 件**加える[1]。これは標的レコードの全周辺への影響を最大化し、厳しいプライバシーテストを与える。このような worst-case 設定は DP 定義と整合し、tight な監査を得るためにしばしば必要とされる[1][R15][R16]。

> 🔎 **考察（実装差）**: 上流公開コードの既定値（Dout サイズ・合成サイズ LEN_SYNTH=25・試行数 N_ALL）と本文記述（Dout=10 行・合成サイズ 50）には差がありうる[survey]。本追試は再現注意点として差分を記録し、傾向再現を目標とする。

### 2.3 脅威モデル（hybrid black/white-box）

hybrid black/white-box 敵対者を想定する[1]:
- **黒箱特徴**: 合成データ上で離散ドメインの**全クエリ**を評価して得る（Query-based MIA [R17] に従う）[1]。
- **白箱特徴**: モデル内部の **noisy one-way marginal counts**[1]。

両者を連結して攻撃分類器の入力とする。黒箱のみ／白箱のみとの比較はアブレーション（§3）で扱う。

### 2.4 distinguishing game と分割（train/valid/test）

(ε,δ)=(1,10⁻²) で **10,000 個の独立モデル**（Dout/Din 各 5,000）を学習し、各モデルがサイズ 50 の合成データセットと noisy marginals を出力する[1]。敵対者は釣り合いの取れたラベル付き出力を受け取り、それを **train 4,000 / validation 2,000 / test 4,000** に分割する[1]。

公平性・リーク防止の要として、**閾値（decision threshold）τ* は validation のみで選び**（advantage = TPR−FPR を最大化）、**test は最終評価に 1 回だけ用いる**[1]。

> 🔎 **設計判断（縮小条件）**: 本追試では試行数を縮小する（例: N_ALL を数百〜千程度）[計画]。分割比率・「閾値は valid のみ・test は 1 回」というリーク防止プロトコルは上流コードに内蔵されており、これを維持する[survey]。縮小に伴う統計的揺れは §5 で限界として論じる。

### 2.5 μ の統計推定（joint Bayesian）と (ε,δ)↔μ 変換

test 上の予測から TPR・FPR を計算し、Zanella-Béguelin ら [R18] に着想を得た **joint Bayesian アプローチ**で、対応する μ-GDP 領域が**事後質量 90%** を含むような下界 μ_emp を導出する[1]。これは**ベイズ下界**として解釈すべきものであり、Nasr ら [R16] が指摘するとおり、頻度論的被覆を必ずしも持たないが経験的にはより tight であることが多い[1]。

機構内部は入力 (ε,δ)-DP 予算を Canonne ら [R20] の変換で ρ-zCDP に変換し、ガウス機構のみを用いるため ρ が直接 μ-GDP に対応する（これを理論目標 implied μ とする）[1]。一方、(ε,δ) → μ の**直接変換**は、中間の zCDP ステップ（数値安定だが保守的[R20]）を経る accounting path より大きい μ（弱いプライバシー）を与える[1]。(ε,δ)↔μ 変換式の詳細は付録 B → [methods/gdp-and-tradeoff.md](gdp-and-tradeoff.html)。

### 2.6 本追試の実装と縮小条件

> 🔎 **設計判断**。以下は本追試固有の実装方針である[計画][survey]。

- **上流コード移植**: 監査ロジックは上流 sassoftware/dpmm の audit-dpmm ブランチ experimental/audit_dpmm/[R2] を移植する（MST ラッパ・(ε,δ)↔μ 変換・FPR/FNR から μ を推定する audit_utils 相当）。
- **N_ALL 縮小**: 完全版の 10,000 モデルを縮小（E0 スモークで所要時間を外挿して最終決定）[計画]。
- **分類器 = GradientBoosting**: 上流公開コードは GradientBoostingClassifier（および比較用 RandomForest）を用いる[survey]。本文は XGBoost [R4] と記すが、本追試は移植元コードに従い GradientBoosting を主とする（実装差として記録）。
- **シード固定**: random_state を固定し、3 本程度のシードで揺れを読む[計画]。
- **依存**: dpmm [R2]・riskcal（get_beta_from_gdp を joint_beta 下界に使用）を含む。uv で requirements.txt を起こしバージョンを固定する[計画]。
- **MST=AIM への帰着**: one-way marginal のみ測定する制限構成では MST と AIM が同一の independent-marginal モデルに帰着するため[1]、主構成では MST のみを扱えば AIM もカバーされる（→ [methods/mst-aim.md](mst-aim.html)）。

---

## 3. 結果

> ⚠️ 本章の数値・図表は**すべて未測定**であり、実験（E1 / スコープ B）の完了後に埋める。

### 3.1 FPR–FNR トレードオフ曲線（RQ2）

<!-- TODO: 実験後に埋める — figures/ に生成する FPR–FNR トレードオフ曲線図（図ラベルは英語）。経験的曲線（黒）と、ρ-zCDP 経由の implied μ（赤実線）・(ε,δ)→μ 直接変換（赤破線）・(ε,δ)-DP / ρ-zCDP の context 線・random guess を重ねる。原論文 Fig.1 に対応。 -->

図 1（予定）: MIA の経験的プライバシートレードオフと、複数の DP 概念のもとでの理論境界の比較（英語ラベル）。

<!-- TODO: 実験後に埋める — 所見 1〜2 行。経験的曲線が implied μ-GDP 境界をどの程度トラッキングするか。 -->

### 3.2 閾値選択曲線（RQ1）

<!-- TODO: 実験後に埋める — validation 上で FPR・FNR・empirical advantage を閾値の関数として描いた図（原論文 Fig.2 相当）。選択された閾値 τ* を明示。 -->

図 2（予定）: validation データ上の閾値選択（英語ラベル）。

### 3.3 μ_emp / μ_lower / AUC の表（RQ1）

<!-- TODO: 実験後に埋める — 下表を測定値で埋める。実行環境（OS / Python / dpmm・riskcal バージョン）・シード・N_ALL を脚注に明記。 -->

| 指標 | 値（縮小再現） | 原論文 [1] |
|---|---|---|
| 理論 μ（implied, via ρ-zCDP） | TODO | 0.45 |
| 理論 μ（(ε,δ)→μ 直接変換） | TODO | （Fig.1 破線、より大きい値） |
| 経験的 μ_emp（点推定 μ̂） | TODO | ≈0.43 |
| 経験的下界 μ_lower（joint_beta, 90%） | TODO | （Fig.3 Default） |
| 経験的下界 μ_lower（bonferroni_cp） | TODO | （Fig.3 比較バー） |
| 攻撃 AUC（診断用） | TODO | （非掲載） |

### 3.4 アブレーション（RQ3）

<!-- TODO: 実験後に埋める — 監査設定を 1 軸ずつ変えた μ_lower の表／図（原論文 Fig.3 相当）。軸: 閾値選択基準（max_advantage / max_mu_hat 等）・信頼区間（joint_beta / bonferroni_cp）・Dout サイズ・分類器（GradientBoosting / RandomForest）・脅威モデル（黒箱のみ / 黒箱+白箱）。特に「不安定な閾値選択で μ_emp が 0 に潰れる」現象の有無を所見として記す。 -->

図 3（予定）: 監査選択のアブレーションと経験的プライバシー μ_emp への影響（英語ラベル）。

---

## 4. 未実施の実験

本追試のスコープ外（**未測定**）である:

- **完全再現 C**: N_ALL を原論文どおり 10,000 モデルとし、上流の run_audit.ipynb のプロットを完全再現すること[計画]。計算コストが大きく、E0 スモークによる外挿後に別途判断する。
- **AIM / 高次 marginal（原論文 付録 A 相当）**: 2-way・3-way marginal で学習した MST/AIM の監査[1]。主構成では one-way 制限により MST=AIM に帰着するため未実施でも主結果はカバーされるが、付録 A の「高次でも監査は弱まらず μ_emp≈0.44（3-way）/0.43（2-way 黒箱）」[1] の再現は行わない[計画]。
- **複数 (ε,δ) でのトレードオフ全面掃引**: 本追試は (ε,δ)=(1,10⁻²) の単一設定に絞る。

---

## 5. 考察と限界

> 結果が出る前の暫定枠。**実験後に測定値を引いて各項を具体化**する。各限界は独立に列挙する。

### 5.1 強みと弱み（実装の妥当性 vs 監査の妥当性）

<!-- TODO: 実験後に埋める — μ_emp が implied μ に近ければ「実装が分析と整合（tight）」、大きく下回れば「縮小・実装差による緩さ」または「実装の問題」のいずれかを切り分けて論じる。 -->

### 5.2 外的妥当性（縮小規模・単一実装）

- 本追試は試行数を**縮小**しており、原論文の 10,000 モデルより統計的解像度が低い[計画]。μ_emp の絶対値は試行数に依存しうる。
- 対象は **dpmm の単一実装**であり[1][R2]、他ライブラリ（SmartNoise [R10] / Synthcity [R11] 等）の MST/AIM 実装には一般化しない。

### 5.3 統計的信頼性（少数シード・ベイズ下界の被覆）

- **少数シード**: 3 本程度のシードでは揺れの推定が粗い。単一シードの数値を断定的に扱わず、傾向として読む[規約]。
- **ベイズ下界の頻度論的被覆**: μ_lower は joint Bayesian（事後質量 90%）に基づくベイズ下界であり、頻度論的被覆を必ずしも持たない[1][R16]。下界を「保証された下界」と誤読しないよう注意する。

### 5.4 内的妥当性（valid/test 分離）

- 閾値選択を validation のみで行い test を 1 回だけ用いるプロトコル[1]を維持することで、閾値の test へのリークを防ぐ。これを崩すと μ_emp が楽観的に膨らむため、再現実装でも厳守する[survey]。

### 5.5 実装差に由来する限界

- 分類器（GradientBoosting vs 本文 XGBoost [R4]）・合成サイズ（25 vs 50）・Dout サイズ等の差[survey]。数値完全一致は狙わず、差分を本節および付録 A に記録する。

---

## 6. 結論と今後

<!-- TODO: 実験後に埋める（結論本体は最後に書く）— RQ1〜RQ3 への回答（μ_emp が μ=0.45 近傍に来たか／FPR–FNR 曲線で複数 DP 概念を比較できたか／不安定な閾値選択で 0 に潰れる現象を再現したか）を 3〜5 行でまとめる。 -->

今後の課題:
- E0 スモークに基づく N_ALL の最終決定と、可能なら完全再現 C への拡張。
- 付録 A 相当（2-way/3-way marginal、AIM 名義の独立再現）への拡張。
- dpmm/riskcal の固定バージョン確定（uv pip freeze）と、他ライブラリ実装への横展開。

---

## 付録 A 再現手順

> シードは実行時に固定する。下記は本リポジトリの README と整合する手順。詳細・落とし穴は付録 B のエンジニアリングノートに分離する。

```bash
# 0. クローン
git clone https://github.com/gghatano/tpdp2026-mst-aim-audit
cd tpdp2026-mst-aim-audit

# 1. 環境構築（uv, Python 3.11。dpmm は 3.10/3.11 のみ対応 [R2]）
bash scripts/setup_env.sh

# 2. 一括実行（E0 スモーク → 攻撃特徴生成 → 監査 → 図表）
bash scripts/run_all.sh

# 3. HTML ビルド（htmls/ に生成）
uv run python scripts/build_html.py
```

- **シード**: random_state を固定（3 本程度で揺れを確認）。実行環境（OS・Python・dpmm/riskcal バージョン・シード・N_ALL）は生成物（outputs/metrics.json 等）と一緒に保存する。
- **入力データ**: 不要。攻撃スクリプトが worst-case 隣接データ（全 0 行 vs 全 0+標的 1 行）を内部生成する[survey]。
- **再現の注意点**:
  - 上流環境定義は conda（environment.yml）であり uv 向けではないため、requirements.txt で dpmm・riskcal を固定する[survey]。
  - 攻撃スクリプトは multiprocessing を使い、Windows は spawn のため起動コストが高い。出力は UTF-8 を明示し、cp932 由来の文字化けを避ける[survey]。

<!-- TODO: 実験後に埋める — 実測の所要時間（E0 スモークの 1 試行 wall-clock と縮小版総時間）、確定した N_ALL、固定した dpmm/riskcal バージョンを追記。 -->

## 付録 B 補助資料（technical notes）

技術的な定義・背景は本体から分離し、methods/ に置く（図ラベルは英語、本文は日本語）:

- [methods/gdp-and-tradeoff.md](gdp-and-tradeoff.html) — (ε,δ)-DP → ρ-zCDP → μ-GDP の関係、トレードオフ関数 T、G_μ、Neyman-Pearson、なぜ単一 (ε,δ) でなく曲線で見るのか。
- [methods/mia-auditing.md](mia-auditing.html) — メンバーシップ推論による DP 監査、distinguishing game、強敵対者モデル、worst-case カナリア、なぜ tight が難しいか、従来研究が μ_emp=0 だった理由。
- [methods/mst-aim.md](mst-aim.html) — MST/AIM の select-measure-generate、指数機構・ガウス機構・PGM、MST と AIM の違い、one-way 制限で MST=AIM に帰着する理由。

上流監査コード: [sassoftware/dpmm (audit-dpmm ブランチ)](https://github.com/sassoftware/dpmm/tree/audit-dpmm) experimental/audit_dpmm/[R2]。

---

## References

> 本レポート独自の採番 [Rn]。原論文 [1] の引用番号（References [1]–[42]）とは独立である。原論文そのものは本文中 [1] で参照する。各 methods/ ページ末尾にもそのページで引く出典の対応表を置く。

- **[1]** Ganev, Annamalai, Kulynych. Tight Auditing of Differential Privacy in MST and AIM. TPDP 2026. arXiv:2604.18352. <https://arxiv.org/abs/2604.18352> （本追試の対象論文）
- **[R1]** Annamalai, Ganev, De Cristofaro. What do you want from theory alone? Experimenting with Tight Auditing of Differentially Private Synthetic Data Generation. USENIX Security, 2024.（原論文 [1][24] に対応する従来監査）
- **[R2]** Mahiou, Dizche, Nazari, Wu, Abbey, Silva, Ganev. dpmm: Differentially Private Marginal Models, a Library for Synthetic Tabular Data Generation. TPDP 2025. <https://github.com/sassoftware/dpmm> （原論文 [24]。上流ライブラリ・監査コード）
- **[R3]** McKenna, Liu. A Simple Recipe for Private Synthetic Data Generation. DifferentialPrivacy.org, 2022. <https://differentialprivacy.org/synth-data-1/> （原論文 [26]。select-measure-generate）
- **[R4]** Chen, Guestrin. XGBoost: A Scalable Tree Boosting System. ACM KDD, 2016.（原論文 [8]。本文の攻撃分類器）
- **[R5]** McKenna, Miklau, Sheldon. Winning the NIST Contest: A Scalable and General Approach to Differentially Private Synthetic Data. JPC, 2021.（原論文 [28]。MST）
- **[R6]** McKenna, Mullins, Sheldon, Miklau. AIM: An Adaptive and Iterative Mechanism for Differentially Private Synthetic Data. PVLDB, 2022.（原論文 [29]。AIM）
- **[R7]** Gomez, Kulynych, Kaissis, Calmon, Hayes, Balle, Honkela. Position: Gaussian DP for Reporting Differential Privacy Guarantees in Machine Learning. IEEE SaTML, 2026.（原論文 [18]。単一 (ε,δ) 報告の問題）
- **[R8]** NIST. 2018 Differential Privacy Synthetic Data Challenge. 2018. <https://www.nist.gov/ctl/pscr/open-innovation-prize-challenges/past-prize-challenges/2018-differential-privacy-synthetic> （原論文 [33]）
- **[R9]** ONS. Synthesising the Linked 2011 Census and Deaths Dataset while Preserving its Confidentiality. 2023. <https://datasciencecampus.ons.gov.uk/synthesising-the-linked-2011-census-and-deaths-dataset-while-preserving-its-confidentiality/> （原論文 [34]）
- **[R10]** OpenDP. SmartNoise SDK: Tools for Differential Privacy on Tabular Data. 2021. <https://github.com/opendp/smartnoise-sdk> （原論文 [35]）
- **[R11]** Qian, Davis, van der Schaar. Synthcity: A Benchmark Framework for Diverse Use Cases of Tabular Synthetic Data. NeurIPS D&B, 2023. <https://github.com/vanderschaarlab/synthcity> （原論文 [36]）
- **[R12]** Annamalai, Balle, Hayes, Kaissis, De Cristofaro. SoK: The Hitchhiker Guide to Efficient, End-to-End, and Tight DP Auditing. IEEE SaTML, 2026.（原論文 [2]。DP 監査総説）
- **[R13]** Hayes, Melis, Danezis, De Cristofaro. LOGAN: Membership Inference Attacks against Generative Models. PoPETs, 2019.（原論文 [20]）
- **[R14]** Shokri, Stronati, Song, Shmatikov. Membership Inference Attacks against Machine Learning Models. IEEE S&P, 2017.（原論文 [39]）
- **[R15]** Nasr, Song, Thakurta, Papernot, Carlini. Adversary Instantiation: Lower Bounds for Differentially Private Machine Learning. IEEE S&P, 2021.（原論文 [31]。worst-case 構成）
- **[R16]** Nasr, Hayes, Steinke, Balle, Tramer, Jagielski, Carlini, Terzis. Tight Auditing of Differentially Private Machine Learning. USENIX Security, 2023.（原論文 [32]。ベイズ下界の被覆に関する注意）
- **[R17]** Houssiau, Jordon, Cohen, Daniel, Elliott, Geddes, Mole, Rangel-Smith, Szpruch. TAPAS: A Toolbox for Adversarial Privacy Auditing of Synthetic Data. NeurIPS Workshop, 2022.（原論文 [21]。Query-based MIA）
- **[R18]** Zanella-Beguelin, Wutschitz, Tople, Salem, Ruhle, Paverd, Naseri, Kopf, Jones. Bayesian Estimation of Differential Privacy. ICML, 2023.（原論文 [42]。joint Bayesian μ 推定）
- **[R19]** Dong, Roth, Su. Gaussian Differential Privacy. JRSSB, 2022.（原論文 [10]。GDP の定義）
- **[R20]** Canonne, Kamath, Steinke. The Discrete Gaussian for Differential Privacy. NeurIPS, 2020.（原論文 [5]。(ε,δ)→ρ-zCDP の保守的変換）
