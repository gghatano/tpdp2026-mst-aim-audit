# 実験計画草案 Issue #18: MST/AIM の Tight な DP 監査の追試

> 本計画は `experiment-plan` スキルのテンプレートに従う。**草案**であり、実行（`experiment-run`）は別フェーズ。
> 出典タグ `[n]` は `docs/research/issue-18-survey.md` の出典一覧と対応する。
> 想定する成果物は GitHub Pages 公開用の自己完結 HTML レポート（`demo-report-builder` 準拠）。

## 0. 背景と想定ユースケース

- 対象論文: Tight Auditing of Differential Privacy in MST and AIM（Ganev, Annamalai, Kulynych, arXiv:2604.18352, TPDP 2026）`[1][6]`。
- 監査コード: `sassoftware/dpmm` の `audit-dpmm` ブランチ `experimental/audit_dpmm/` `[4][5]`。
- **業務ユースケース（1 行）**: DP 合成データ（MST/AIM）を外部提供する際、「実装が主張通りのプライバシー（μ-GDP / (ε,δ)）を本当に満たすか」を、攻撃成功の FP–FN トレードオフから経験的に監査して提供可否を判断する。

## 0.1 成果物モードの推奨

- **推奨: モードB（アカデミック論文型）を主、モードA（技術解説+デモ型）を従**。
  - 理由: 本件は「論文の主張（μ_emp ≈ μ で gap が小さい）を追試し、限界を正直に述べる」実証研究であり、Abstract / 方法 / 結果 / 考察・限界 / 結論 / References の論文体が中心に適する。
  - ただし読者向けに、GDP / f-DP / FPR–FNR トレードオフ・membership inference 監査の**技術解説ページ（モードA 的な method-*.md）を分離**して付ける。規約 §2 の「本体は検証対象主軸、アルゴリズム固有の深掘りは個別ページ」に従う。

---

## 実験 E1: MST の経験的 GDP 監査の再現（縮小版）

- **目的**: レポート結果章の中核主張「MST 実装の経験的下界 μ_emp が理論 μ に近い（tight）」を、縮小試行で確認する。
- **仮説**: `(ε,δ)=(1,1e-2)` で、論文の μ_emp≈0.43 / 理論 μ≈0.45 `[1]` と同オーダー（μ_emp が μ をわずかに下回る）の結果が出る。棄却（大きく下回る/上回る）なら、試行数不足・分類器・閾値選択・信頼区間方式の影響として解釈し E3 で切り分ける。
- **指標（出典付き）**:
  - FPR–FNR トレードオフ曲線、μ-GDP（点推定 `μ̂ = Φ⁻¹(1−FPR)−Φ⁻¹(FNR)`）`[5]`。GDP の定義に準拠（Dong et al., Gaussian Differential Privacy）。
  - μ の下界 μ_lower（`joint_beta` 既定、`bonferroni_cp` 併記）`[5]`。riskcal / Bayesian DP estimation に準拠。
  - 攻撃 AUC（診断用、閾値選択には不使用）`[5]`。
  - (ε,δ)↔μ 変換（`adp2gdp.py` 式(6)）`[5]`。
- **比較条件**: 対象 = MST（dpmm 実装ラッパ）`[5]`。`(ε,δ)=(1,1e-2)`。worst-case 隣接データ（全0 vs 全0+1行）は `run_attack.py` の既定 `[5]`。
- **公平性の担保**:
  - Train/Valid/Test 分割を固定。**閾値は Valid のみで選択、Test は 1 回評価**（コードに内蔵 `[5]`、リーク防止）。
  - シード固定（`random_state`）。試行数 `N_ALL` は縮小（例 300–1000）で実施し、本文では「単発・縮小のため傾向を読む」と注記（規約 §2）。
  - ベースライン: 「攻撃 AUC≈0.5 / μ̂≈0」（無情報＝ランダム推測）を下限基準として併置。
- **実行**: `run_attack.py`（`N_ALL` を縮小に変更）→ `run_audit.ipynb` 相当の処理をスクリプト化。所要時間は事前スモーク（後述 E0）で外挿。シード 3 本程度。
- **完了基準**: トレードオフ曲線図 + μ̂ + μ_lower + AUC が、実行環境・シード・dpmm/riskcal バージョン付きで得られ、結果章に図表として載せられる。

## 実験 E0（前提・スモーク）: 単発計測と外挿

- **目的**: `N_ALL=1` あたりの MST 学習+生成の所要時間を計測し、縮小版・完全版の総時間を外挿（実行可能性の事前確認、規約 §6）。
- **完了基準**: 1 試行の wall-clock と、想定 `N_ALL`・コア数での総時間見積もりが得られる。重ければ E1 の `N_ALL` を下げる判断材料にする。

