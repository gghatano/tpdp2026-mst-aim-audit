#!/usr/bin/env bash
# 環境構築（冪等）。uv で Python 3.11 の仮想環境を作り、固定依存をインストールする。
# 上流監査コードは scripts/auditlib/ に同梱済み（別途 clone 不要）。
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv が見つかりません。https://docs.astral.sh/uv/ を参照してインストールしてください。" >&2
  exit 1
fi

# 仮想環境（既存ならスキップ）
if [ ! -d .venv ]; then
  uv venv --python 3.11 .venv
else
  echo "[setup] .venv は既存。スキップ。"
fi

# 固定依存をインストール
uv pip install --python .venv -r requirements.txt

# import スモーク
PYTHONPATH=scripts .venv/Scripts/python -c "from auditlib import MST, run_audit, mu_from_eps_delta; print('[setup] auditlib import OK')" \
  || PYTHONPATH=scripts .venv/bin/python -c "from auditlib import MST, run_audit, mu_from_eps_delta; print('[setup] auditlib import OK')"

echo "[setup] 完了。次に: bash scripts/run_all.sh"
