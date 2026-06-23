# Issue #18 調査メモ: Tight Auditing of Differential Privacy in MST and AIM

> 本ドキュメントは Issue #18 の調査（計画フェーズ）の一次記録である。
> **事実**（一次情報から直接読み取れること）と **推定**（そこからの解釈・仮説）を区別して記す。
> 事実には出典タグ `[n]` を付し、推定は `> 🔎 **推定**` ブロックで明示する。
> 本フェーズでは実装・コード実行・環境構築は行っていない（調査と草案のみ）。

## 出典一覧（取得日: 2026-06-18、すべて curl による HTTP 取得）

- `[1]` 論文 arXiv ページ: https://arxiv.org/abs/2604.18352 （HTTP 200、メタデータ・abstract を取得）
- `[2]` dpmm リポジトリ GitHub API メタデータ: https://api.github.com/repos/sassoftware/dpmm
- `[3]` dpmm README（main ブランチ）: https://raw.githubusercontent.com/sassoftware/dpmm/main/README.md
- `[4]` 監査コード（`audit-dpmm` ブランチ）ツリー: https://api.github.com/repos/sassoftware/dpmm/git/trees/audit-dpmm?recursive=1
- `[5]` 監査コード本体: `experimental/audit_dpmm/` 配下（`audit-dpmm` ブランチ）の README.md / environment.yml / code/run_attack.py / code/audit_utils.py / code/mst/adp2gdp.py / code/mst/mst.py
- `[6]` TPDP 2026 採択ページ: https://tpdp.journalprivacyconfidentiality.org/2026/ （タイトルが採択リストに掲載）
- `[7]` ローカルにある論文 PDF: `docs/2604.18352v1.pdf` → `pdftotext`（mingw64, 環境内に存在）で全文抽出し `docs/2604.18352v1.txt` に保存。**本文（全7ページ）を精読済み**。以下 §1.4 はこの一次情報に基づく。

---

## 1. 文献の特定

### 1.1 arXiv ID の検証（結論: Issue 記載の ID は正しい）

- Issue が「要検証」とした候補 ID **2604.18352 は正しい** `[1]`。
- 確認できたメタデータ `[1]`:
  - タイトル: **Tight Auditing of Differential Privacy in MST and AIM**（Issue と完全一致）
  - 著者: **Georgi Ganev、Meenatchi Sundaram Muthu Selva Annamalai、Bogdan Kulynych**（3 名）
  - 投稿日: **2026-04-20**（arXiv ID の `2604` = 2026 年 4 月と整合）
  - 主分野: **cs.CR (Cryptography and Security)**
  - PDF: https://arxiv.org/pdf/2604.18352
- TPDP 2026（Theory and Practice of Differential Privacy）の採択タイトル一覧に同名論文が掲載 `[6]`。

### 1.2 Abstract（一次情報の引用要約）`[1]`

論文 abstract の主張は以下の通り（要約。原文の数値は正確に転記）:

- MST・AIM のような最新の DP 合成データ生成器は広く使われているが、そのプライバシー保証を **tight に監査**するのは依然困難。
- **Gaussian Differential Privacy (GDP) ベースの監査フレームワーク**を導入し、**false-positive / false-negative の完全なトレードオフ**としてプライバシーを測定する。
- MST・AIM に **worst-case 設定**で適用し、**strong-privacy regime（強プライバシー領域）で初めて tight な監査**を与える。
- `(ε, δ) = (1, 10⁻²)` のとき、**経験的 μ_emp ≈ 0.43** に対し **理論が含意する μ = 0.45** が得られ、理論と実装の乖離（theory-practice gap）が小さいことを示す。

> 🔎 **推定**: ここでの "tight" は、「監査で得られる経験的下界 μ_emp が、理論上界 μ にほぼ一致する（gap が小さい）」ことを指すと解する。従来の DP-SGD 等の監査では gap が大きく緩い下界しか得られないことが多かったが、本研究は MST/AIM という marginal 系合成器について、worst-case 隣接データセットを構成することで下界を上界近くまで押し上げた、という構図と推定する。コードの構成（後述）もこの解釈と整合する。

### 1.3 何が新規か（abstract + コードからの理解）

