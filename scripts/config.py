"""共通設定。上流 run_attack.py / run_audit.ipynb の既定値に準拠し、縮小再現のための
パラメータ（N_ALL・分割）を一元管理する。"""
from pathlib import Path

# --- パス（絶対パス化。cwd 非依存・Windows 安全） ---
ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
FIGURES = ROOT / "figures"
DATA = ROOT / "data"
for _d in (OUTPUTS, FIGURES, DATA):
    _d.mkdir(exist_ok=True)

# --- 監査対象データ／プライバシー（上流 run_attack.py と同一） ---
N_ROWS = 10          # Dout の同一レコード数
N_COLS = 3           # 列数（ドメイン {0,1}）
LEN_SYNTH = 25       # 各モデルが出す合成データ件数（上流コード既定。論文本文は 50）
EPSILON = 1.0
DELTA = 1e-2

# --- 縮小再現の規模 ---
# 上流（論文）は N_ALL=5000/side（train2000/valid1000/test2000）。
# 本追試はまず N_ALL_MAIN を主結果とし、より小さい実効サイズで収束を見る。
N_ALL_MAIN = 2500    # 1 side あたりの独立試行数（out/in 各 N_ALL_MAIN）

# 主結果の分割（train+valid+test == N_ALL_MAIN）
SPLIT_MAIN = dict(n_train=1000, n_valid=500, n_test=1000)

# μ_emp の収束を見る実効サイズ（features は N_ALL_MAIN を 1 回生成し、各サイズで切り出す）
# 各要素は train+valid+test == size。比率は主結果と同じ 2:1:2。
CONVERGENCE_SIZES = [
    dict(size=250,  n_train=100,  n_valid=50,  n_test=100),
    dict(size=500,  n_train=200,  n_valid=100, n_test=200),
    dict(size=1000, n_train=400,  n_valid=200, n_test=400),
    dict(size=2500, n_train=1000, n_valid=500, n_test=1000),
]

# --- 監査の既定（上流 run_audit.py 既定 + 論文 "Default" 構成） ---
AUDIT_SEED = 13            # 攻撃分類器・評価の乱数（features 固定なら再現可能）
DEFAULT_AUDIT = dict(
    classifier="xgboost",            # 実体は GradientBoostingClassifier（上流命名）
    threshold_mode="quantiles",
    n_thresholds=80,                 # 上流既定 200 から削減（joint_beta 積分が重いため）。曲線解像度は十分。
    threshold_selection="max_advantage",
    ci_method="joint_beta",
    alpha=0.1,
)

def features_path(n_all: int) -> Path:
    return OUTPUTS / f"features_N{n_all}.pkl"

def n_features() -> int:
    # black-box: 2^N_COLS クエリ + white-box: 2*N_COLS marginal counts
    return (2 ** N_COLS) + 2 * N_COLS
