"""
step4_dual.py - Step 4 (development): dual normalization with a validation-estimated mixing weight and an
out-of-range guard.

Step 3 showed that neither global nor per-sequence (seq) normalization is uniformly better and that the
reliability-weighted shrinkage of Step 2b does not choose between them. Step 4 trains every model with both
normalizations, imputes the held-out early-stopping windows as well as the test windows, and compares ways of
combining the two imputations. All four datasets used so far are development data from now on
(Siemens, ECG200, Motor, Hydraulic); the chosen variant is frozen and tested in Step 5 on new datasets.

Commands:
  python step4_dual.py plan            # writes step4_outputs/PLAN_step4.md (development plan, commit it)
  python step4_dual.py run [--worker k --n-workers K]
  python step4_dual.py status
  python step4_dual.py pack            # collects truth, predictions and guard statistics per dataset and condition
  python step4_dual.py report          # analysis of the combination variants (needs pack)
Motor and Hydraulic use the windows cached by Step 3 (step3_outputs/cache) and Step 3's splits, masks and model
seeds, so their test imputations reproduce Step 3 (checked in the report).
"""
import argparse, glob, hashlib, json, os, platform, sys, time, traceback
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import numpy as np
import pandas as pd

OUT = "step4_outputs"
STEP3 = "step3_outputs"
EPS = 1e-5
SEEDS = list(range(5))
DATASETS = ["Siemens", "ECG200", "Motor", "Hydraulic"]
CONDITIONS = [("MCAR", 0.3), ("MCAR", 0.7), ("MNAR", 0.3), ("GAP", 0.4)]
GAP_L = {"Siemens": 30, "ECG200": 16, "Motor": 36, "Hydraulic": 12}
GAP_FRAC = 0.4
MODELS = ["KNN", "SAITS", "Transformer"]
NORMS = ["global", "seq"]
TRANSFORMER = dict(revin=False, mask_input=True, mask_mode="mix")
MOTOR_TEST, MOTOR_STOP = 5, 2
HYD_BLOCK, HYD_TEST, HYD_STOP = 25, 0.3, 0.1
WITHIN = 1.02
VARIANTS = ["seq", "global", "sel_pool", "sel_var", "comb_pool", "comb_var",
            "sel_pool+guard", "sel_var+guard", "comb_pool+guard", "comb_var+guard"]


def script_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def sseed(*keys):
    return int(hashlib.sha256("|".join(map(str, keys)).encode()).hexdigest()[:8], 16)


PLAN = """# Step 4 - development of dual normalization (exploratory)

Script step4_dual.py, SHA-256 {sha}. Written before any Step 4 result.

## Status of the data
Siemens, ECG200, Motor and Hydraulic are development data from now on. Motor and Hydraulic results of Step 3 are
known. Nothing in Step 4 is confirmatory; the variant chosen here is frozen and tested in Step 5 on datasets that
have not been opened (NASA C-MAPSS, MetroPT-3).

## Runs
* Seeds 0-4; conditions MCAR 30%, MCAR 70%, MNAR 30%, consecutive gaps (40% of each variable; gap length Siemens 30,
  ECG200 16, Motor 36, Hydraulic 12 points).
* Models KNN (k = 5), SAITS (development configuration), DTIN transformer (internal normalization off), each with
  global and seq normalization and the same model seed for both; linear regression on time as a reference.
* Every run imputes the masked early-stopping windows (validation) and the masked test windows. The validation
  masks are the training masks of those windows.
* Motor and Hydraulic: Step 3 splits, masks and model seeds (the test imputations should reproduce Step 3).
  Siemens and ECG200: the development split used in Steps 2-2b; new masks.

## Combination variants (all use only the validation windows and the masked inputs)
* sel_pool: the normalization with the lower validation MSE.
* sel_var: per variable, the normalization with the lower validation MSE.
* comb_pool / comb_var: convex combination a*global + (1-a)*seq with the weight that minimizes the validation MSE,
  a = clip((Es - C) / (Eg + Es - 2C), 0, 1), Eg, Es the validation MSEs and C the mean product of the two errors
  (pooled, or per variable).
* +guard: for a test window and variable whose visible mean or log standard deviation lies outside the range of the
  masked training windows, seq only (a = 0).

## Choice of the variant (fixed now)
Cells = dataset x condition x model = 48; oracle = min(mean RMSE global, mean RMSE seq) over seeds.
1. Highest number of cells with mean RMSE <= {w} x oracle.
2. Ties (within one cell): lower worst-case ratio to the oracle.
3. Remaining ties: the simpler variant (pool before var, sel before comb, no guard before guard).
Also reported: per-seed ratios, ratios per test unit (median over units), guard activation rates, linear regression.
"""