- 事実 `[1][5]`: 監査の指標を **(ε, δ) ではなく μ-GDP**（Gaussian DP の単一パラメータ μ）に置き、**FPR–FNR トレードオフ曲線**で評価する。
- 事実 `[5]`: (ε, δ) ↔ μ の相互変換が `adp2gdp.py` に実装されている（後述 2.3）。
- 事実 `[1]`: 「strong-privacy regime で初めて tight」と明記。

### 1.4 PDF 本文の精読結果（事実 `[7]`、以前の未読論点を解消）

本文（4 ページ本編 + 付録 A）を `pdftotext` で抽出して精読した。abstract・コードからの推定が概ね正しいことを確認し、未解決だった論点を以下で解消する。

**(a) AIM 監査コードが別に無い理由（旧・未解決論点 #2 を解消）`[7]`**
- 本実験は MST/AIM を **「one-way marginal のみ測定する制限構成」** で扱う（§3「MST and AIM. We study MST and AIM under a restricted configuration where only one-way marginals are measured.」）。
- この制限下では依存グラフが固定され高次 marginal を選ばないため、**MST と AIM は同一の independent-marginal モデルに帰着する**（"reduce to the same independent-marginal model"）。
- 全予算を one-way 測定に割り当て、用いる機構が Gaussian 機構のみになるため μ-GDP 枠で解析可能になる。
- → ゆえに公開コードに `aim/` ディレクトリが無く `mst/` のみでも、主実験としては整合する（MST=AIM）。**AIM 専用の追加実装は主構成では不要**。
- 付録 A では制限を緩め、**2-way・3-way marginal** で学習した MST/AIM も監査。高次 marginal でも監査は弱まらず、むしろわずかに tight（3-way で μ_emp≈0.44, 2-way ブラックボックスで μ_emp≈0.43, vs 理論 μ=0.45）`[7]`。

**(b) worst-case 構成・攻撃・統計（コードからの理解を本文で確認）`[7]`**
- 隣接データ: `Dout` = 同一レコード `[0,0,0]` を 10 個、`Din` = それに標的レコード `[1,1,1]` を 1 つ追加（§3「Neighboring Datasets and Target Record」）。標的の全 marginal への影響を最大化する worst-case。
  - ※ 本文の記述（Dout=10 行・合成サイズ 50）と、エージェントが読んだ公開コードの既定値（`LEN_SYNTH=25` 等）には差がある可能性。**再現時の注意点**として §3.x に後述。
- 脅威モデル: **hybrid black/white-box**。ブラックボックス特徴 = 合成データ上の全クエリ評価（Query-based MIA [21]）、ホワイトボックス特徴 = モデル内部の noisy one-way marginal counts。
- distinguishing game: `(ε,δ)=(1,10⁻²)` で **独立に 10,000 モデル学習（Dout/Din 各 5,000）**、各モデルは size 50 の合成データと noisy marginals を出す。出力を **train 4,000 / validation 2,000 / test 4,000** に分割。
- 分類器: 本文は **XGBoost** と明記（§3 DP Distinguishing Game）。アブレーションで Random Forest も比較（Fig.3）。
  - ※ エージェントが読んだ公開コードは `GradientBoostingClassifier`/`RandomForest`。本文 XGBoost との差は **実装差/版差**として再現注意点に記録。
- 閾値選択: validation で advantage（TPR−FPR）を最大化する閾値 τ\* を選び、**test は 1 回だけ評価**（Fig.2）。
- μ の統計推定: **Zanella-Béguelin et al. [42] に着想を得た joint Bayesian アプローチ**で、μ-GDP 領域が事後質量 90% を含むような下界 μ_emp を導出。Nasr et al. [32] に従い「ベイズ下界であり頻度論的被覆を必ずしも持たないが、経験的にはより tight」と明記。

**(c) 主要結果（本文の数値、事実 `[7]`）**
- 主張: `(ε,δ)=(1,10⁻²)` → 理論 μ=0.45 に対し経験的 **μ_emp≈0.43**。strong-privacy regime（ε=1）で**初の tight audit**。従来研究 [1,24] は同領域で μ_emp=0（null）だった。
- Fig.1: 経験的 FPR–FNR 曲線が、機構内部の **ρ-zCDP 経由で含意される μ**（実線・赤）にほぼ一致。一方、**(ε,δ)→μ の直接変換**（破線）はより大きい μ（弱いプライバシー）を出す。この差は中間の zCDP 変換 [5]（数値安定だが保守的）に由来。
- Fig.3 アブレーション: 「Default」（joint_beta + Dout サイズ既定 + ブラックボックス+ホワイトボックス + 閾値=max advantage）が最も tight。**不安定な閾値選択基準（推定 μ̂ を validation で最大化）は過小な閾値を選び FPR を過大にして下界を 0 に潰す** → これが従来研究の μ_emp=0 の原因と説明。
- 拡張性: 枠組みは Gaussian 機構ベースの他の DP 生成手法にも適用可能（結論）。

