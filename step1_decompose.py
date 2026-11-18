"""
step1_decompose.py - Step 1 of the follow-up study.

Question: is the advantage of DTIN-v2 on Siemens due to the transformer (and its mask input), or to the
mask-aware per-sequence normalization that every model could use?

The normalization used inside DTIN-v2 is applied as a wrapper to the baselines (KNN, BRITS, SAITS), and
DTIN-v2 is run with and without its normalization and mask input. Siemens and ECG200 (including their former
test splits) are DEVELOPMENT data in the follow-up study: nothing produced here is independent evidence.

Run from the working folder (dtin_core.py, dtin_v2.py, dtin_v2_eval.py, dtin_improve.py, dtin_outputs/):

  python step1_decompose.py plan                       # 1. writes step1_outputs/PLAN_step1.md -> commit it first
  python step1_decompose.py run                        # 2. all jobs, resumable (finished jobs are skipped)
  python step1_decompose.py run --worker 0 --n-workers 3   #    or split the jobs over 3 terminals (k = 0, 1, 2)
  python step1_decompose.py status                     #    progress
  python step1_decompose.py report                     # 3. tables and the decision defined in the plan
"""
import argparse
import glob
import hashlib
import json
import os
import platform
import sys
import time
import traceback

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")      # before CUDA is initialised
import numpy as np
import pandas as pd

OUT = "step1_outputs"
SEEDS = [0, 1, 2, 3, 4]
CONDITIONS = [("Siemens", "MCAR", 0.3), ("Siemens", "MAR", 0.3), ("Siemens", "MNAR", 0.3),
              ("Siemens", "GAP", 30), ("ECG200", "MCAR", 0.3)]
BASELINES = ["KNN", "BRITS", "SAITS"]                   # each with global and with per-sequence normalization
DTIN_VARIANTS = {                                       # name -> changes to the final DTIN-v2 imputation config
    "DTIN-v2 (mask input + seq-norm)": {},
    "DTIN-v2 w/o seq-norm": dict(revin=False),
    "DTIN-v2 w/o mask input": dict(mask_input=False),
    "Transformer (no mask input, no seq-norm)": dict(mask_input=False, revin=False),
}
THRESH_GAP = 0.05          # relative RMSE gap that counts as an architecture advantage
THRESH_NORM = 0.05         # relative RMSE change that counts as a normalization effect
EPS = 1e-5                 # as in dtin_v2._normalise

PLAN = f"""# Step 1 - decomposition of the DTIN-v2 advantage (pre-specified)

Written before any Step 1 result was computed. Commit this file (with its date) before running the jobs.

## Question
Is the lower imputation RMSE of DTIN-v2 on Siemens explained by the transformer and its mask input, or by the
mask-aware per-sequence normalization, which any imputation model can use?

## Data status
Siemens and ECG200, including their former test splits, are development data in the follow-up study. The
results of Step 1 guide the method design and are not reported as independent evidence.

## Design
* Conditions: Siemens MCAR 30%, MAR 30%, MNAR 30%, consecutive gaps of length 30 (40% removed); ECG200 MCAR 30%.
* Seeds: {SEEDS}. Missing masks as in the earlier experiments (same mask generator and seeds).
* Training data: development-training part of the training set; early stopping on the early-stopping part
  (same splits as before); evaluation on the former test split.
* Normalization wrapper (identical to the one inside DTIN-v2): per sequence and variable, mean m and standard
  deviation s of the visible values, s = sqrt(sum v (x - m)^2 / c + {EPS}); m = 0 if c = 0 and s = 1 if c < 2.
  Inputs are normalized with their own statistics, the model imputes in the normalized space, and the
  output is transformed back. Validation targets are normalized with the statistics of the masked validation inputs.
* Methods: linear regression (invariant to the wrapper; reference), KNN, BRITS and SAITS each with
  global standardization only ("global") and with the wrapper ("seq"); DTIN-v2 variants:
  {", ".join(DTIN_VARIANTS)}.
* Fixed settings: BRITS hidden 64; SAITS = configuration selected earlier on development data; KNN k = 5;
  DTIN-v2 = final imputation configuration (lambda = 0). No tuning in Step 1. CSDI is excluded
  (unstable and slow in the earlier experiments).
* Metrics: RMSE at removed positions; on Siemens also without PI12002_PV_Out.

## Decision rules (fixed now)
For each Siemens condition c and each metric, let B* be the method with the lowest mean RMSE among the
baselines with the wrapper (linear regression, KNN-seq, BRITS-seq, SAITS-seq), G_c = (RMSE(B*) - RMSE(DTIN-v2)) / RMSE(B*)
and W_c the number of seeds in which DTIN-v2 has a lower RMSE than B*.

* R1 - architecture advantage: G_c >= {THRESH_GAP} and W_c >= 4 of 5 in at least 3 of the 4 Siemens conditions,
  on both metrics. Then the follow-up study may claim the mask-aware transformer as part of its contribution.
* R2 - normalization explains the advantage: R1 does not hold. Then the transformer architecture is not claimed
  as a contribution, and Step 2 develops the normalization as a model-agnostic component evaluated with several
  imputation models.
* N1 - normalization helps on Siemens: (RMSE(global) - RMSE(seq)) / RMSE(global) >= {THRESH_NORM} for at least
  2 of the 3 baselines (KNN, BRITS, SAITS) in at least 3 of the 4 Siemens conditions (primary metric).
* N2 - normalization harms on ECG200: the same relative change is <= -{THRESH_NORM} for at least 2 of the 3
  baselines. Then Step 2 must include an adaptive rule whose design target is never to be more than 2% worse
  than global standardization on development data.
The mask-input effect (DTIN-v2 with and without mask input) is reported descriptively.
"""


