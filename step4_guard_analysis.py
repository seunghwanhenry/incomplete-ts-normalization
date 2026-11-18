"""
step4_guard_analysis.py - post hoc development analysis of Step 4 (exploratory; written after REPORT_step4.md).

Reads step4_outputs/pack/*.npz and evaluates, in addition to the pre-listed variants, window-level guards: a test
window uses seq only if any variable has a visible mean (location, "m") or a visible mean or log standard deviation
("ms") outside the range of the masked training windows by more than kappa range widths. Writes
step4_outputs/step4_guard_analysis.csv and prints the summary that led to the frozen Step 5 method
(comb_var + window guard "ms", kappa = 1).
Usage: python step4_guard_analysis.py [pack_dir]
"""
import sys, importlib.util, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("s4", os.path.join(HERE, "step4_dual.py")); s4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s4)
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(s4.OUT, "pack")
KAPS = [0, 0.1, 0.25, 0.5, 1, 2, 5, 10, np.inf]
FLOOR = 1e-6          # range floor: constant variables and float32 storage of the window statistics

rows, grow = [], []
for ds in s4.DATASETS:
    for mech, lv in s4.CONDITIONS:
        A = np.load(os.path.join(P, f"{ds}_{mech}_{lv:g}.npz")); cond = f"{mech} {lv:g}"
        for seed in s4.SEEDS:
            k = f"{seed}|"
            y, n, d = A[k + "y_te"].astype(float), A[k + "n_te"], A[k + "d_te"]; D = len(A[k + "m_lo"])
            mlo, mhi, llo, lhi = A[k + "m_lo"], A[k + "m_hi"], A[k + "l_lo"], A[k + "l_hi"]
            mt, lt, ok = A[k + "m_te"], A[k + "l_te"], A[k + "c_te"] >= 2
            exm = np.maximum(mlo - mt, mt - mhi) / np.maximum(mhi - mlo, FLOOR)
            exl = np.maximum(llo - lt, lt - lhi) / np.maximum(lhi - llo, FLOOR)
            ex = {"ms": np.where(ok, np.maximum(exm, exl), -np.inf).max(1), "m": np.where(ok, exm, -np.inf).max(1)}
            for kap in KAPS:
                grow.append(dict(dataset=ds, cond=cond, seed=seed, kappa=kap, share_ms=float((ex["ms"] > kap).mean()), share_m=float((ex["m"] > kap).mean())))
            for mdl in s4.MODELS:
                g, s_ = A[f"{k}{mdl}|global|te"].astype(float), A[f"{k}{mdl}|seq|te"].astype(float)
                W = s4.weights(A[k + "y_st"].astype(float), A[f"{k}{mdl}|global|st"].astype(float), A[f"{k}{mdl}|seq|st"].astype(float), A[k + "d_st"], D)
                for name, p in (("seq", s_), ("global", g)):
                    rows.append(dict(dataset=ds, cond=cond, seed=seed, model=mdl, variant=name, guard="-", kappa=np.nan, rmse=float(np.sqrt(((p - y) ** 2).mean()))))
                for name in ("sel_var", "comb_var"):
                    a = W[name][d]
                    for gk, e in ex.items():
                        for kap in KAPS:
                            ag = np.where(e[n] > kap, 0.0, a); p = ag * g + (1 - ag) * s_
                            rows.append(dict(dataset=ds, cond=cond, seed=seed, model=mdl, variant=name, guard=gk, kappa=kap, rmse=float(np.sqrt(((p - y) ** 2).mean()))))
r = pd.DataFrame(rows); r.to_csv(os.path.join(s4.OUT, "step4_guard_analysis.csv"), index=False)
base = r[r.guard == "-"].groupby(["dataset", "cond", "model", "variant"]).rmse.mean().unstack()
orc = base.min(axis=1)
v = r[r.guard != "-"].groupby(["dataset", "cond", "model", "variant", "guard", "kappa"]).rmse.mean()
ratio = v / orc.reindex(v.index.droplevel([3, 4, 5])).values
summ = ratio.groupby(level=[3, 4, 5]).agg(cells_within=lambda x: int((x <= s4.WITHIN).sum()), worst="max",
                                         gmean=lambda x: float(np.exp(np.log(x).mean())))
print("variant x guard x kappa (kappa = inf: no guard): cells within 2% of the oracle (of 48), worst ratio, geometric mean")
print(summ.round(3).to_string())
g = pd.DataFrame(grow)
print("\nshare of test windows guarded (ms):")
print(g.groupby(["dataset", "kappa"]).share_ms.mean().unstack().round(3).to_string())
fin = ratio.xs(("comb_var", "ms", 1.0), level=[3, 4, 5])
print("\nfrozen method comb_var + guard ms, kappa = 1: per-cell ratio to the oracle")
print(fin.round(3).to_string())