## 実験 E2（任意）: AIM／高次 marginal の監査

- **目的**: 論文付録 A に対応。主実験では one-way 制限により **MST=AIM に帰着**する（survey §1.4(a)）ため、AIM 名義の独立再現は **2-way/3-way marginal** 設定で意味を持つ。
- **位置づけの更新**: 旧・未解決論点「AIM コードの所在」は解消済み。主構成で AIM 専用コードは不要。高次 marginal 設定は dpmm 本体の対応機能を `mst/mst.py` 同様にラップして追加実装する想定。
- **仮説**: 高次 marginal でも監査は弱まらず、μ_emp は理論 μ=0.45 近傍を保つ（本文: 3-way で≈0.44、2-way 黒箱で≈0.43）`[7]`。
- **指標・公平性**: E1 と同一プロトコル（同一 (ε,δ)・同一分割規約・同一シード集合）。

## 実験 E3（任意）: 監査設定の感度分析（アブレーション）

- **目的**: 結果が「設定」でなく「実装のプライバシー」を反映していることの確認。考察章を支える。
- **比較条件**: 分類器（GradientBoosting vs RandomForest）、閾値選択（max_advantage / max_mu_hat / max_mu_lower）、信頼区間（joint_beta / bonferroni_cp）、特徴（黒箱のみ vs 黒箱+白箱）`[5]`。
- **公平性**: E1 と同一データ・同一シード・同一分割で 1 軸ずつ変更。
- **完了基準**: μ_lower が設定にどう依存するかの表 + 「白箱特徴の寄与」の所見。論文の `data/abl.pdf` と対応づく。

---

## 必要環境・入力データ（再現補足の草案）

- Python 3.11（dpmm は 3.10/3.11 のみ `[3]`）。**uv で `requirements.txt` を起こし `dpmm`・`riskcal` を固定**（`environment.yml` は conda・未固定のため流用しない）`[5]`、規約 §4。
- 依存: dpmm, riskcal, scikit-learn, scipy, pandas, matplotlib, tqdm（+ jupyter）`[5]`。
- 入力データ: **不要**（`run_attack.py` が合成隣接データを内部生成）`[5]`。
- 出力: `outputs/`（features.pkl）, `figures/`（tradeoff/valid/abl）。生成物は再実行で再生成可能に。

## 想定リスク

1. ~~PDF 本文未読~~ / ~~AIM コード非公開~~ → **解消**（survey §1.4。本文精読済み、one-way 制限で MST=AIM）。
2. **コードと本文の細部差**: 分類器（コード GradientBoosting vs 本文 XGBoost）、合成サイズ（コード 25 vs 本文 50）、Dout サイズ等 `[5][7]`。→ **数値完全一致は狙わず傾向再現を目標**（μ_emp が μ=0.45 近傍 + 不安定な閾値基準で 0 に潰れる現象の再現）。差は再現注意点としてレポートに明記。
3. **計算コスト**: 完全再現は MST を 1 万回実行。→ E0 で外挿し `N_ALL` を調整、単発断定を避けマルチシードで傾向を読む（規約 §2）。
4. **Windows + uv の落とし穴**: multiprocessing の spawn 起動コスト、相対パス `../data/` 書き出し、cp932 文字化け、`riskcal` の Win 対応未確認 `[5]`。→ 絶対パス化・UTF-8 明示・事前 import スモーク。
5. **再現性**: dpmm/riskcal のバージョン未固定 `[5]`。→ ロック必須。

## 作業 issue 起案の方針（実行への受け渡し）

- 計画確定後、E0→E1 を 1 つの作業 issue（implementer 担当、worktree `issue-18-mst-audit`）として起案。完了条件は「features.pkl 生成（件数チェック）＋ tradeoff 図 PNG 生成＋ μ̂/μ_lower/AUC を JSON 出力」など機械的検証で定める（規約 §6、TDD 不可分は生成物検証で代替）。
- E2/E3 は PDF 確認後に別 issue として段階的に起案。

---

## ユーザー確定事項（2026-06-19）

- **再現スコープ = A + B**（A: dpmm 単体で MST/AIM 合成デモ ／ B: 監査の縮小再現。完全再現 C と AIM/高次 E2 は当面スコープ外）。
- **成果物モード = モードB（論文型）主 + モードA（技術解説）従**。
- 目標は数値完全一致でなく**傾向再現**（μ_emp が μ=0.45 近傍 + 不安定な閾値基準で μ_emp が 0 に潰れる現象の再現）。

## 残課題（実行フェーズで確定）

- dpmm / riskcal の固定バージョン（`uv pip freeze` で確定）。
- E0 スモークによる縮小版 `N_ALL` の最終決定。