# ------------------------------------------------------------------------------------------- normalization
def seq_stats(X_nan):
    """Per-sequence, per-variable statistics of the visible (non-NaN) values; same rule as dtin_v2._normalise."""
    v = ~np.isnan(X_nan); c = v.sum(1, keepdims=True).astype(float)
    x = np.nan_to_num(X_nan)
    m = (x * v).sum(1, keepdims=True) / np.maximum(c, 1)
    s = np.sqrt((((x - m) * v) ** 2).sum(1, keepdims=True) / np.maximum(c, 1) + EPS)
    m = np.where(c > 0, m, 0.0); s = np.where(c > 1, s, 1.0)
    return m, s


def normalize(X, m, s):
    return (X - m) / s


def denormalize(Z, m, s):
    return Z * s + m


# ------------------------------------------------------------------------------------------- environment
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
    import dtin_improve as di
    import dtin_v2 as v2
    import dtin_v2_eval as ev
    return dc, di, v2, ev


# ------------------------------------------------------------------------------------------- jobs
def job_list():
    jobs = []
    for ds, mech, lv in CONDITIONS:
        for seed in SEEDS:
            jobs.append(dict(dataset=ds, mech=mech, level=lv, seed=seed, method="Linear regression", norm="global"))
            for b in BASELINES:
                for norm in ("global", "seq"):
                    jobs.append(dict(dataset=ds, mech=mech, level=lv, seed=seed, method=b, norm=norm))
            for name in DTIN_VARIANTS:
                jobs.append(dict(dataset=ds, mech=mech, level=lv, seed=seed, method=name, norm="internal"))
    for j in jobs:
        j["id"] = f'{j["dataset"]}|{j["mech"]}|{j["level"]}|{j["seed"]}|{j["method"]}|{j["norm"]}'
    return jobs


def res_path(j):
    return os.path.join(OUT, "results", hashlib.md5(j["id"].encode()).hexdigest() + ".json")


def run_job(j, dc, di, v2, ev):
    import torch
    ds, mech, lv, seed, method, norm = j["dataset"], j["mech"], j["level"], j["seed"], j["method"], j["norm"]
    D = dc.get_data(ds); Xtr, Xte = D["Xtr"], D["Xte"]; sp = di.dev_split(ds)
    Mtr = dc.make_mask(ds, Xtr, mech, lv, seed, "train"); Mte = dc.make_mask(ds, Xte, mech, lv, seed, "test")
    Xtr_m, Xte_m = dc.apply_mask(Xtr, Mtr), dc.apply_mask(Xte, Mte)
    s = dc.stable_seed("step1", ds, mech, lv, seed, method, norm)
    tr, st = sp["train"], sp["stop"]
    info = {}
    if method == "Linear regression":
        imp = dc.impute_lr_time(Xte_m)
    elif method in BASELINES:
        if norm == "seq":
            m_tr, s_tr = seq_stats(Xtr_m); m_te, s_te = seq_stats(Xte_m)
            Ztr, Zte = normalize(Xtr_m, m_tr, s_tr), normalize(Xte_m, m_te, s_te)
            m_st, s_st = seq_stats(Xtr_m[st]); Zst_true = normalize(Xtr[st], m_st, s_st)
        else:
            Ztr, Zte, Zst_true = Xtr_m, Xte_m, Xtr[st]
        if method == "KNN":
            Zimp = dc.impute_knn(Ztr, Zte, dc.CFG["knn_k"])
        else:
            hp = ev.select_saits()["cfg"] if method == "SAITS" else ev.BASE_DEFAULT[method]
            Zimp, val = ev.pypots_fit_impute(method, hp, Ztr[tr], Zst_true, Mtr[st], Zte, s)
            info["val_stop_rmse_in_model_space"] = val
        imp = denormalize(Zimp, m_te, s_te) if norm == "seq" else Zimp
        imp = np.where(np.isnan(Xte_m), imp, Xte_m)
    elif method in DTIN_VARIANTS:
        cfg = v2.imputation_config(**DTIN_VARIANTS[method])
        model = v2.DTINv2Imputer(cfg, seed=s).fit(Xtr_m[tr], Xtr[st], Mtr[st])
        imp = model.impute(Xte_m); info["best_step"] = model.info.get("best_step"); del model
    else:
        raise ValueError(method)
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    res = dict(j, rmse=dc.rmse_at(Xte, imp, Mte), **info)
    if ds == "Siemens":
        k = ev.shifted_index(); M2 = Mte.copy(); M2[:, :, k] = False
        res["rmse_wo_shifted"] = dc.rmse_at(Xte, imp, M2)
    return res