> 🔎 **推定（再現上の含意）**: 公開コードの既定値（`N_ALL=5000`/side、`LEN_SYNTH=25`）と本文記述（5,000/side、合成サイズ 50）は概ね一致するが細部に差があり、分類器も GradientBoosting（コード）vs XGBoost（本文）と異なる。**完全一致での数値再現は難しく、追試の目標は「μ_emp が μ=0.45 の近傍に来て、かつ閾値選択基準を変えると 0 に潰れる現象が再現されること」**（傾向の再現）に置くのが現実的と判断する。

---

## 2. コード／データの確認

### 2.1 dpmm リポジトリの性質（事実 `[2][3]`）

- フルネーム: **sassoftware/dpmm**、説明: 「synthetic tabular data generation with rich functionality and end-to-end Differential Privacy guarantees」`[2]`。
- 言語: **Python**、ライセンス: **Apache-2.0**、作成 2025-03-25、最終更新 2026-05-04、デフォルトブランチ `main` `[2]`。
- 正式名称は **_dpmm_: Differentially Private Marginal Models**。`select-measure-generate` パラダイム + Private-PGM に基づく DP marginal 合成ライブラリ `[3]`。
- 実装モデル: **PrivBayes+PGM / MST / AIM** `[3]`。DP 前処理（ドメイン抽出・離散化: Uniform / PrivTree）、floating-point 精度対応も含む `[3]`。
- 関連論文（dpmm ライブラリ自体）: arXiv **2506.00322**（`mahiou2025dpmm`, TPDP 2025）`[3]`。← Issue #18 の監査論文（2604.18352）とは**別物**。
- README は「DP auditing of underlying mechanisms and models/pipelines」を機能として挙げる `[3]` が、main ブランチの `src/dpmm/` 配下に監査専用モジュールは見当たらない（audit 関連で名前一致したのは `mbi/inference.py` のみ）`[4]`。

### 2.2 監査コードの所在（重要な発見、事実 `[4][5]`）

- **監査コードは `main` ではなく `audit-dpmm` ブランチの `experimental/audit_dpmm/` にある** `[4]`。
- arXiv abstract の「Our code is publicly available」のリンク先は **github.com/sassoftware/dpmm** `[1]`。監査論文の専用リポジトリは別途存在せず、dpmm のブランチに同梱されている。
- `experimental/audit_dpmm/` の構成 `[5]`:
  ```
  experimental/audit_dpmm/
  ├── README.md            … 「Tight Auditing ...」論文の course code と明記
  ├── environment.yml      … conda 環境（python=3.11, dpmm, riskcal ほか）
  ├── code/
  │   ├── run_attack.py    … 攻撃（特徴量生成）スクリプト（手順1）
  │   ├── run_audit.ipynb  … 監査・プロット（手順2、本フェーズでは中身未読）
  │   ├── audit_utils.py   … 監査ロジック（FPR/FNR・μ 推定・信頼区間）
  │   └── mst/
  │       ├── __init__.py
  │       ├── mst.py       … dpmm の MST を薄くラップしホワイトボックス特徴を露出
  │       └── adp2gdp.py   … (ε,δ) ↔ μ-GDP 変換
  └── data/                … features.pkl（事前計算特徴）、*.pdf（tradeoff/valid/abl 図）
  ```
- README の再現手順 `[5]`: 「1. `run_attack.py` を実行 → 2. `run_audit.ipynb` を実行」。
- 同ブランチ群には Issue #18 のタイトルと直接対応する **`18-privacy-leak-via-data-dependent-domain-inference`** ブランチも存在し、main には「Fix domain privacy leak (#19)」「Update mst.py (#22)」がマージ済み `[2][4]`。

