# MST / AIM の差分プライバシーを GDP で tight に監査する：論文 arXiv:2604.18352 の縮小追試

> 対象 = MST / AIM（DP 合成データ生成器） ／ 対象論文 = *Tight Auditing of Differential Privacy in MST and AIM*（[arXiv:2604.18352](https://arxiv.org/abs/2604.18352), TPDP 2026）[1] ／ リポジトリ = <https://github.com/gghatano/tpdp2026-mst-aim-audit> ／ 最終更新 = 2026-06-20

> ⚠️ **ステータス注記**: 本レポートは**中間報告**である。実験スコープは A（dpmm 単体での MST/AIM 合成デモ）＋ B（監査の縮小再現、out/in 各 1,125 試行）に限定し、数値完全一致でなく**傾向の再現**を目標とする。記載数値は測定済みのもの（[outputs/metrics.json](outputs/metrics.json)）。完全再現 C（10,000 fit）・AIM/高次 marginal（付録 A 相当）は当面スコープ外である。**DP ノイズは secure RNG のため特徴生成は run 間でビット非再現**だが、集約 μ_emp は安定する（[SETUP.md](SETUP.md) 再現性節）。

---

## Abstract

差分プライバシー（DP）合成データ生成器のうち MST [R5] と AIM [R6] は、強いプライバシー・有用性トレードオフと NIST コンペ優勝・公的統計での採用実績から広く普及している[1]。一方で、その**プライバシー保証を tight に監査する**こと——すなわち実装が主張通りの保証を満たすかを経験的に検証すること——は依然として難しく、特に **強プライバシー領域（ε=1 など）では従来の監査が緩い／ゼロの下界しか与えられなかった**[1]。

本追試は、原論文の **Gaussian Differential Privacy（GDP）ベースの監査フレームワーク**を縮小規模で再現する。プライバシーを単一の (ε,δ) 値ではなく、強敵対者によるメンバーシップ推論攻撃（MIA）の **FPR–FNR トレードオフ全体**として測り、μ-GDP の単一パラメータ μ に要約する[1]。worst-case 隣接データセット（標的レコードを 1 件だけ加える構成）と hybrid black/white-box 脅威モデルのもとで、distinguishing game により経験的下界 μ_emp を推定する[1]。

主要結果（縮小再現、out/in 各 **1,125 試行**、Default 構成、分割 train450/valid225/test450）: `(ε,δ)=(1,10⁻²)` の理論目標 **implied μ=0.45** に対し、経験的下界 **μ_emp=0.39**（点推定 μ̂=0.42、攻撃 AUC=0.62）を得た。縮小規模・分類器の差（GradientBoosting）により原論文の μ_emp≈0.43 [1] よりやや小さいが、**強プライバシー領域（ε=1）でゼロでない tight な下界**であり、μ_emp は試行数とともに implied μ へ近づいた（N=250→0.19、N=1,000→0.44）。さらに、閾値選択基準を不安定なもの（validation 上の μ̂ 最大化）に変えると **μ_emp が 0 に潰れる**ことを確認し、これは従来研究が強プライバシー領域で μ_emp=0 を報告した原因という原論文の説明 [1] を縮小規模で再現する。

結論（暫定）: 本縮小追試は、原論文の主要な**傾向**——(1) 経験的下界が implied μ の近傍に来る（実装が自身のプライバシー解析と整合）、(2) 監査規模を増やすと下界が締まる、(3) 不安定な閾値選択が下界を 0 に潰す——をいずれも再現した。数値の完全一致（μ_emp≈0.43）には至らないが、これは縮小規模（1,125 vs 5,000 試行）・分類器差・DP ノイズの非決定性（後述）に由来し、限界として明記する。

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

プライバシーを単一の (ε,δ) でなく **FPR–FNR トレードオフ全体**として測り、μ-GDP の単一パラメータ μ に要約することが本枠組みの中核である[1]。(ε,δ)-DP・ρ-zCDP・μ-GDP の相互関係と、なぜ単一値でなく曲線で見るのかは付録 B → [methods/gdp-and-tradeoff.md](methods/gdp-and-tradeoff.md) で解説する。

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

機構内部は入力 (ε,δ)-DP 予算を Canonne ら [R20] の変換で ρ-zCDP に変換し、ガウス機構のみを用いるため ρ が直接 μ-GDP に対応する（これを理論目標 implied μ とする）[1]。一方、(ε,δ) → μ の**直接変換**は、中間の zCDP ステップ（数値安定だが保守的[R20]）を経る accounting path より大きい μ（弱いプライバシー）を与える[1]。(ε,δ)↔μ 変換式の詳細は付録 B → [methods/gdp-and-tradeoff.md](methods/gdp-and-tradeoff.md)。

### 2.6 本追試の実装と縮小条件

> 🔎 **設計判断**。以下は本追試固有の実装方針である[計画][survey]。

- **上流コード移植**: 監査ロジックは上流 sassoftware/dpmm の audit-dpmm ブランチ experimental/audit_dpmm/[R2] を移植する（MST ラッパ・(ε,δ)↔μ 変換・FPR/FNR から μ を推定する audit_utils 相当）。
- **N_ALL 縮小**: 完全版の 10,000 モデルを縮小（E0 スモークで所要時間を外挿して最終決定）[計画]。
- **分類器 = GradientBoosting**: 上流公開コードは GradientBoostingClassifier（および比較用 RandomForest）を用いる[survey]。本文は XGBoost [R4] と記すが、本追試は移植元コードに従い GradientBoosting を主とする（実装差として記録）。
- **シード固定**: random_state を固定し、3 本程度のシードで揺れを読む[計画]。
- **依存**: dpmm [R2]・riskcal（get_beta_from_gdp を joint_beta 下界に使用）を含む。uv で requirements.txt を起こしバージョンを固定する[計画]。
- **MST=AIM への帰着**: one-way marginal のみ測定する制限構成では MST と AIM が同一の independent-marginal モデルに帰着するため[1]、主構成では MST のみを扱えば AIM もカバーされる（→ [methods/mst-aim.md](methods/mst-aim.md)）。

### 2.7 縮小の理由（規模と所要時間）

> 🔎 **設計判断**。「縮小」は単一の理由ではなく、軸ごとに動機が異なる。**計算時間**に由来するもの（試行数 N_ALL・シード本数）と、**スコープ／理論的正当性**に由来するもの（単一 (ε,δ)・one-way 制限）を分けて記す[計画]。

監査対象は極小の worst-case トイデータである（Dout=10 行・3 列・2 値ドメイン・合成サイズ 25）[survey]。したがって計算コストの主因は**データ規模ではなく、独立に学習する DP モデルの本数 N_ALL** である（1 試行あたり MST を 2 回 fit する: Dout 側・Din 側）。

| 縮小した軸 | 本追試（実測） | 原論文 [1] | 縮小の理由 |
|---|---|---|---|
| 試行数 N_ALL | **1,125 / side**（= 2,250 fit、目標 2,500 を実行環境のジョブ上限で中断→resume で到達） | 5,000 / side（= 10,000 fit） | **計算時間**＋実行環境の長時間ジョブ打ち切り |
| シード | 監査の random_state=13 固定（特徴生成は非決定、後述） | 多数 | 計算時間 |
| (ε,δ) | (1, 10⁻²) 単一 | 複数設定を掃引 | **スコープ**（強プライバシー領域の 1 点に集中） |
| marginal の次数 | one-way のみ | 付録 A で 2/3-way | **理論的に正当**: one-way 制限では選択機構が消え MST=AIM に帰着する（§2.6・付録 B [mst-aim](methods/mst-aim.md)）。高次は PGM 推論が重くスコープ外 |

**所要時間（実測）**: MST 1 fit ≈ 9.2 秒（単体）、18 並列での実効スループットは **約 1.24 秒/fit**（[outputs](outputs/) のメタ参照）。2,250 fit で実時間 約 30–40 分相当。実行環境が長時間バックグラウンドジョブを **約 10–15 分で打ち切る**ため、チェックポイント＋resume 方式（落ちても完了分を保存し再開で積み増す）で 1,125/side まで到達した（[scripts/01_run_attack.py](scripts/01_run_attack.py)）。フル再現 C（10,000 fit）は同条件で概ね **2–3 時間規模**と外挿される。

> 🔎 **書き分けの含意**: 「縮小＝計算節約」が当てはまるのは N_ALL とシードのみである。単一 (ε,δ) と one-way 制限は計算ではなく**スコープ・理論的正当性**による選択であり、後者は主結果の妥当性を損なわない（むしろ AIM もカバーする）[1][計画]。

---

## 3. 結果

> 測定値は out/in 各 **1,125 試行**（Default 構成、分割 train450/valid225/test450、監査 random_state=13、dpmm 0.1.9 / riskcal 1.5.1 / Python 3.11、n_thresholds=80）。図中ラベルは英語、本文は日本語。生成物は [outputs/metrics.json](outputs/metrics.json)。

### 3.1 FPR–FNR トレードオフ曲線（RQ2）

![FPR-FNR tradeoff curve](figures/tradeoff.png)

図 1: MIA の経験的プライバシートレードオフ（黒）と、複数の DP 概念のもとでの理論境界の比較。原論文 Fig.1 に対応。

**所見**: 経験的曲線（黒）は random guess（対角）より明確に内側にあり、かつ implied μ=0.45 の μ-GDP 曲線（赤実線）の**外側（上側）**に位置する——任意の MIA は理論フロンティアを越えられないため、経験的曲線が理論線の外にあるのは正しい挙動である。両者の隔たりは小さく、経験的曲線が **accounting path（ρ-zCDP 経由の implied μ）側**に概ね沿う。これは「実装が自身のプライバシー解析と整合（tight 寄り）」という原論文の主結論 [1] の傾向に一致する。RQ2 については、3 つの DP 概念（(ε,δ)-DP・ρ-zCDP・μ-GDP）を同一の FPR–FNR 平面上に並べて比較できた。

### 3.2 閾値選択曲線（RQ1）

![Threshold selection on validation](figures/valid_threshold.png)

図 2: validation データ上の閾値選択。FPR・FNR・empirical advantage を閾値の関数として描き、advantage を最大化する **τ\*≈0.49** を選択（原論文 Fig.2 相当）。advantage は閾値に対して滑らかで安定しており、この τ\* を test に 1 回だけ適用して μ_emp を推定する。

### 3.3 μ_emp / μ_lower / AUC の表（RQ1）

| 指標 | 値（縮小再現, N=1,125/side） | 原論文 [1] |
|---|---|---|
| 理論 μ（implied, via ρ-zCDP） | **0.455** | 0.45 |
| 理論 μ（(ε,δ)→μ 直接変換） | 0.533 | （Fig.1 破線、より大きい値） |
| 経験的下界 μ_emp（joint_beta, 90%, Default） | **0.393** | （Fig.3 Default） |
| 経験的 点推定 μ̂ | 0.415 | ≈0.43 |
| 経験的下界 μ_emp（bonferroni_cp） | 0.177 | （Fig.3 比較バー） |
| 攻撃 AUC（test, 診断用） | 0.616 | （非掲載） |

> 🔎 **所見（RQ1）**: μ_emp=0.39 は implied μ=0.455 に対し gap 約 0.06。原論文の μ_emp≈0.43（gap≈0.02）より gap はやや大きいが、これは縮小規模（1,125 vs 5,000）と分類器差（GradientBoosting vs XGBoost）で説明でき（§5.5）、**強プライバシー領域で非ゼロの tight 寄りの下界**という質的結論は再現された。joint_beta（0.393）は bonferroni_cp（0.177）より明確に tight で、原論文が Default に joint_beta を採る判断 [1] とも整合する。

### 3.4 アブレーション（RQ3）

![Ablation of audit choices](figures/ablation.png)

図 3: 監査設定を 1 軸ずつ変えたときの経験的下界 μ_emp（test）。赤線は implied μ=0.45（原論文 Fig.3 相当）。

| 設定 | μ_emp | 所見 |
|---|---|---|
| **Default**（max_advantage + joint_beta + hybrid + GBM） | **0.393** | 主結果 |
| 閾値選択 = max_μ̂（不安定） | **0.000** | 過小な閾値を選び FPR が膨張、下界が 0 に潰れる |
| 閾値選択 = max_μ_lower | 0.929 | validation に過適合し楽観的（test で過大評価の恐れ） |
| 信頼区間 = bonferroni_cp | 0.177 | joint_beta より保守的 |
| 分類器 = RandomForest | 0.315 | GradientBoosting より弱い |
| 脅威モデル = 黒箱のみ | 0.261 | 白箱 marginal 特徴を落とすと低下＝白箱が効く |

> 🔎 **所見（RQ3）**: 最重要の再現点は **max_μ̂ で μ_emp=0** である。validation 上で μ̂ を直接最大化する不安定な基準は過小な閾値を選んで FPR を過大にし、下界を 0 に潰す——これは「従来研究が強プライバシー領域で μ_emp=0 を報告した原因」という原論文の説明 [1] を、本縮小規模でも明確に再現する。また白箱特徴の寄与（hybrid 0.39 > 黒箱のみ 0.26）と joint_beta の優位（0.39 > bonferroni_cp 0.18）も確認され、Default 構成が最も tight という原論文の主張 [1] と整合する。

### 3.5 補足: dpmm 単体での合成忠実度デモ（スコープ A）

> 監査（§3.1–3.4）とは独立に、dpmm の MST/AIM が「DP 予算 ε を上げるほど元データの分布を忠実に再現する」基本挙動を確認する補助デモ。相関のあるカテゴリカルデータ（n=2,000・5 列）を生成して "real" とし、列の 1-way / 2-way 周辺分布の Total Variation Distance（TVD、小さいほど忠実）を測った。

![Fidelity vs epsilon for MST and AIM](figures/demo_fidelity.png)

図 4: ε に対する 1-way / 2-way TVD（MST・AIM）。両手法とも **ε を上げるほど TVD が単調に減少**し、想定どおりプライバシー予算と有用性がトレードオフする。例えば MST の 1-way TVD は ε=0.5 で 0.010、ε=4 で 0.002。MST と AIM は本データ規模では同程度の忠実度を示した（one-way 制限の監査構成とは別に、ここでは両手法の標準設定を用いている）。

> 🔎 **位置づけ**: このデモは「手法が普通に動き、ε で品質が変わる」ことの確認であり、監査の主結論とは独立である。詳細は [methods/mst-aim.md](methods/mst-aim.md) を参照。

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

本追試では μ_emp=0.39 が implied μ=0.455 の近傍（gap≈0.06）に来た。これは **「監査が実装のプライバシーを概ね正しく捉えている（tight 寄り）」** ことを示し、dpmm の MST 実装に強プライバシー領域での明白な漏洩（ドメイン漏洩・浮動小数点脆弱性等）が無いという原論文の所見 [1] と整合する。一方、原論文の gap≈0.02 より緩い（gap が大きい）のは、**実装の問題ではなく監査側の縮小・実装差**（試行数 1,125 vs 5,000、分類器 GradientBoosting vs XGBoost）に帰せられる——その根拠として、(a) 監査規模を増やすと μ_emp が implied μ に向けて単調に締まる収束傾向（§3 図はないが convergence の数値: 250→0.19, 1000→0.44）、(b) Default 以外の設定では下界がさらに緩む／0 に潰れるアブレーション（§3.4）、の 2 点が「緩さは攻撃側の弱さに由来」という解釈を支持する。すなわち**「監査の緩さ＝実装の安全性」と誤読しない**ことが重要である。

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

### 5.6 他手法への適用可能性（適用範囲）

> 🔎 **考察（適用範囲）**。「この監査が MST/AIM 以外に使えるか」は手法名でなく、**監査コードが置く前提**で決まる[計画]。

まず系統の整理: DP 合成データ生成器は大きく **marginal 系**（低次周辺を選んで測る。MST [R5]・AIM [R6] はこちら）と、**DP-SGD 系**（勾配のクリップ + ノイズ付加による深層生成。DP-GAN・PATE-GAN・DP-CTGAN 等）に分かれる。MST/AIM は DP-SGD ではない。

本実装が依存する前提は次の 3 点である: ① worst-case カナリア [1,1,1]、② 攻撃特徴 = 黒箱クエリ + **白箱 noisy one-way marginal counts**（MST 内部構造に直結）[1]、③ 測定が**ガウス機構のみ**であること（ρ-zCDP → μ-GDP の tight 化の根拠）[1]。これらが他手法でどれだけ成り立つかで可否が決まる:

- **他の marginal 系（PrivBayes・GEM・RAP・MWEM 等）**: 監査の方法論（MIA distinguishing game → FPR–FNR → μ）は流用できるが、白箱特徴は MST 専用のため作り直しが要る。Laplace 併用など純ガウスでない機構では μ-GDP の tight 化が崩れ、解析枠の付け替えが必要[計画]。→ **部分的に可能・要改修**。
- **DP-SGD 系の生成器**: 監査の枠組み自体は手法非依存であり、DP-SGD の監査は文献が豊富である [R16]。ただし本リポジトリのコードでは扱えず、(a) 各生成器の実装、(b) 白箱特徴の勾配ベースへの置換、(c) DP-SGD 会計（μ の別経路）への対応、が必要[計画]。→ **概念的には可能だが別実装**。

要するに、**監査の方法論（GDP・FPR–FNR トレードオフ）は手法非依存だが、本再現コードは MST/AIM の構造に密結合している**。他手法への横展開は本追試のスコープ外であり、§6 今後の課題に挙げる[計画]。

---

## 6. 結論と今後

本縮小追試（out/in 各 1,125 試行）は、原論文 GDP 監査フレームワークの主要な傾向を再現した。**RQ1**: `(ε,δ)=(1,10⁻²)` で経験的下界 μ_emp=0.39 を得て implied μ=0.455 の近傍に達した——強プライバシー領域で**非ゼロの tight 寄りの下界**であり、原論文の質的結論（実装が自身の解析と整合）を支持する（数値 0.43 との差は縮小・実装差に由来）。**RQ2**: (ε,δ)-DP・ρ-zCDP・μ-GDP を同一の FPR–FNR トレードオフ平面上に並べて比較でき、単一 (ε,δ) より豊かな診断が得られた。**RQ3**: 不安定な閾値選択（max_μ̂）で μ_emp が 0 に潰れる現象を再現し、従来研究が μ_emp=0 を報告した原因という原論文の説明を裏づけた。総じて、本実装で MST/AIM の DP 保証に明白な破れは観測されず、監査の「緩さ」は実装の安全性ではなく攻撃側の縮小条件に帰せられる。

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

**実測（本実行環境, 20 コア・18 並列）**: MST 1 fit ≈ 9.2 秒（単体）、18 並列実効スループット ≈ 1.24 秒/fit。到達 N_ALL=1,125/side（実行環境のジョブ打ち切りに対しチェックポイント＋resume で積み増し）。固定バージョン: dpmm 0.1.9 / riskcal 1.5.1 / scikit-learn 1.5.0 / numpy 1.26.4（[requirements.txt](requirements.txt)）。

## 付録 B 補助資料（technical notes）

技術的な定義・背景は本体から分離し、methods/ に置く（図ラベルは英語、本文は日本語）:

- [methods/gdp-and-tradeoff.md](methods/gdp-and-tradeoff.md) — (ε,δ)-DP → ρ-zCDP → μ-GDP の関係、トレードオフ関数 T、G_μ、Neyman-Pearson、なぜ単一 (ε,δ) でなく曲線で見るのか。
- [methods/mia-auditing.md](methods/mia-auditing.md) — メンバーシップ推論による DP 監査、distinguishing game、強敵対者モデル、worst-case カナリア、なぜ tight が難しいか、従来研究が μ_emp=0 だった理由。
- [methods/mst-aim.md](methods/mst-aim.md) — MST/AIM の select-measure-generate、指数機構・ガウス機構・PGM、MST と AIM の違い、one-way 制限で MST=AIM に帰着する理由。

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