def run(worker=0, n_workers=1):
    if not os.path.exists(os.path.join(OUT, "PLAN_step1.md")):
        sys.exit("Write and commit the plan first: python step1_decompose.py plan")
    os.makedirs(os.path.join(OUT, "results"), exist_ok=True); os.makedirs(os.path.join(OUT, "errors"), exist_ok=True)
    dc, di, v2, ev = modules()
    import torch
    jobs = [j for i, j in enumerate(job_list()) if i % n_workers == worker]
    for i, j in enumerate(jobs, 1):
        p = res_path(j)
        if os.path.exists(p): continue
        print(f"[{i}/{len(jobs)}] {j['id']}", flush=True)
        t0 = time.time(); res = None
        for strict in (True, False):
            strict_mode(strict)
            try:
                res = run_job(j, dc, di, v2, ev); res["deterministic"] = strict; break
            except RuntimeError as e:
                if strict and "deterministic" in str(e).lower():
                    print("   no deterministic kernel -> warn_only mode", flush=True); continue
                open(os.path.join(OUT, "errors", os.path.basename(p) + ".txt"), "w").write(j["id"] + "\n" + traceback.format_exc())
                break
            except Exception:
                open(os.path.join(OUT, "errors", os.path.basename(p) + ".txt"), "w").write(j["id"] + "\n" + traceback.format_exc())
                break
        if res is not None:
            res["seconds"] = round(time.time() - t0, 1)
            tmp = p + ".tmp"; json.dump(res, open(tmp, "w"), indent=1, default=float); os.replace(tmp, p)
    env = dict(python=platform.python_version(), torch=torch.__version__, cuda=torch.version.cuda,
               gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
    json.dump(env, open(os.path.join(OUT, "environment.json"), "w"), indent=1)


def status():
    jobs = job_list(); done = sum(os.path.exists(res_path(j)) for j in jobs)
    errs = glob.glob(os.path.join(OUT, "errors", "*.txt"))
    print(f"finished {done} of {len(jobs)} jobs; errors: {len(errs)}")
    for e in errs[:5]: print("  ", open(e).read().splitlines()[0])


# ------------------------------------------------------------------------------------------- report
def lv_str(lv):
    lv = float(lv)
    return str(int(lv)) if lv.is_integer() else f"{lv:g}"


def label(r):
    return r["method"] if r["norm"] == "internal" or r["method"] == "Linear regression" else f'{r["method"]}-{r["norm"]}'


def report():
    rows = [json.load(open(p)) for p in glob.glob(os.path.join(OUT, "results", "*.json"))]
    if not rows: sys.exit("no results yet")
    d = pd.DataFrame(rows); d["label"] = d.apply(label, axis=1)
    d["cond"] = d.apply(lambda r: f'{r["dataset"]} {r["mech"]} {lv_str(r["level"])}', axis=1)
    metrics = [("rmse", "all variables"), ("rmse_wo_shifted", "without PI12002_PV_Out")]
    lines = ["# Step 1 report", "", f"Jobs finished: {len(d)} of {len(job_list())}", ""]
    tables = {}
    for col, name in metrics:
        sub = d.dropna(subset=[col]) if col in d else d.iloc[0:0]
        if sub.empty: continue
        t = sub.groupby(["cond", "label"])[col].agg(["mean", "std", "count"]).reset_index()
        tables[col] = t
        piv = t.pivot(index="label", columns="cond", values="mean").round(4)
        lines += [f"## Mean RMSE ({name})", "", "```", piv.to_string(), "```", ""]
        piv.to_csv(os.path.join(OUT, f"step1_mean_{col}.csv"))
    # decision rules
    sie = [f"Siemens {m} {lv_str(lv)}" for ds, m, lv in CONDITIONS if ds == "Siemens"]
    normed = ["Linear regression", "KNN-seq", "BRITS-seq", "SAITS-seq"]
    dtin = "DTIN-v2 (mask input + seq-norm)"
    r1_ok = {}
    for col, name in metrics:
        if col not in d: continue
        hits = 0; detail = []
        for c in sie:
            sub = d[(d.cond == c)].dropna(subset=[col])
            means = sub.groupby("label")[col].mean()
            cand = means.reindex(normed).dropna()
            if cand.empty or dtin not in means: continue
            best = cand.idxmin(); G = (cand[best] - means[dtin]) / cand[best]
            a = sub[sub.label == best].set_index("seed")[col]; b = sub[sub.label == dtin].set_index("seed")[col]
            cm = sorted(set(a.index) & set(b.index)); W = int((b[cm] < a[cm]).sum())
            ok = G >= THRESH_GAP and W >= 4; hits += ok
            detail.append(f"| {c} | {best} | {cand[best]:.4f} | {means[dtin]:.4f} | {G:+.3f} | {W}/{len(cm)} | {'yes' if ok else 'no'} |")
        r1_ok[col] = hits >= 3
        lines += [f"## R1 check ({name})", "", "| condition | best normalized baseline B* | RMSE B* | RMSE DTIN-v2 | G | DTIN-v2 better | meets R1 |",
                  "|---|---|---|---|---|---|---|"] + detail + ["", f"conditions meeting R1: {hits} of {len(sie)}", ""]
    decision = "R1 - architecture advantage" if r1_ok and all(r1_ok.values()) else "R2 - normalization explains the advantage"
    # normalization effects
    def rel(c, b, col="rmse"):
        sub = d[(d.cond == c)]; g = sub[sub.label == f"{b}-global"][col].mean(); s_ = sub[sub.label == f"{b}-seq"][col].mean()
        return (g - s_) / g if g == g and s_ == s_ else np.nan
    n1 = sum(sum(rel(c, b) >= THRESH_NORM for b in BASELINES) >= 2 for c in sie) >= 3
    ecg = "ECG200 MCAR 0.3"; n2 = sum(rel(ecg, b) <= -THRESH_NORM for b in BASELINES) >= 2
    lines += ["## Normalization effects (relative RMSE change, global -> seq; positive = normalization helps)", "",
              "| condition | " + " | ".join(BASELINES) + " |", "|---|" + "---|" * len(BASELINES)]
    for c in sie + [ecg]:
        lines.append(f"| {c} | " + " | ".join(f"{rel(c, b):+.3f}" for b in BASELINES) + " |")
    lines += ["", f"N1 (normalization helps on Siemens): {'yes' if n1 else 'no'}",
              f"N2 (normalization harms on ECG200): {'yes' if n2 else 'no'}", "",
              f"## Decision according to the plan: **{decision}**", ""]
    if decision.startswith("R2"):
        lines.append("The transformer architecture is not claimed as a contribution; Step 2 develops the normalization as a model-agnostic component.")
    else:
        lines.append("The mask-aware transformer may be claimed as part of the contribution, together with the normalization.")
    if n2:
        lines.append("Step 2 must include an adaptive rule that is never more than 2% worse than global standardization on development data.")
    nd = int((~d.get("deterministic", pd.Series(True, index=d.index)).astype(bool)).sum())
    lines += ["", f"Jobs run without strict determinism: {nd}"]
    txt = "\n".join(lines)
    open(os.path.join(OUT, "REPORT_step1.md"), "w", encoding="utf-8").write(txt)
    d.to_csv(os.path.join(OUT, "step1_all_runs.csv"), index=False)
    print(txt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "run", "status", "report"])
    ap.add_argument("--worker", type=int, default=0); ap.add_argument("--n-workers", type=int, default=1)
    a = ap.parse_args()
    if a.cmd == "plan":
        os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, "PLAN_step1.md")
        if os.path.exists(p): sys.exit(f"{p} already exists; it must not be changed after results exist")
        open(p, "w", encoding="utf-8").write(PLAN + f"\nWritten: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(open(p, encoding="utf-8").read()); print("SHA-256:", hashlib.sha256(open(p, "rb").read()).hexdigest())
    elif a.cmd == "run":
        run(a.worker, a.n_workers)
    elif a.cmd == "status":
        status()
    else:
        report()