> 🔎 **推定**: この `tpdp2026-18` リポジトリの Issue #18 は、dpmm 側の同名トピック（data-dependent domain inference によるプライバシー漏洩）と関連した監査研究の追試を意図していると思われる。dpmm の domain 抽出が非 DP だと監査で漏洩が検出されうる、という論点が論文・dpmm 修正の双方に通底していると推定する（PDF 本文で要確認）。

### 2.3 監査手法の詳細（コードからの事実 `[5]`）

攻撃・監査のパイプラインは典型的な **membership inference ベースの経験的 DP 監査**:

1. **worst-case データ構成**（`run_attack.py`）: `N_COLS=3` の全 0 行列を `df_out`、そこに 1 行だけ全 1 のレコードを足したものを `df_in` とする隣接データセット。差分は 1 レコード（"canary"）。`EPSILON=1, DELTA=1e-2`, 合成サンプル長 `LEN_SYNTH=25`, 試行 `N_ALL=5000`。
2. **特徴量化**: 合成データに対するクエリ集合のカウント（ブラックボックス特徴）＋ `model.measures` から取り出した周辺測定値（ホワイトボックス特徴）を連結。`df_in / df_out` それぞれで MST を 5000 回学習・生成し特徴を蓄積 → `data/features.pkl`。
3. **攻撃モデル**（`audit_utils.run_audit`）: out/in 特徴を Train/Valid/Test に分割し、`GradientBoostingClassifier`（または RandomForest）を訓練。**閾値選択は Valid のみで行い、Test は 1 回だけ評価**（評価の公平性・リーク防止が設計に組み込まれている）。
4. **μ の推定**:
   - 点推定 `_mu_from_fpr_fnr`: `μ = Φ⁻¹(1−FPR) − Φ⁻¹(FNR)`（GDP のトレードオフ曲線から）。
   - 下界 `_mu_lo_from_counts`: 2 方式。`bonferroni_cp`（FPR/FNR それぞれに Clopper–Pearson 上側信頼限界を取り Bonferroni 補正）と `joint_beta`（FPR~Beta, FNR~Beta の Jeffreys 事後分布で μ-GDP 実現可能領域の事後質量から下界。`riskcal.analysis.get_beta_from_gdp` を使用）。既定は `joint_beta`, `alpha=0.1`。
5. **(ε,δ)↔μ 変換**（`adp2gdp.py`）: `δ(ε,μ) = Φ(−ε/μ + μ/2) − e^ε·Φ(−ε/μ − μ/2)`（Tight Auditing DPML 論文の式(6)）を `brentq` で逆解きし `μ_from_eps_delta` を提供。`(1, 1e-2)` を入れると理論 μ が出る（abstract の μ≈0.45 と整合）。

- 依存（`environment.yml`）`[5]`: python=3.11, tqdm, scikit-learn, pandas, matplotlib, jupyterlab, pip 経由で **dpmm** と **riskcal**。
- `mst/mst.py` は `dpmm.models.base` を import する **dpmm 依存のラッパ**で、`private-pgm` の MST を一般化したもの `[5]`。

> 🔎 **推定**: 公開コードに見える範囲は **MST のブラックボックス+ホワイトボックス監査**が中心。abstract は AIM も対象とするが、`code/` 配下に `aim` ディレクトリは見当たらず（`mst/` のみ）`[4][5]`。AIM 監査のコードは（a）notebook 内に直書き、（b）未公開、（c）dpmm 本体の AIM を直接呼ぶ、のいずれか。PDF 本文と `run_audit.ipynb` の確認で切り分ける必要がある。

---

## 3. 再現可否の判断（計画フェーズの結論）

### 3.1 現実的に手元で回せるもの（推奨スコープ）

> 🔎 **推定（実行は次フェーズ。本フェーズは可否判断のみ）**

- **最小デモA（dpmm 単体）**: `pip install dpmm` で MST/AIM の合成を公開データ（README の wine 例、または UCI Adult 等）で動かす。計算は軽量。リスク小。
- **再現B（監査の縮小版）**: `audit-dpmm` ブランチの `run_attack.py` を**試行回数 `N_ALL` を 5000→数百に縮小**して特徴量を生成し、`audit_utils.run_audit` で FPR–FNR トレードオフ曲線・μ_hat・μ_lower を算出・可視化。論文の μ_emp≈0.43 と同オーダーが出るかを確認。
- **再現C（完全再現）**: `N_ALL=5000` で `run_attack.py` を回し（multiprocessing、CPU バウンド）、`run_audit.ipynb` のプロット（tradeoff/valid/abl）を再現。**最も重いが最も論文に忠実**。

