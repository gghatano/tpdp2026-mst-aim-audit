# 環境構築・再現手順

本ページは、本リポジトリの実験を**まっさらな環境から再現する**ための手順・動作環境・落とし穴をまとめる。
レポート本体は [content/REPORT.md](content/REPORT.md)、技術解説は `methods/` を参照。

## 動作環境（確認済み）

| 項目 | 値 |
|---|---|
| OS | Windows 11 Pro (10.0.26200) |
| Python | 3.11.15（uv が自動取得） |
| パッケージ管理 | [uv](https://docs.astral.sh/uv/) |
| 主要依存 | dpmm 0.1.9 / riskcal 1.5.1 / scikit-learn 1.5.0 / scipy 1.17.1 / numpy 1.26.4 |
| CPU | 20 コア（並列 18 workers で実行） |

依存は全て `requirements.txt` にバージョン固定済み。

## クイックスタート

```bash
# 1. 環境構築（uv で .venv を作成し、固定依存をインストール、import スモーク）
bash scripts/setup_env.sh

# 2. 一括実行（デモ → 攻撃特徴生成 → 監査 → 図表）
bash scripts/run_all.sh           # 主結果（N_ALL=2500、約40-50分）
bash scripts/run_all.sh 200       # 縮小スモーク（数分）

# 3. HTML レポートをビルド（htmls/ に出力）
PYTHONPATH=scripts .venv/Scripts/python scripts/build_html.py
```

## 個別実行

```bash
export PYTHONPATH=scripts PYTHONUTF8=1
PY=.venv/Scripts/python   # Linux/Mac は .venv/bin/python

# (A) dpmm の MST/AIM 合成デモ（監査とは独立。1-way/2-way TVD）
$PY scripts/00_demo_dpmm.py

# (B) 攻撃特徴生成（worst-case 隣接データで MST を多数学習）
$PY scripts/01_run_attack.py --n-all 2500 --workers 18

# 監査（FPR-FNR トレードオフ・μ_emp/μ_lower・収束・アブレーション）
$PY scripts/02_audit_eval.py --n-all 2500

# 図の生成
$PY scripts/03_plot.py
```

## 計算コストの目安

- MST 1 回の学習+生成 ≈ **9.2 秒**（n=10 行・3 列・ε=1）。`01_run_attack` は out/in 各 N_ALL 回 = 2×N_ALL 回。
- 18 workers 並列で **N_ALL=2500 → 約 40-50 分**、N_ALL=5000（論文の完全規模）→ 約 80-90 分。
- 監査（`02`）・図（`03`）は数十秒〜数分（特徴 pkl さえあれば軽量）。

事前に小さい `--n-all`（例 50-200）でスモークし、所要時間を外挿してから本実行することを推奨。

## Windows + uv の落とし穴（実際に踏んだもの）

1. **`multiprocessing` は spawn**: Windows は fork でなく spawn のため、各 worker が全モジュールを再 import する。
   `01_run_attack.py` は `if __name__ == "__main__"` ガード必須（実装済み）。`maxtasksperchild` を 1 にすると
   タスク毎に dpmm を再 import（約 10 秒）してしまうため、**25 に設定**して償却している。
2. **cp932 文字化け**: 日本語 Windows の既定エンコーディング対策として `PYTHONUTF8=1` を設定し、
   ファイル書き出しは全て `encoding="utf-8"` を明示。
3. **相対パスの罠**: 上流 `run_attack.py` は `../data/` に書く前提だったが、本移植では
   `config.py` で**絶対パス化**し cwd 非依存にした。
4. **理論フロンティアのオーバーフロー**: `riskcal.get_beta_from_zcdp` は α≈0 で `OverflowError`。
   `03_plot.py` はポイント毎評価で NaN マスクし、context 曲線は α∈[1e-3, 1-1e-3] に制限。

## 再現性に関する重要な注意（DP ノイズの非決定性）

MST の DP ガウスノイズは **secure RNG（seed 不能）** で生成される（実装を確認）。これは DP として
正しい挙動だが、その帰結として:

- **特徴量生成（`01`）は run 間でビット一致しない**。`numpy.random.seed` や `prng` 引数を渡しても
  個々の試行の数値は固定できない（検証済み）。
- ただし**多数試行にわたる集約 μ_emp は安定**する。本追試は「単一値の完全一致」ではなく
  **傾向の再現**（μ_emp が implied μ≈0.45 近傍に来る／不安定な閾値選択基準で μ_emp が 0 に潰れる）を目標とする。
- 一方、**監査ステップ（`02`）は features.pkl を固定すれば再現可能**（分類器・分割の乱数は `AUDIT_SEED=13` で固定）。

## GitHub Pages 公開

1. `.github/workflows/deploy-pages.yml` が `htmls/` を配信する。
2. GitHub の **Settings → Pages → Build and deployment → Source** を **「GitHub Actions」** に設定（初回のみ手動）。
   - CLI でも可: `gh api --method POST repos/gghatano/tpdp2026-mst-aim-audit/pages -f build_type=workflow`
   - ⚠️ この設定を忘れると **Actions は緑（success）のままなのにサイトは 404** になる。ワークフローの `Check Pages is enabled` step が未設定を検知して fail させるので、その場合はこの手順を実施すること。判定: `gh api repos/gghatano/tpdp2026-mst-aim-audit/pages` が 404 なら未有効。
3. `main` へ push すると Actions が走り、`https://gghatano.github.io/tpdp2026-mst-aim-audit/` で公開される。

ローカル確認: `python -m http.server 8099 --directory htmls`。
