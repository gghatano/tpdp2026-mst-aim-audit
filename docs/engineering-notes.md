# エンジニアリングノート（実装・再現で踏んだ点）

実装中に判明した一次情報。レポートの「実運用の落とし穴」「再現性」節の根拠。

## 上流コードの移植

- 上流 `sassoftware/dpmm` の **`audit-dpmm` ブランチ** `experimental/audit_dpmm/code/` を `scripts/auditlib/` に移植。
- 変更は**パッケージ化に伴う相対 import 化のみ**（`from mst import ...` → `from .adp2gdp import ...`）。
  監査ロジック（worst-case 隣接データ・黒箱/白箱特徴・joint-beta による μ 下界）は未改変。
- `auditlib/mst.py` は dpmm 本体の MST を 1-way marginal のみに制限したラッパ（`dpmm.models.base.*` に依存）。

## DP ノイズの非決定性（再現性の核心）

- MST のガウスノイズは **secure RNG（seed 不能）** で生成される。検証: `numpy.random.seed(s)` を固定しても、
  また MST に `prng=RandomState(s)` を渡しても、同一 seed で marginal 測定値が**一致しない**ことを確認。
- これは DP として正しい（ノイズが予測可能だと保証が崩れる）。帰結として特徴生成（`01`）は run 間でビット非再現。
- **集約 μ_emp は安定**するため、目標は「単一値の完全一致」でなく**傾向の再現**に置く。
- 監査ステップ（`02`）は features.pkl 固定 + `AUDIT_SEED=13` で再現可能。

## 計算コストと並列化

- MST 1 fit+generate ≈ **9.2 秒**（warmup 後、安定。初回は JIT で ~10s 上乗せ）。20 コア環境で 18 workers 並列。
- `multiprocessing.Pool(maxtasksperchild=1)`（上流既定）は Windows spawn で**タスク毎に dpmm を再 import（~10s）**し
  大幅に遅くなる。`maxtasksperchild=25` に変更して償却（独立性は secure RNG ゆえ影響なし）。
- N_ALL=60 スモーク（18 workers, maxtasksperchild=1）= 159s。N_ALL=2500 は約 40-50 分の見込み。

## worst-case 生成の稀な失敗

- 全 0 の worst-case データ + ノイズで、稀に MST 生成が `ValueError: probabilities contain NaN`
  （周辺が負→正規化で NaN）を出す。`01_run_attack.py` に**最大 5 回の再試行ガード**を実装し、
  恒常的失敗は NaN 行として記録 → 監査側（`02`）で除外。スモークでは失敗 0 件。

## Windows / uv

- `PYTHONUTF8=1` + 全書き出し `encoding="utf-8"` で cp932 文字化けを回避。
- 上流の相対パス `../data/` 書き出しを `config.py` で絶対パス化（cwd 非依存）。
- `riskcal.get_beta_from_zcdp` は α≈0 で `OverflowError` → `03_plot.py` でポイント毎 NaN マスク。

## 上流コードとの差分（数値完全一致を狙わない理由）

| 項目 | 上流コード | 論文本文 | 本追試 |
|---|---|---|---|
| 分類器 | `GradientBoostingClassifier` | XGBoost | 上流に従い GradientBoosting |
| 合成データ件数 | `LEN_SYNTH=25` | 50 | 上流に従い 25 |
| 試行数 N_ALL | 5000/side | 5000/side | 2500/side（縮小）+ 収束図 |
| Dout 行数 | 10 | 10 | 10 |
