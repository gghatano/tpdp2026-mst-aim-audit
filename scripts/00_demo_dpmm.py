"""モードA デモ: dpmm の MST / AIM で DP 合成データを生成し、分布忠実度を測る。

監査（01/02）とは独立の「使い方＋有用性」デモ。再現性のため、相関のある
カテゴリカルデータを決定的に生成して "real" とし、ε を振って 1-way / 2-way の
Total Variation Distance (TVD) を測る。図中ラベルは英語。

注意: dpmm の DP ノイズは secure RNG のため run 間でビット一致しないが、傾向（ε 増→TVD 減）は安定。

使い方: PYTHONPATH=scripts python scripts/00_demo_dpmm.py
"""
import sys, os, json, itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from dpmm.models import MSTGM, AIMGM

plt.rcParams.update({"figure.dpi": 130, "font.size": 11})
EPSILONS = [0.5, 1.0, 2.0, 4.0]
DELTA = 1e-5
N = 2000
SEED = 0


def make_real_data(n=N, seed=SEED):
    """相関のあるカテゴリカルデータを決定的に生成（age_grp, edu, income, region, marital）。"""
    rng = np.random.default_rng(seed)
    age = rng.integers(0, 4, n)                         # 0..3
    # edu は age に相関
    edu = np.clip((age + rng.integers(0, 3, n)) // 1, 0, 4) % 5
    # income は edu に相関
    income = (edu + rng.integers(0, 2, n) >= 3).astype(int)  # 0/1
    region = rng.integers(0, 3, n)
    marital = ((age >= 2).astype(int) ^ (rng.random(n) < 0.2).astype(int))
    return pd.DataFrame({"age": age, "edu": edu, "income": income,
                         "region": region, "marital": marital})


def tvd_1way(real, synth):
    vals = []
    for c in real.columns:
        cats = sorted(set(real[c]) | set(synth[c]))
        pr = real[c].value_counts(normalize=True).reindex(cats, fill_value=0).values
        ps = synth[c].value_counts(normalize=True).reindex(cats, fill_value=0).values
        vals.append(0.5 * np.abs(pr - ps).sum())
    return float(np.mean(vals))


def tvd_2way(real, synth):
    vals = []
    for a, b in itertools.combinations(real.columns, 2):
        pr = real.groupby([a, b]).size() / len(real)
        ps = synth.groupby([a, b]).size() / len(synth)
        idx = pr.index.union(ps.index)
        pr = pr.reindex(idx, fill_value=0).values
        ps = ps.reindex(idx, fill_value=0).values
        vals.append(0.5 * np.abs(pr - ps).sum())
    return float(np.mean(vals))


def fit_gen(model_cls, eps, real, **kw):
    dom = {c: int(real[c].max()) + 1 for c in real.columns}
    m = model_cls(epsilon=eps, delta=DELTA, domain=dom, compress=False, n_jobs=1, **kw)
    m.fit(real)
    return m.generate(len(real))


def main():
    real = make_real_data()
    print(f"[demo] real data: {real.shape}, domains={ {c:int(real[c].max())+1 for c in real.columns} }")
    results = {"epsilons": EPSILONS, "delta": DELTA, "n": N, "MST": [], "AIM": []}
    for eps in EPSILONS:
        s_mst = fit_gen(MSTGM, eps, real)
        s_aim = fit_gen(AIMGM, eps, real)
        results["MST"].append({"eps": eps, "tvd1": tvd_1way(real, s_mst), "tvd2": tvd_2way(real, s_mst)})
        results["AIM"].append({"eps": eps, "tvd1": tvd_1way(real, s_aim), "tvd2": tvd_2way(real, s_aim)})
        print(f"[demo] eps={eps}: MST tvd1={results['MST'][-1]['tvd1']:.3f} tvd2={results['MST'][-1]['tvd2']:.3f}"
              f" | AIM tvd1={results['AIM'][-1]['tvd1']:.3f} tvd2={results['AIM'][-1]['tvd2']:.3f}")

    with open(C.OUTPUTS / "demo_metrics.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, key, title in zip(axes, ["tvd1", "tvd2"], ["1-way TVD", "2-way TVD"]):
        ax.plot(EPSILONS, [r[key] for r in results["MST"]], "o-", label="MST", lw=2)
        ax.plot(EPSILONS, [r[key] for r in results["AIM"]], "s-", label="AIM", lw=2)
        ax.set_xlabel(r"Privacy budget $\epsilon$"); ax.set_ylabel(f"{title} (lower=better)")
        ax.set_title(f"{title} vs $\\epsilon$"); ax.legend(); ax.grid(alpha=0.15)
    plt.tight_layout(); fig.savefig(C.FIGURES / "demo_fidelity.png"); plt.close(fig)
    print("[demo] wrote figures/demo_fidelity.png and outputs/demo_metrics.json")


if __name__ == "__main__":
    main()