### 3.2 必要環境・入力データ

- Python **3.11**（dpmm は 3.10/3.11 のみ対応 `[3]`）。
- 主要依存: `dpmm`, `riskcal`, scikit-learn, scipy, pandas, matplotlib, tqdm（jupyter はノート再現用）`[5]`。
- 入力データ: **公開データセットは不要**。`run_attack.py` は合成的な 0/1 ビットの隣接データセットを内部生成するため、外部データの取得・代替は不要 `[5]`。dpmm 単体デモ（A）には wine / Adult 等の公開表データで代替可。
- 計算資源: `N_ALL=5000` × in/out それぞれ MST 学習・生成 = 1 万回の MST 実行。`maxtasksperchild=1` の Pool 並列。**CPU コア数に強く依存**。縮小版（B）なら通常 PC で数分〜十数分と推定。完全再現（C）は要事前スモークで外挿。

### 3.3 Windows + uv 環境の落とし穴（指摘）

> 🔎 **推定・注意**

- 監査コードの環境定義は **conda の `environment.yml`** で uv 向けではない `[5]`。uv で再現するなら `requirements.txt` を別途起こし、`dpmm`・`riskcal` のバージョンを固定する必要がある（再現性規約 §4）。
- `run_attack.py` は **`multiprocessing.Pool` + `imap_unordered`** を使う `[5]`。Windows は `fork` でなく `spawn` のため、`if __name__ == "__main__":` ガード必須（コードは満たしている）。ただし spawn では各ワーカが全モジュールを再 import するため起動コストが Linux より高い。
- `run_attack.py` は出力先を **相対パス `../data/features.pkl`** に書く `[5]`。実行は `code/` ディレクトリを cwd にする前提。Windows + 当エージェントの「cwd がリセットされる」制約と相性が悪く、ラッパスクリプトで絶対パス化が無難。
- dpmm は `poetry install`（ローカル）か `pip install dpmm`（PyPI）`[3]`。uv では `uv pip install dpmm` で取得しロックする。
- `riskcal` の対応 Python・依存は未確認（要 PyPI 確認）。`get_beta_from_gdp` の API 安定性に依存するためバージョン固定必須。
- cp932（日本語 Windows）デフォルトエンコーディング起因の文字化けに注意（出力は UTF-8 明示）。

---

## 4. 未解決・ユーザー確認が必要な論点

- ~~**PDF 本文が未読**~~ → **解消**。`pdftotext` で全文抽出し精読済み（§1.4）。AIM 監査の手法（one-way 制限で MST=AIM）・主要結果・信頼区間方式（joint Bayesian, 90% 事後質量）を確認した。
- ~~**AIM 監査コードの所在**~~ → **概ね解消**。主実験は one-way 制限により MST=AIM に帰着するため AIM 専用コードは不要（§1.4(a)）。AIM 名義での個別再現は付録 A の高次 marginal 設定で別途可能だが必須ではない。

残る要判断（次フェーズの実行スコープに関わる）:

1. **再現のスコープ**: 3.1 の A/B/C のどこまでをやるか。計算資源（コア数・許容時間）次第。完全再現 C は要事前スモーク。**推奨は B（縮小再現）＋ A（dpmm 単体デモ）** で、傾向（μ_emp が μ=0.45 近傍 + 閾値基準で 0 に潰れる現象）の再現を目標にする（§1.4 推定）。
2. **dpmm/riskcal のバージョン固定**: `environment.yml` はバージョン未固定 `[5]`。再現性のため固定版を決める必要（次フェーズ実行時に `uv pip freeze`）。
3. **完全一致 vs 傾向再現**: 公開コードと本文に細部差（分類器 GradientBoosting vs XGBoost、合成サイズ 25 vs 50 等、§1.4(b)）。数値完全一致は狙わず傾向再現を目標にする方針でよいか。
4. **成果物モード**: 推奨 = モードB（論文型）主 + モードA（技術解説）従（plan §0.1）。承認可否。
