"""攻撃用の特徴量生成（distinguishing game の前半）。

上流 run_attack.py を移植し、(1) N_ALL を引数化、(2) 例外（worst-case データで稀に
生成が NaN 確率を出す）に対する再試行ガード、(3) 絶対パス出力、(4) 進捗・失敗・所要時間・
依存バージョンのメタ記録、を追加した。ロジック（worst-case 隣接データ・黒箱/白箱特徴）は不変。

注意: MST の DP ノイズは secure RNG（seed 不能）で生成されるため、特徴量生成は run 間で
ビット一致しない（DP として正しい挙動）。多数試行の集約 μ_emp は安定する。

使い方:
  PYTHONPATH=scripts python scripts/01_run_attack.py            # N_ALL_MAIN
  PYTHONPATH=scripts python scripts/01_run_attack.py --n-all 50 # スモーク
"""
import sys, os, time, json, string, pickle, argparse, platform
import numpy as np
import pandas as pd
from itertools import product
from multiprocessing import Pool, cpu_count

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import MST
import config as C

MAX_RETRIES = 5  # worst-case 生成での NaN 等に対する再試行回数


def featurize_df_queries(df, queries):
    features = np.zeros(len(queries))
    for i, query in enumerate(queries):
        features[i] = (df == query).all(axis=1).sum()
    return features.astype(int)


def featurize_model(model, columns):
    meas = model.measures
    measures = np.zeros(2 * len(columns))
    for col_idx, col in enumerate(columns):
        col_proj = sorted([m for m in meas if col in m[3]], key=lambda x: len(x[3]))
        proj = col_proj[0][3]
        _meas = col_proj[0][1]
        _meas = _meas.reshape(*[_meas.size // 2 ** (len(proj) - 1) for _ in proj])
        if len(col_proj[0][3]) > 1:
            axis = col_proj[0][3].index(col)
            _meas = np.sum(_meas, axis=tuple(i for i in range(len(_meas.shape)) if i != axis))
        measures[2 * col_idx:(2 * col_idx) + _meas.shape[0]] = _meas
    return measures


def _fit_one(df, columns, domain, queries):
    gen = MST(epsilon=C.EPSILON, delta=C.DELTA, domain=domain, compress=False, n_jobs=1)
    gen.fit(df)
    synth = gen.generate(C.LEN_SYNTH)
    return np.concatenate([featurize_df_queries(synth, queries), featurize_model(gen, columns)])


def one_iteration(args):
    i, df_out, df_in, columns, domain, queries = args
    retries = 0
    while True:
        try:
            out_feats = _fit_one(df_out, columns, domain, queries)
            in_feats = _fit_one(df_in, columns, domain, queries)
            return i, out_feats, in_feats, retries
        except Exception:
            retries += 1
            if retries > MAX_RETRIES:
                # 稀な恒常的失敗。NaN 行を返し、呼び出し側で除外する。
                nf = len(queries) + 2 * len(columns)
                return i, np.full(nf, np.nan), np.full(nf, np.nan), retries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-all", type=int, default=C.N_ALL_MAIN)
    ap.add_argument("--workers", type=int, default=max(1, cpu_count() - 2))
    args = ap.parse_args()

    N_ALL = args.n_all
    columns = list(string.ascii_uppercase[:C.N_COLS])
    domain = {col: 2 for col in columns}
    df_out = pd.DataFrame(np.zeros((C.N_ROWS, C.N_COLS), dtype=int), columns=columns)
    df_in = pd.DataFrame(
        np.vstack([np.ones((1, C.N_COLS), dtype=int), np.zeros((C.N_ROWS, C.N_COLS), dtype=int)]),
        columns=columns,
    )
    queries = np.array(list(product([0, 1], repeat=C.N_COLS)))
    nf = len(queries) + 2 * len(columns)
    data = {"out": np.zeros([N_ALL, nf]), "in": np.zeros([N_ALL, nf])}

    tasks = [(i, df_out, df_in, columns, domain, queries) for i in range(N_ALL)]
    n_cpu = max(1, min(args.workers, cpu_count() - 1))
    print(f"[attack] N_ALL={N_ALL} workers={n_cpu} eps={C.EPSILON} delta={C.DELTA} "
          f"len_synth={C.LEN_SYNTH} n_features={nf}", flush=True)

    t0 = time.time()
    total_retries = 0
    done = 0
    # maxtasksperchild を大きめにし、worker 再生成ごとの dpmm 再 import コスト（~10s）を償却する。
    # DP ノイズは secure RNG のため process 再利用の有無は独立性に影響しない。
    with Pool(processes=n_cpu, maxtasksperchild=25) as pool:
        for i, out_row, in_row, retries in pool.imap_unordered(one_iteration, tasks, chunksize=1):
            data["out"][i, :] = out_row
            data["in"][i, :] = in_row
            total_retries += retries
            done += 1
            if done % max(1, N_ALL // 20) == 0 or done == N_ALL:
                el = time.time() - t0
                print(f"[attack] {done}/{N_ALL}  elapsed={el:.0f}s  eta={el/done*(N_ALL-done):.0f}s  "
                      f"retries={total_retries}", flush=True)

    # NaN 行（恒常的失敗）を記録（除外は監査側で実施）
    n_nan = int(np.isnan(data["out"]).any(axis=1).sum() + np.isnan(data["in"]).any(axis=1).sum())
    elapsed = time.time() - t0

    out_path = C.features_path(N_ALL)
    with open(out_path, "wb") as fh:
        pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)

    meta = {
        "n_all": N_ALL, "workers": n_cpu, "epsilon": C.EPSILON, "delta": C.DELTA,
        "len_synth": C.LEN_SYNTH, "n_rows": C.N_ROWS, "n_cols": C.N_COLS,
        "n_features": nf, "elapsed_sec": round(elapsed, 1),
        "per_fit_sec": round(elapsed / (2 * N_ALL), 3),
        "total_retries": total_retries, "n_nan_rows": n_nan,
        "python": platform.python_version(),
    }
    with open(C.OUTPUTS / f"attack_meta_N{N_ALL}.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(f"[attack] saved {out_path.name}  elapsed={elapsed:.0f}s  retries={total_retries}  nan_rows={n_nan}")
    print(f"[attack] meta: {json.dumps(meta, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
