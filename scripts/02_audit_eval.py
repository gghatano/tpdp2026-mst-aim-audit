"""監査・推定（distinguishing game の後半）。

features_N{N}.pkl を読み、(1) 主結果（Default 構成）、(2) μ_emp の収束（実効サイズ別）、
(3) アブレーション（1 要素ずつ変更）を計算して outputs/metrics.json に保存する。
プロット用に Default 構成の validation 曲線（FPR/FNR/threshold/advantage）も保存する。

使い方:
  PYTHONPATH=scripts python scripts/02_audit_eval.py             # N_ALL_MAIN を使用
  PYTHONPATH=scripts python scripts/02_audit_eval.py --n-all 50  # スモーク
"""
import sys, os, json, pickle, argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import run_audit, mu_from_eps_delta
from dpmm.models.base.mechanisms import cdp_rho
import config as C

N_QUERIES = 2 ** C.N_COLS  # 黒箱特徴の数（先頭 N_QUERIES 列）


def _clean(data):
    """NaN 行（恒常的に生成失敗した試行）を out/in 双方から落とす。"""
    mask = ~(np.isnan(data["out"]).any(axis=1) | np.isnan(data["in"]).any(axis=1))
    return {"out": data["out"][mask], "in": data["in"][mask]}, int((~mask).sum())


def _audit(out, in_, split, **over):
    cfg = dict(C.DEFAULT_AUDIT)
    cfg.update(over)
    return run_audit(out, in_, n_train=split["n_train"], n_valid=split["n_valid"],
                     n_test=split["n_test"], random_state=C.AUDIT_SEED, **cfg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-all", type=int, default=C.N_ALL_MAIN)
    args = ap.parse_args()

    path = C.features_path(args.n_all)
    with open(path, "rb") as fh:
        raw = pickle.load(fh)
    data, n_dropped = _clean(raw)
    avail = min(len(data["out"]), len(data["in"]))
    print(f"[audit] loaded {path.name}: available={avail} (dropped {n_dropped} NaN rows)")

    # --- 理論 μ（2 経路） ---
    rho = float(cdp_rho(C.EPSILON, C.DELTA))
    implied_mu = float(np.sqrt(2 * rho))          # (eps,delta)->rho-zCDP->mu（MST/AIM の内部経路）
    theory_mu = float(mu_from_eps_delta(C.EPSILON, C.DELTA))  # (eps,delta)->mu 直接変換
    print(f"[audit] implied_mu(via zCDP)={implied_mu:.4f}  theory_mu(direct)={theory_mu:.4f}")

    metrics = {
        "n_all": args.n_all, "available": avail, "n_dropped": n_dropped,
        "epsilon": C.EPSILON, "delta": C.DELTA, "rho": rho,
        "implied_mu": implied_mu, "theory_mu": theory_mu,
        "audit_seed": C.AUDIT_SEED, "default_config": C.DEFAULT_AUDIT,
    }

    # --- 主結果（Default 構成、最大の実効サイズ） ---
    main_split = C.SPLIT_MAIN
    res = _audit(data["out"], data["in"], main_split)
    pt = res["test"]["point"]
    metrics["main"] = {
        "split": main_split,
        "mu_emp": pt["mu_lower"], "mu_hat": pt["mu_hat"],
        "FPR": pt["FPR"], "FNR": pt["FNR"], "advantage": pt["advantage"],
        "auc_test": res["test"]["auc"], "auc_valid": res["valid"]["auc"],
        "opt_threshold": res["valid"]["curve"]["opt_t"],
    }
    print(f"[audit] MAIN: mu_emp={pt['mu_lower']:.4f}  mu_hat={pt['mu_hat']:.4f}  "
          f"AUC_test={res['test']['auc']:.3f}  (implied mu={implied_mu:.3f})")

    # validation 曲線（プロット用）
    cv = res["valid"]["curve"]
    metrics["valid_curve"] = {k: np.asarray(cv[k]).tolist()
                              for k in ["thresholds", "FPR", "FNR", "advantage", "mu_hat", "mu_lower"]}
    metrics["valid_curve"]["opt_t"] = float(cv["opt_t"])

    # --- 収束（実効サイズ別） ---
    conv = []
    for s in C.CONVERGENCE_SIZES:
        if s["size"] > avail:
            continue
        r = _audit(data["out"], data["in"], s)
        p = r["test"]["point"]
        conv.append({"size": s["size"], "mu_emp": p["mu_lower"], "mu_hat": p["mu_hat"],
                     "auc_test": r["test"]["auc"]})
        print(f"[audit] conv size={s['size']:>4}: mu_emp={p['mu_lower']:.4f} mu_hat={p['mu_hat']:.4f} "
              f"AUC={r['test']['auc']:.3f}")
    metrics["convergence"] = conv

    # --- アブレーション（Default から 1 要素ずつ変更、最大サイズ） ---
    abl = {}
    abl["default"] = metrics["main"]["mu_emp"]
    for sel in ["max_mu_hat", "max_mu_lower"]:
        abl[f"thr={sel}"] = _audit(data["out"], data["in"], main_split,
                                   threshold_selection=sel)["test"]["point"]["mu_lower"]
    abl["ci=bonferroni_cp"] = _audit(data["out"], data["in"], main_split,
                                     ci_method="bonferroni_cp")["test"]["point"]["mu_lower"]
    abl["clf=random_forest"] = _audit(data["out"], data["in"], main_split,
                                      classifier="random_forest")["test"]["point"]["mu_lower"]
    # 黒箱のみ（白箱 marginal 特徴を落とす）
    bb_out, bb_in = data["out"][:, :N_QUERIES], data["in"][:, :N_QUERIES]
    abl["threat=black_box_only"] = _audit(bb_out, bb_in, main_split)["test"]["point"]["mu_lower"]
    metrics["ablation"] = {k: float(v) for k, v in abl.items()}
    print(f"[audit] ablation: {json.dumps(metrics['ablation'], ensure_ascii=False)}")

    out = C.OUTPUTS / "metrics.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=2)
    print(f"[audit] wrote {out}")


if __name__ == "__main__":
    main()
