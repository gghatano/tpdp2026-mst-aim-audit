#!/usr/bin/env bash
# 一括実行: デモ(A) → 攻撃特徴生成(B) → 監査 → 図表。
# N_ALL は引数で上書き可（既定は config.py の N_ALL_MAIN=2500、約40-65分）。
#   bash scripts/run_all.sh           # 主結果
#   bash scripts/run_all.sh 200        # 縮小スモーク
set -euo pipefail
cd "$(dirname "$0")/.."

PY=".venv/Scripts/python"
[ -x "$PY" ] || PY=".venv/bin/python"
export PYTHONPATH=scripts
export PYTHONUTF8=1   # Windows cp932 回避

N_ALL="${1:-}"

echo "[run_all] (A) dpmm 合成デモ"
"$PY" scripts/00_demo_dpmm.py

echo "[run_all] (B) 攻撃特徴生成"
if [ -n "$N_ALL" ]; then
  "$PY" scripts/01_run_attack.py --n-all "$N_ALL"
  echo "[run_all] 監査・図表 (N_ALL=$N_ALL)"
  "$PY" scripts/02_audit_eval.py --n-all "$N_ALL"
else
  "$PY" scripts/01_run_attack.py
  echo "[run_all] 監査・図表 (N_ALL_MAIN)"
  "$PY" scripts/02_audit_eval.py
fi

"$PY" scripts/03_plot.py
echo "[run_all] 完了。図: figures/  メトリクス: outputs/metrics.json"
echo "[run_all] HTML: $PY scripts/build_html.py"