# ------------------------------------------------------------------------------------------- frozen helpers
def seq_stats(X_nan):
    v = ~np.isnan(X_nan); c = v.sum(1, keepdims=True).astype(float); x = np.nan_to_num(X_nan)
    m = (x * v).sum(1, keepdims=True) / np.maximum(c, 1)
    s = np.sqrt((((x - m) * v) ** 2).sum(1, keepdims=True) / np.maximum(c, 1) + EPS)
    return np.where(c > 0, m, 0.0), np.where(c > 1, s, 1.0)


def vis_stats(X_nan):
    """visible mean and log standard deviation per window and variable; count of visible values"""
    v = ~np.isnan(X_nan); c = v.sum(1).astype(float); x = np.nan_to_num(X_nan)
    m = (x * v).sum(1) / np.maximum(c, 1)
    var = (((x - m[:, None, :]) * v) ** 2).sum(1) / np.maximum(c, 1)
    return m, 0.5 * np.log(var + EPS), c


def strict_mode(strict=True):
    import torch
    torch.use_deterministic_algorithms(True, warn_only=not strict)
    torch.backends.cudnn.benchmark = False; torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    for f, val in (("enable_flash_sdp", False), ("enable_mem_efficient_sdp", False), ("enable_math_sdp", True)):
        if hasattr(torch.backends.cuda, f): getattr(torch.backends.cuda, f)(val)


def modules():
    import dtin_core as dc
    dc.init(os.path.join("dtin_outputs", "config.json"))
    import dtin_improve as di, dtin_v2 as v2, dtin_v2_eval as ev
    return dc, di, v2, ev


# ------------------------------------------------------------------------------------------- data
_CACHE = {}


def step3_cache(ds):
    p, q = os.path.join(STEP3, "cache", f"{ds}.npz"), os.path.join(STEP3, "cache", f"{ds}_windows.csv")
    if not os.path.exists(p):
        sys.exit(f"{p} missing: the Step 3 cache is needed (python step3_independent.py prepare)")
    return np.load(p)["X"], pd.read_csv(q)


def step3_split(ds, meta, seed):                    # identical to step3_independent.split_idx
    rng = np.random.default_rng(sseed("step3-split", ds, seed))
    if ds == "Motor":
        perm = rng.permutation(np.sort(meta.unit.unique()))
        test, stop = set(perm[:MOTOR_TEST]), set(perm[MOTOR_TEST:MOTOR_TEST + MOTOR_STOP])
        role = meta.unit.map(lambda u: "test" if u in test else "stop" if u in stop else "train")
    else:
        blocks = rng.permutation(np.sort(meta.block.unique()))
        nt, ns = round(HYD_TEST * len(blocks)), round(HYD_STOP * len(blocks))
        test, stop = set(blocks[:nt]), set(blocks[nt:nt + ns])
        role = meta.block.map(lambda b: "test" if b in test else "stop" if b in stop else "train")
    role = role.to_numpy()
    return np.flatnonzero(role == "train"), np.flatnonzero(role == "stop"), np.flatnonzero(role == "test")


