# MST / AIM の差分プライバシーを GDP で tight に監査する：論文 arXiv:2604.18352 の縮小追試

> 対象 = MST / AIM（DP 合成データ生成器） ／ 対象論文 = *Tight Auditing of Differential Privacy in MST and AIM*（[arXiv:2604.18352](https://arxiv.org/abs/2604.18352), TPDP 2026）[1] ／ リポジトリ = <https://github.com/gghatano/tpdp2026-mst-aim-audit> ／ 最終更新 = 2026-06-20

> ⚠️ **ステータス注記**: 本レポートは**進行中の中間報告**であり、結果章（§3）の数値・図表は **N_ALL=500/side（= 1,000 fit）・単一シードの暫定値**である（原論文は 5,000/side）。実験スコープは A（dpmm 単体での MST/AIM 合成デモ）＋ B（監査の縮小再現）に限定し[計画]、数値完全一致でなく**傾向の再現**を目標とする。本文に記載する数値は**測定済みのもののみ**とし、未実施・未取得の箇所は「未測定」と明記する。完全再現 C・AIM/高次 marginal（付録 A 相当）は当面スコープ外である[計画]。

---

## Abstract

差分プライバシー（DP）合成データ生成器のうち MST [R5] と AIM [R6] は、強いプライバシー・有用性トレードオフと NIST コンペ優勝・公的統計での採用実績から広く普及している[1]。一方で、その**プライバシー保証を tight に監査する**こと——すなわち実装が主張通りの保証を満たすかを経験的に検証すること——は依然として難しく、特に **強プライバシー領域（ε=1 など）では従来の監査が緩い／ゼロの下界しか与えられなかった**[1]。

本追試は、原論文の **Gaussian Differential Privacy（GDP）ベースの監査フレームワーク**を縮小規模で再現する。プライバシーを単一の (ε,δ) 値ではなく、強敵対者によるメンバーシップ推論攻撃（MIA）の **FPR–FNR トレードオフ全体**として測り、μ-GDP の単一パラメータ μ に要約する[1]。worst-case 隣接データセット（標的レコードを 1 件だけ加える構成）と hybrid black/white-box 脅威モデルのもとで、distinguishing game により経験的下界 μ_emp を推定する[1]。

主要結果（縮小再現、**N_ALL=500/side の暫定値**）:

- (ε,δ)=(1,10⁻²) で理論目標は implied μ=**0.455**（ρ-zCDP 経由）／直接変換 μ=**0.532** であった。Default 構成（GradientBoosting・max_advantage・joint_beta 90%）の経験的下界は **μ_emp=0.275**（点推定 μ̂=0.178、攻撃 AUC=0.555）で、原論文の μ_emp≈0.43 [1] には届かず、理論 μ との間に **gap が残った**。これは主に試行数の縮小（500/side、原論文は 5,000/side）による統計的解像度の低さに帰せられる（攻撃 AUC が 0.55 程度に留まる）。
- 閾値選択基準を不安定なもの（μ̂ 最大化）や信頼区間を bonferroni_cp に変えると **μ_emp が 0 に潰れる**現象が縮小規模でも再現した（§3.4）。逆に下界そのものを選択基準にすると 0.93 まで過大評価され、「設定が結果を作る」リスクを確認した。

結論（暫定）:

- 縮小規模では μ_emp（0.275）は理論 μ（0.455）を**下回り**、原論文のような tight な一致（μ_emp≈μ）は本試行数では再現しなかった。一方、FPR–FNR 曲線上で複数の DP 概念を同一平面で比較でき（図 1）、不安定な閾値選択が μ_emp を 0 に潰す現象も再現した。すなわち**方法論の枠組みと定性的傾向は再現したが、数値の tight 性は試行数に依存する**——これが本縮小追試の暫定結論である。

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

| 縮小した軸 | 本追試（暫定） | 原論文 [1] | 縮小の理由 |
|---|---|---|---|
| 試行数 N_ALL | **500 / side（= 1,000 fit）** | 5,000 / side（= 10,000 fit） | **計算時間**（本暫定報告は 500/side。傾向確認用） |
| シード | 1 本（audit_seed=13、攻撃生成は secure RNG で seed 不能） | 多数 | 計算時間 |
| (ε,δ) | (1, 10⁻²) 単一 | 複数設定を掃引 | **スコープ**（強プライバシー領域の 1 点に集中） |
| marginal の次数 | one-way のみ | 付録 A で 2/3-way | **理論的に正当**: one-way 制限では選択機構が消え MST=AIM に帰着する（§2.6・付録 B [mst-aim](methods/mst-aim.md)）。高次は PGM 推論が重くスコープ外 |

**所要時間（実測、本実行環境）**: 実行環境は Ubuntu 24.04 / 4 vCPU（worker=3）。**per-fit ≈ 4.84 秒**（N_ALL=500/side, 3 worker, MST を 1 試行あたり 2 回 fit）で、N_ALL=500/side（= 1,000 fit）の総所要は約 **81 分**であった（`outputs/attack_meta_N500.json`）。E0 スモーク（N=50/side, 2 worker）では per-fit ≈ 7.37 秒（`outputs/attack_meta_N50.json`）で、worker 数の差が効いている。この per-fit を線形外挿すると、フル再現 C（10,000 fit・単一 (ε,δ)）は本環境で概ね **13 時間規模**（≈ 10,000 × 4.84 / 3,600）となり、当初見積もり（1.5–2.5 時間）はコア数を多めに仮定した楽観値であったことが判明した。完全再現は別途リソースを確保して判断する。

> 🔎 **書き分けの含意**: 「縮小＝計算節約」が当てはまるのは N_ALL とシードのみである。単一 (ε,δ) と one-way 制限は計算ではなく**スコープ・理論的正当性**による選択であり、後者は主結果の妥当性を損なわない（むしろ AIM もカバーする）[1][計画]。なお本暫定報告の N_ALL=500/side は原論文（5,000/side）より 1 桁小さく、§5 の統計的限界が強く効く点に注意。

---

## 3. 結果

> ⚠️ 本章の数値・図表は **N_ALL=500/side（= 1,000 fit）・単一シード（audit_seed=13）の暫定値**である。原論文（5,000/side）より 1 桁小さく、絶対値は揺れが大きい。傾向の確認を目的とし、断定は避ける（実行環境・バージョンは §3.3 脚注）。

### 3.1 FPR–FNR トレードオフ曲線（RQ2）

![図1 FPR-FNR トレードオフ](figures/tradeoff.png)

図 1: MIA の経験的プライバシートレードオフ（黒）と、複数の DP 概念のもとでの理論境界（implied μ-GDP 赤実線 μ=0.45／(ε,δ)→μ 直接変換 赤破線 μ=0.53／ρ-zCDP・(ε,δ)-DP の context 線／random guess）の比較。

**所見**: 経験的曲線（黒）は implied μ-GDP フロンティア（赤実線）の**外側**（random guess 寄り）に位置し、理論が許す上界よりも**緩い**（攻撃が弱い）。原論文 Fig.1 では経験曲線が μ-GDP 境界にほぼ張り付くが、本縮小規模では攻撃が境界まで到達できておらず、μ_emp < μ（§3.3）と整合する。複数の DP 概念を同一平面で比較する枠組み自体（RQ2）は機能している。

### 3.2 閾値選択曲線（RQ1）

![図2 閾値選択](figures/valid_threshold.png)

図 2: validation データ上で FPR (α)・FNR (β)・empirical advantage (TPR−FPR) を決定閾値の関数として描いたもの。選択された閾値は **τ\*=0.535**（advantage 最大化、validation のみで選択し test には未使用）。

**所見**: advantage は τ*=0.535 付近で最大となるが、ピーク自体が浅い（最大 advantage ≈ 0.07）。これは縮小規模で攻撃の分離能力が弱いことを反映し、閾値選択が不安定になりやすい下地（§3.4 で μ_emp が 0 に潰れる現象）を示す。

### 3.3 μ_emp / μ_lower / AUC の表（RQ1）

| 指標 | 値（縮小再現, N_ALL=500/side） | 原論文 [1] |
|---|---|---|
| 理論 μ（implied, via ρ-zCDP） | **0.455** | 0.45 |
| 理論 μ（(ε,δ)→μ 直接変換） | **0.532** | （Fig.1 破線、より大きい値） |
| 経験的 点推定 μ̂ | **0.178** | ≈0.43 |
| 経験的下界 μ_emp（joint_beta, 90%, Default） | **0.275** | （Fig.3 Default） |
| 経験的下界 μ_emp（bonferroni_cp） | **0.000** | （Fig.3 比較バー） |
| 攻撃 AUC（test, 診断用） | **0.555** | （非掲載） |

τ*=0.535 における test の FPR=0.40 / FNR=0.53 / empirical advantage=0.07、AUC_valid=0.531。

**所見（RQ1）**: 経験的下界 μ_emp=0.275 は理論 implied μ=0.455 を下回り、原論文の μ_emp≈0.43 にも届かない。攻撃 AUC が 0.555 と random guess 近傍に留まることから、これは**実装のプライバシー漏れが小さい**というより**縮小試行で攻撃が十分な統計的解像度を得られていない**ことを主因と解釈する（§5.1）。

> 脚注（実行条件）: OS = Ubuntu 24.04（Linux 6.18.5）／Python 3.11.15／dpmm 0.1.9・riskcal 1.5.1・scikit-learn 1.5.0・numpy 1.26.4・scipy 1.17.1。N_ALL=500/side（= 1,000 fit）、test 分割 200/100/200（40/20/40）、audit_seed=13。攻撃特徴生成は MST の secure RNG により seed 不能（DP として正しい挙動）であり、本数値は単一実行の暫定値。

**収束（補足）**:

![図4 μ_emp の実効サイズ依存](figures/convergence.png)

図 4: 実効サイズ別の経験的 μ。size=250 → μ_emp=0.89（μ̂=2.70, AUC=0.516）、size=500 → μ_emp=0.275（μ̂=0.178, AUC=0.555）と**非単調**であった。size=250 の高値は test=100 件の小標本ノイズ（μ̂ が 2.7 と非現実的に発散）であり、収束傾向を論じるにはサイズ・シードの拡張が必要である（§5.3）。

### 3.4 アブレーション（RQ3）

![図3 アブレーション](figures/ablation.png)

図 3: 監査設定を Default から 1 要素ずつ変更したときの経験的下界 μ_emp（test）。

| 構成 | μ_emp | 備考 |
|---|---|---|
| Default（max_advantage / joint_beta / GradientBoosting / 黒箱+白箱） | 0.275 | 基準 |
| 閾値選択 = max_mu_hat | **0.000** | **不安定な選択で 0 に潰れる**（RQ3 再現） |
| 閾値選択 = max_mu_lower | 0.930 | 下界そのものを選択基準 → 過大評価（楽観バイアス） |
| 信頼区間 = bonferroni_cp | **0.000** | 保守的 CI で 0 に潰れる |
| 分類器 = RandomForest | 0.491 | GradientBoosting より高め（縮小規模の揺れ） |
| 脅威 = 黒箱のみ | 0.254 | Default（黒箱+白箱 0.275）とほぼ同等：白箱寄与は小 |

**所見（RQ3）**: 「不安定な閾値選択（max_mu_hat）・保守的信頼区間（bonferroni_cp）で μ_emp が 0 に潰れる」という原論文の説明 [1] は、縮小規模でも明瞭に再現した。逆に下界を直接最大化する選択（max_mu_lower）は同一統計量への過適合で μ_emp=0.93 まで膨らみ、**「結果が設定でなく実装のプライバシーを反映している」ことの確認には Default 系の安定な選択が必須**であることを裏づける（C3）。白箱特徴の寄与は本規模では小さい（0.254 vs 0.275）。

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

本暫定結果では μ_emp=0.275 が implied μ=0.455 を**下回った**。この gap は原理的に 3 つの解釈がありうる: (a) dpmm 実装が分析より強くプライバシーを守っている（漏れが小さい）、(b) 縮小試行・単一シードによる**監査側の緩さ**（攻撃が境界まで到達できていない）、(c) 実装/移植のバグ。本追試は (b) を主因と判断する——攻撃 AUC が 0.555 と random guess 近傍に留まり（図 1 で経験曲線が境界の外側）、原論文が 5,000/side で μ_emp≈0.43 を得ている [1] のに対し本試行は 500/side と 1 桁小さいためである。すなわち本数値は**「実装が tight でない」証拠ではなく、監査の統計的解像度不足**を示す。tight 性の判定には N_ALL の拡大が前提となる（§6）。

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

縮小規模（N_ALL=500/side、単一シード）の暫定追試として、RQ への回答は次のとおり:

- **RQ1（μ_emp は理論 μ に近いか）**: 否。μ_emp=0.275 は implied μ=0.455 を下回り、原論文の μ_emp≈0.43 にも届かなかった。攻撃 AUC=0.555 から、これは実装の緩さでなく試行数縮小による監査の解像度不足と判断する（§5.1）。
- **RQ2（FPR–FNR 曲線で複数 DP 概念を比較できるか）**: 是。経験曲線と implied μ-GDP／直接変換 μ／ρ-zCDP／(ε,δ)-DP を同一平面で描画でき（図 1）、枠組みは機能した。
- **RQ3（不安定な閾値選択で μ_emp が 0 に潰れるか）**: 是。max_mu_hat・bonferroni_cp で μ_emp=0、max_mu_lower で過大評価と、設定依存性を明瞭に再現した（図 3）。

総じて、**方法論の枠組みと定性的傾向（RQ2・RQ3）は再現したが、数値の tight 性（RQ1）は試行数に依存し本規模では未達**である。

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

**実測（本暫定報告）**: per-fit ≈ 4.84 秒（N_ALL=500/side, 4 vCPU・worker=3）、縮小版総所要 ≈ 81 分（`outputs/attack_meta_N500.json`）。E0 スモーク（N=50/side, worker=2）は per-fit ≈ 7.37 秒（`outputs/attack_meta_N50.json`）。固定バージョン: dpmm 0.1.9・riskcal 1.5.1・scikit-learn 1.5.0・numpy 1.26.4・scipy 1.17.1（Python 3.11.15）。本報告の確定 N_ALL = 500/side（傾向確認用の暫定値。tight 性確認には拡大が必要）。

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
