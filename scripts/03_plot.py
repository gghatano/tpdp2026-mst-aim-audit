"""metrics.json から図を生成（figures/）。図中ラベルは英語に統一（フォント文字化け回避）。

生成物:
  figures/tradeoff.png        … 経験的 FPR-FNR 曲線 vs 理論フロンティア（論文 Fig.1 相当）
  figures/valid_threshold.png … 閾値ごとの FPR/FNR/advantage と選択閾値（論文 Fig.2 相当）
  figures/convergence.png     … μ_emp の実効サイズ依存（本追試の独自図）
  figures/ablation.png        … 監査設定のアブレーション（論文 Fig.3 相当）
"""
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from riskcal.analysis import get_beta_from_adp, get_beta_from_zcdp, get_beta_from_gdp

plt.rcParams.update({"figure.dpi": 130, "font.size": 11})


def load():
    with open(C.OUTPUTS / "metrics.json", encoding="utf-8") as fh:
        return json.load(fh)


def _safe_curve(fn, a):
    """理論フロンティアをポイント毎に評価し、オーバーフロー等は NaN にして描画から除外。"""
    out = np.full_like(a, np.nan, dtype=float)
    for i, x in enumerate(a):
        try:
            out[i] = float(fn(x))
        except (OverflowError, ValueError, ZeroDivisionError):
            out[i] = np.nan
    return out


def fig_tradeoff(m):
    cv = m["valid_curve"]
    fpr, fnr = np.array(cv["FPR"]), np.array(cv["FNR"])
    a = np.linspace(1e-6, 1 - 1e-6, 400)
    ac = np.linspace(1e-3, 1 - 1e-3, 400)  # context 曲線用（端点でのオーバーフロー回避）
    fig = plt.figure(figsize=(6, 6))
    plt.gca().set_aspect("equal", "box")
    plt.plot(fpr, fnr, color="black", lw=3, label="Empirical audit")
    plt.plot(a, _safe_curve(lambda x: get_beta_from_gdp(m["implied_mu"], x), a), color="red", lw=2.5,
             label=r"$\mu$-GDP (via $\rho$-zCDP), $\mu$=%.2f" % m["implied_mu"])
    plt.plot(a, _safe_curve(lambda x: get_beta_from_gdp(m["theory_mu"], x), a), color="red", ls="--", lw=2,
             label=r"$\mu$-GDP (via $(\epsilon,\delta)$), $\mu$=%.2f" % m["theory_mu"])
    plt.plot(ac, _safe_curve(lambda x: get_beta_from_zcdp(m["rho"], x), ac), color="royalblue", ls="-.", lw=1.8, alpha=.7,
             label=r"$\rho$-zCDP (context)")
    plt.plot(ac, _safe_curve(lambda x: get_beta_from_adp(m["epsilon"], m["delta"], x), ac), color="gray", ls=":", lw=1.8, alpha=.7,
             label=r"$(\epsilon,\delta)$-DP (context)")
    plt.plot(a, 1 - a, color="gray", ls="--", lw=1.5, alpha=.5, label="Random guess")
    plt.xlabel(r"FPR ($\alpha$)"); plt.ylabel(r"FNR ($\beta$)")
    plt.xlim(0, 1); plt.ylim(0, 1); plt.legend(loc="upper right", fontsize=9)
    plt.grid(alpha=0.12); plt.tight_layout()
    fig.savefig(C.FIGURES / "tradeoff.png"); plt.close(fig)


def fig_valid_threshold(m):
    cv = m["valid_curve"]
    t = np.array(cv["thresholds"]); fpr = np.array(cv["FPR"]); fnr = np.array(cv["FNR"])
    adv = np.array(cv["advantage"]); opt = cv["opt_t"]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(t, fpr, color="tab:blue", lw=2, alpha=.7, label=r"FPR ($\alpha$)")
    ax.plot(t, fnr, color="tab:orange", lw=2, alpha=.7, label=r"FNR ($\beta$)")
    ax.plot(t, adv, color="darkgreen", lw=3, label="Empirical advantage (TPR-FPR)")
    ax.axvline(opt, color="black", ls="--", lw=1.5, label=r"Selected $\tau^*$=%.3f" % opt)
    ax.set_xlabel("Decision threshold"); ax.set_ylabel("Rate")
    ax.set_xlim(0, 1); ax.legend(fontsize=9); ax.grid(alpha=0.15)
    plt.tight_layout(); fig.savefig(C.FIGURES / "valid_threshold.png"); plt.close(fig)


def fig_convergence(m):
    conv = m.get("convergence", [])
    if not conv:
        return
    sizes = [c["size"] for c in conv]
    mu_emp = [c["mu_emp"] for c in conv]
    mu_hat = [c["mu_hat"] for c in conv]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(sizes, mu_emp, "o-", color="black", lw=2, label=r"$\mu_{emp}$ (lower bound)")
    ax.plot(sizes, mu_hat, "s--", color="gray", lw=1.5, alpha=.8, label=r"$\hat{\mu}$ (point est.)")
    ax.axhline(m["implied_mu"], color="red", lw=2, label=r"Implied $\mu$=%.2f" % m["implied_mu"])
    ax.set_xscale("log"); ax.set_xlabel("Effective audit size per class (N)")
    ax.set_ylabel(r"$\mu$"); ax.legend(fontsize=10); ax.grid(alpha=0.15)
    ax.set_title("Empirical privacy vs audit size")
    plt.tight_layout(); fig.savefig(C.FIGURES / "convergence.png"); plt.close(fig)


def fig_ablation(m):
    abl = m.get("ablation", {})
    if not abl:
        return
    keys = list(abl.keys()); vals = [abl[k] for k in keys]
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["tab:green" if k == "default" else "tab:blue" for k in keys]
    ax.bar(range(len(keys)), vals, color=colors, alpha=.85)
    ax.axhline(m["implied_mu"], color="red", lw=2, label=r"Implied $\mu$=%.2f" % m["implied_mu"])
    ax.set_xticks(range(len(keys))); ax.set_xticklabels(keys, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel(r"$\mu_{emp}$ (test)"); ax.legend(); ax.grid(alpha=0.15, axis="y")
    ax.set_title("Ablation of audit choices")
    plt.tight_layout(); fig.savefig(C.FIGURES / "ablation.png"); plt.close(fig)


def main():
    m = load()
    fig_tradeoff(m); fig_valid_threshold(m); fig_convergence(m); fig_ablation(m)
    print("[plot] wrote figures:", *[p.name for p in sorted(C.FIGURES.glob('*.png'))])


if __name__ == "__main__":
    main()