def setting(dc, di, ds, seed):
    """complete training-side windows Xa (train + stop [+ report]), test windows Xte, index arrays into Xa,
    test-unit labels, namespace for masks and seeds"""
    key = (ds, seed)
    if key in _CACHE: return _CACHE[key]
    if ds in ("Motor", "Hydraulic"):
        if ds not in _CACHE: _CACHE[ds] = step3_cache(ds)
        X, meta = _CACHE[ds]
        itr, ist, ite = step3_split(ds, meta, seed)
        itrain = np.r_[itr, ist]
        Xa, Xte, _ = dc.standardize(X[itrain], X[ite])
        tr, st = np.arange(len(itr)), np.arange(len(itr), len(itrain))
        unit = (meta.unit if ds == "Motor" else meta.block).to_numpy()[ite]
        out = dict(Xa=Xa, Xte=Xte, tr=tr, st=st, unit_te=unit, ns="step3")
    else:
        D = dc.get_data(ds); sp = di.dev_split(ds)
        unit = np.arange(len(D["Xte"]))
        if ds == "Siemens":
            w = pd.read_csv(os.path.join(dc.CFG["out_dir"], "siemens_windows.csv"))
            unit = w[w.split == "test"].batch.to_numpy(); assert len(unit) == len(D["Xte"])
        out = dict(Xa=D["Xtr"], Xte=D["Xte"], tr=np.asarray(sp["train"]), st=np.asarray(sp["stop"]), unit_te=unit, ns="step4")
    _CACHE[key] = out
    return out


def masks(dc, ds, S, mech, lv, seed):
    def mk(X, split):
        rng = np.random.default_rng(sseed(f"{S['ns']}-mask", ds, mech, lv, seed, split))
        if mech == "MCAR": return dc.mask_mcar(X.shape, lv, rng)
        if mech == "MNAR": return dc.mask_mnar(X, lv, rng, dc.CFG["mnar_quantile"], dc.CFG["mnar_p_high"])
        if mech == "GAP": return dc.mask_gaps(X.shape, GAP_L[ds], int(round(GAP_FRAC * X.shape[1])), rng)
        raise ValueError(mech)
    return mk(S["Xa"], "train"), mk(S["Xte"], "test")


# ------------------------------------------------------------------------------------------- jobs
def job_list():
    lr, knn, heavy = [], [], []
    for ds in DATASETS:
        for mech, lv in CONDITIONS:
            for seed in SEEDS:
                base = dict(dataset=ds, mech=mech, level=lv, seed=seed)
                lr.append(dict(base, method="Linear regression", norm="global"))
                for mdl in MODELS:
                    for norm in NORMS:
                        (knn if mdl == "KNN" else heavy).append(dict(base, method=mdl, norm=norm))
    jobs = lr + knn + heavy
    for j in jobs:
        j["id"] = f'{j["dataset"]}|{j["mech"]}|{j["level"]}|{j["seed"]}|{j["method"]}|{j["norm"]}'
    return jobs


def res_path(j, ext):
    return os.path.join(OUT, "results", hashlib.md5(j["id"].encode()).hexdigest() + ext)


def run_job(j, dc, di, v2, ev):
    import torch
    ds, mech, lv, seed, method, norm = j["dataset"], j["mech"], j["level"], j["seed"], j["method"], j["norm"]
    S = setting(dc, di, ds, seed); Xa, Xte, tr, st = S["Xa"], S["Xte"], S["tr"], S["st"]
    Mtr, Mte = masks(dc, ds, S, mech, lv, seed)
    Xtr_m, Xte_m = dc.apply_mask(Xa, Mtr), dc.apply_mask(Xte, Mte)
    Xst_m = Xtr_m[st]; nst = np.setdiff1d(np.arange(len(Xa)), st)
    s = sseed(f"{S['ns']}-init", ds, mech, lv, seed, method); info = {}
    if method == "Linear regression":
        imp_te, imp_st = dc.impute_lr_time(Xte_m), dc.impute_lr_time(Xst_m)
    else:
        if norm == "global":
            Ztr, Zte, Zst_true, Zst_m = Xtr_m, Xte_m, Xa[st], Xst_m
            back_te = back_st = (lambda Z: Z)
        else:
            (mtr, s_tr), (mte, s_te), (mst, s_st) = seq_stats(Xtr_m), seq_stats(Xte_m), seq_stats(Xst_m)
            Ztr, Zte, Zst_true, Zst_m = (Xtr_m - mtr) / s_tr, (Xte_m - mte) / s_te, (Xa[st] - mst) / s_st, (Xst_m - mst) / s_st
            back_te = lambda Z: Z * s_te + mte; back_st = lambda Z: Z * s_st + mst
        if method == "KNN":
            Zte_i = dc.impute_knn(Ztr, Zte, dc.CFG["knn_k"])
            Zst_i = dc.impute_knn(Ztr[nst], Zst_m, dc.CFG["knn_k"])          # validation windows not in the reference
        elif method == "SAITS":
            Zall, val = ev.pypots_fit_impute("SAITS", ev.select_saits()["cfg"], Ztr[tr], Zst_true, Mtr[st],
                                             np.concatenate([Zte, Zst_m]), s)
            Zte_i, Zst_i = Zall[:len(Zte)], Zall[len(Zte):]; info["val_stop_rmse_model_space"] = val
        elif method == "Transformer":
            model = v2.DTINv2Imputer(v2.imputation_config(**TRANSFORMER), seed=s).fit(Ztr[tr], Zst_true, Mtr[st])
            Zte_i, Zst_i = model.impute(Zte), model.impute(Zst_m); del model
        else:
            raise ValueError(method)
        imp_te, imp_st = back_te(Zte_i), back_st(Zst_i)
    imp_te = np.where(np.isnan(Xte_m), imp_te, Xte_m); imp_st = np.where(np.isnan(Xst_m), imp_st, Xst_m)
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    np.savez_compressed(res_path(j, ".npz"), te=imp_te[Mte].astype(np.float32), st=imp_st[Mtr[st]].astype(np.float32))
    return dict(j, rmse=dc.rmse_at(Xte, imp_te, Mte), rmse_val=dc.rmse_at(Xa[st], imp_st, Mtr[st]), **info)


def run(worker=0, n_workers=1):
    if not os.path.exists(os.path.join(OUT, "PLAN_step4.md")):
        sys.exit("Write the plan first: python step4_dual.py plan")
    os.makedirs(os.path.join(OUT, "results"), exist_ok=True); os.makedirs(os.path.join(OUT, "errors"), exist_ok=True)
    dc, di, v2, ev = modules(); import torch; sha = script_sha()
    jobs = [j for i, j in enumerate(job_list()) if i % n_workers == worker]
    for i, j in enumerate(jobs, 1):
        p = res_path(j, ".json")
        if os.path.exists(p): continue
        print(f"[{i}/{len(jobs)}] {j['id']}", flush=True); t0 = time.time(); res = None
        for strict in (True, False):
            strict_mode(strict)
            try:
                res = run_job(j, dc, di, v2, ev); res["deterministic"] = strict; break
            except RuntimeError as e:
                if strict and "deterministic" in str(e).lower(): continue
                open(os.path.join(OUT, "errors", os.path.basename(p) + ".txt"), "w").write(j["id"] + "\n" + traceback.format_exc()); break
            except Exception:
                open(os.path.join(OUT, "errors", os.path.basename(p) + ".txt"), "w").write(j["id"] + "\n" + traceback.format_exc()); break
        if res is not None:
            res.update(seconds=round(time.time() - t0, 1), script_sha256=sha); tmp = p + ".tmp"
            json.dump(res, open(tmp, "w"), indent=1, default=float); os.replace(tmp, p)
    json.dump(dict(python=platform.python_version(), torch=torch.__version__, cuda=torch.version.cuda,
                   gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"),
              open(os.path.join(OUT, "environment.json"), "w"), indent=1)


def status():
    jobs = job_list(); done = sum(os.path.exists(res_path(j, ".json")) for j in jobs)
    errs = glob.glob(os.path.join(OUT, "errors", "*.txt"))
    print(f"finished {done} of {len(jobs)} jobs; errors: {len(errs)}")
    for e in errs[:5]: print("  ", open(e).read().splitlines()[0])


# ------------------------------------------------------------------------------------------- pack
def pack_path(ds, mech, lv):
    return os.path.join(OUT, "pack", f"{ds}_{mech}_{lv:g}.npz")


def pack():
    dc, di, _, _ = modules(); os.makedirs(os.path.join(OUT, "pack"), exist_ok=True)
    jobs = {j["id"]: j for j in job_list()}
    for ds in DATASETS:
        for mech, lv in CONDITIONS:
            A = {}
            for seed in SEEDS:
                S = setting(dc, di, ds, seed); Mtr, Mte = masks(dc, ds, S, mech, lv, seed)
                Xtr_m, Xte_m = dc.apply_mask(S["Xa"], Mtr), dc.apply_mask(S["Xte"], Mte)
                k = f"{seed}|"
                n, t, d = np.nonzero(Mte); A[k + "y_te"] = S["Xte"][Mte].astype(np.float32)
                A[k + "n_te"], A[k + "d_te"] = n.astype(np.int32), d.astype(np.int16)
                A[k + "unit_win"] = np.asarray(S["unit_te"]).astype(np.int64)
                _, _, d2 = np.nonzero(Mtr[S["st"]]); A[k + "y_st"] = S["Xa"][S["st"]][Mtr[S["st"]]].astype(np.float32)
                A[k + "d_st"] = d2.astype(np.int16)
                m_tr, l_tr, c_tr = vis_stats(Xtr_m[S["tr"]]); ok = c_tr >= 2
                A[k + "m_lo"] = np.where(ok, m_tr, np.inf).min(0); A[k + "m_hi"] = np.where(ok, m_tr, -np.inf).max(0)
                A[k + "l_lo"] = np.where(ok, l_tr, np.inf).min(0); A[k + "l_hi"] = np.where(ok, l_tr, -np.inf).max(0)
                m_te, l_te, c_te = vis_stats(Xte_m)
                A[k + "m_te"], A[k + "l_te"], A[k + "c_te"] = m_te.astype(np.float32), l_te.astype(np.float32), c_te.astype(np.int32)
                for method in ["Linear regression"] + MODELS:
                    for norm in (["global"] if method == "Linear regression" else NORMS):
                        jid = f"{ds}|{mech}|{lv}|{seed}|{method}|{norm}"
                        p = res_path(jobs[jid], ".npz")
                        if not os.path.exists(p): continue
                        z = np.load(p); A[f"{k}{method}|{norm}|te"] = z["te"]; A[f"{k}{method}|{norm}|st"] = z["st"]
            np.savez_compressed(pack_path(ds, mech, lv), **A)
            print("packed", pack_path(ds, mech, lv), f"{os.path.getsize(pack_path(ds, mech, lv)) / 1e6:.1f} MB")


# ------------------------------------------------------------------------------------------- analysis
def weights(ys, gs, ss, ds_, D):
    """validation-based mixing weights for global (a) per variant: pooled and per variable, selection and convex"""
    eg, es = gs - ys, ss - ys
    def conv(E, F):
        Eg, Es, C = (E * E).mean(), (F * F).mean(), (E * F).mean(); den = Eg + Es - 2 * C
        return 0.5 if den <= 1e-12 else float(np.clip((Es - C) / den, 0, 1))
    out = {"sel_pool": np.full(D, float((eg ** 2).mean() < (es ** 2).mean())), "comb_pool": np.full(D, conv(eg, es))}
    sv, cv = np.zeros(D), np.zeros(D)
    for d in range(D):
        k = ds_ == d
        if k.sum() == 0:
            sv[d], cv[d] = out["sel_pool"][d], out["comb_pool"][d]; continue
        sv[d] = float((eg[k] ** 2).mean() < (es[k] ** 2).mean()); cv[d] = conv(eg[k], es[k])
    out["sel_var"], out["comb_var"] = sv, cv
    return out


def analyze(pack_dir=None, write=True):
    pack_dir = pack_dir or os.path.join(OUT, "pack")
    rows, unit_rows, guard_rows = [], [], []
    for ds in DATASETS:
        for mech, lv in CONDITIONS:
            p = os.path.join(pack_dir, os.path.basename(pack_path(ds, mech, lv)))
            if not os.path.exists(p): continue
            A = np.load(p); cond = f"{mech} {lv:g}"
            for seed in SEEDS:
                k = f"{seed}|"
                if k + "y_te" not in A: continue
                y, n, d = A[k + "y_te"].astype(float), A[k + "n_te"], A[k + "d_te"]; unit = A[k + "unit_win"][n]
                D = len(A[k + "m_lo"])
                out = ((A[k + "m_te"] < A[k + "m_lo"]) | (A[k + "m_te"] > A[k + "m_hi"]) |
                       (A[k + "l_te"] < A[k + "l_lo"]) | (A[k + "l_te"] > A[k + "l_hi"])) & (A[k + "c_te"] >= 2)
                g_out = out[n, d]
                guard_rows.append(dict(dataset=ds, cond=cond, seed=seed, cells_out=float(out.mean()), entries_out=float(g_out.mean())))
                if k + "Linear regression|global|te" in A:
                    e = A[k + "Linear regression|global|te"] - y
                    rows.append(dict(dataset=ds, cond=cond, seed=seed, model="Linear regression", variant="-", rmse=float(np.sqrt((e ** 2).mean()))))
                for mdl in MODELS:
                    if any(f"{k}{mdl}|{nm}|te" not in A for nm in NORMS): continue
                    g, s_ = A[f"{k}{mdl}|global|te"].astype(float), A[f"{k}{mdl}|seq|te"].astype(float)
                    W = weights(A[k + "y_st"].astype(float), A[f"{k}{mdl}|global|st"].astype(float),
                                A[f"{k}{mdl}|seq|st"].astype(float), A[k + "d_st"], D)
                    preds = {"seq": s_, "global": g}
                    for name, a in W.items():
                        av = a[d]
                        preds[name] = av * g + (1 - av) * s_
                        ag = np.where(g_out, 0.0, av)
                        preds[name + "+guard"] = ag * g + (1 - ag) * s_
                        rows.append(dict(dataset=ds, cond=cond, seed=seed, model=mdl, variant=name + ":weight_mean", rmse=float(a.mean())))
                    for name in VARIANTS:
                        e2 = (preds[name] - y) ** 2
                        rows.append(dict(dataset=ds, cond=cond, seed=seed, model=mdl, variant=name, rmse=float(np.sqrt(e2.mean()))))
                        u = pd.DataFrame(dict(u=unit, e2=e2)).groupby("u").e2.mean() ** 0.5
                        unit_rows.append(dict(dataset=ds, cond=cond, seed=seed, model=mdl, variant=name, unit_median=float(u.median())))
    r = pd.DataFrame(rows); ur = pd.DataFrame(unit_rows); gr = pd.DataFrame(guard_rows)
    if r.empty: sys.exit("no packed results")
    v = r[r.variant.isin(VARIANTS)]
    m = v.groupby(["dataset", "cond", "model", "variant"]).rmse.mean().unstack()
    orc = m[["global", "seq"]].min(axis=1)
    ratio = m[VARIANTS].div(orc, axis=0)
    summ = pd.DataFrame(dict(cells_within=(ratio <= WITHIN).sum(), n_cells=ratio.notna().sum(),
                             median_ratio=ratio.median(), worst_ratio=ratio.max())).loc[VARIANTS]
    order = {"pool": 0, "var": 1}
    def simplicity(name):
        base = name.replace("+guard", "")
        return (("comb" in base) * 2 + order[base.split("_")[1]] if "_" in base else 9) + ("+guard" in name) * 4
    cand = summ.drop(["seq", "global"])
    best_n = cand.cells_within.max()
    tied = cand[cand.cells_within >= best_n - 1]
    tied = tied.assign(simp=[simplicity(x) for x in tied.index]).sort_values(["worst_ratio", "simp"])
    tied2 = tied[tied.worst_ratio <= tied.worst_ratio.min() * 1.001].sort_values("simp")
    choice = tied2.index[0]
    L = ["# Step 4 report (development)", "", f"cells: {int(summ.n_cells.max())} of {len(DATASETS) * len(CONDITIONS) * len(MODELS)}", "",
         "## Variants: mean RMSE relative to the better of global and seq (oracle)", "", "```", summ.round(3).to_string(), "```", "",
         f"**Chosen by the pre-written rule: {choice}**", "",
         "## Ratio to the oracle per cell", "", "```", ratio.round(3).to_string(), "```", "",
         "## Mean RMSE per cell (LR = linear regression on time)", "", "```",
         m.join(r[r.model == "Linear regression"].groupby(["dataset", "cond"]).rmse.mean().rename("LR"), on=["dataset", "cond"])
          .round(4).to_string(), "```", ""]
    wv = r[r.variant.str.endswith(":weight_mean")].copy(); wv["variant"] = wv.variant.str.replace(":weight_mean", "")
    L += ["## Mean weight on global (validation estimate)", "", "```",
          wv.groupby(["dataset", "cond", "model", "variant"]).rmse.mean().unstack().round(2).to_string(), "```", ""]
    L += ["## Guard: share of test window-variable pairs out of the training range", "", "```",
          gr.groupby(["dataset", "cond"])[["cells_out", "entries_out"]].mean().round(4).to_string(), "```", ""]
    um = ur.groupby(["dataset", "cond", "model", "variant"]).unit_median.mean().unstack()
    L += ["## Median over test units of the per-unit RMSE (mean over seeds)", "", "```", um[VARIANTS].round(4).to_string(), "```", ""]
    rep = None
    s3 = os.path.join(STEP3, "step3_all_runs.csv")
    jr = [json.load(open(q)) for q in glob.glob(os.path.join(OUT, "results", "*.json"))]
    if os.path.exists(s3) and jr:
        a = pd.DataFrame(jr); b = pd.read_csv(s3)
        x = a.merge(b[["id", "rmse"]], on="id", suffixes=("", "_step3"))
        if len(x):
            dif = (x.rmse - x.rmse_step3).abs()
            rep = f"Step 3 reproduction (Motor, Hydraulic; same splits, masks and seeds): {len(x)} runs, max |RMSE difference| {dif.max():.2e}, runs differing by more than 1e-4: {int((dif > 1e-4).sum())}"
            L += ["## Reproduction of Step 3", "", rep, ""]
            x.assign(diff=dif)[["id", "rmse", "rmse_step3", "diff"]].to_csv(os.path.join(OUT, "step4_step3_reproduction.csv"), index=False)
    if jr:
        L += [f"Runs without strict determinism: {int((~pd.DataFrame(jr).deterministic.astype(bool)).sum())}"]
    txt = "\n".join(L)
    if write:
        open(os.path.join(OUT, "REPORT_step4.md"), "w", encoding="utf-8").write(txt)
        r.to_csv(os.path.join(OUT, "step4_variant_runs.csv"), index=False); ur.to_csv(os.path.join(OUT, "step4_unit_runs.csv"), index=False)
        if jr: pd.DataFrame(jr).to_csv(os.path.join(OUT, "step4_all_runs.csv"), index=False)
    print(txt)
    return r, ur, gr


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["plan", "run", "status", "pack", "report"])
    ap.add_argument("--worker", type=int, default=0); ap.add_argument("--n-workers", type=int, default=1)
    ap.add_argument("--pack-dir", default=None)
    a = ap.parse_args()
    if a.cmd == "plan":
        os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, "PLAN_step4.md")
        if os.path.exists(p): sys.exit(f"{p} already exists")
        open(p, "w", encoding="utf-8").write(PLAN.format(sha=script_sha(), w=WITHIN) + f"\nWritten: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(open(p, encoding="utf-8").read())
    elif a.cmd == "run": run(a.worker, a.n_workers)
    elif a.cmd == "status": status()
    elif a.cmd == "pack": pack()
    else: analyze(a.pack_dir)
