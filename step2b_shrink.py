"""
step2b_shrink.py - Step 2b: the single permitted revision of the reliability-weighted normalization.

Step 2 (PLAN_step2b.md) failed H1. The plan allows at most one revision on development data, documented with its
reason; if H1 still fails, the study is framed as an analysis of normalization under missingness.

  python step2b_shrink.py plan                              # write step2b_outputs/PLAN_step2b.md -> record it first
  python step2b_shrink.py run [--worker k --n-workers K]    # resumable
  python step2b_shrink.py status
  python step2b_shrink.py report
"""
import argparse, glob, hashlib, json, os, platform, sys, time, traceback
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import numpy as np
import pandas as pd

OUT = "step2b_outputs"
EPS = 1e-5
SEEDS = [0, 1, 2, 3, 4]
CONDITIONS = [("Siemens", "MCAR", 0.3), ("Siemens", "MAR", 0.3), ("Siemens", "MNAR", 0.3), ("Siemens", "GAP", 30),
              ("Siemens", "MCAR", 0.7), ("ECG200", "MCAR", 0.3), ("ECG200", "MCAR", 0.7)]
NORMS = ["global", "seq", "shrink"]
PLUGIN_MODELS = ["SAITS", "KNN", "Transformer"]        # every normalization, every condition
ECG_ONLY = ["BRITS"]                                   # every normalization, ECG200 only (cost on Siemens)
TRANSFORMER = dict(revin=False, mask_input=True, mask_mode="mix")       # DTIN backbone, external normalization
NO_HARM = 1.02            # H1: shrink <= 1.02 x min(global, seq)   (unchanged from Step 2)
NO_HARM_SHARE = 0.90      # ... in at least 90 % of the cells        (unchanged from Step 2)

PLAN = f"""# Step 2b - revised reliability-weighted normalization (pre-specified; the single permitted revision)

Written after Step 2 and before any Step 2b result was computed. Record this file (with its date) before running.

## Why a revision (Step 2, development data)
H1 was not supported (10 of 38 cells within 2%). Diagnostics on the normalized INPUTS (no model output was used):
* 37% of the Siemens sequence-variable cells are (nearly) constant within the window. Version 1 used the pooled
  within-sequence variance in the location weight, so these sequences were shrunk towards the training mean although
  their own mean is exact; divided by their tiny scale, this produced normalized values up to 5,570 (99th percentile
  60, versus 3 for per-sequence normalization).
* For strongly autocorrelated variables the AR(1) effective sample size was about 1, so the scale weight was 0 and
  sequences with a standard deviation of 4 were divided by the training typical scale 0.0055.
* One setpoint (FIC14002_SP) is constant in every training window but varies in one test window; shrinking its scale
  towards the training value again produced extreme inputs.

## Revised method fixed now (no tuning parameter)
For variable d and a sequence with c visible values out of T, own mean m_seq, own variance var and log standard
deviation l_seq = 0.5 log(var + {EPS}):
* sampling variance of the mean: var / c x (1 - c / T) (the pooled training variance when c < 2) - the variability
  caused by which values are visible, with the finite-population correction; no AR(1) correction;
* sampling variance of l_seq: 1 / (2 (c - 1)) x (1 - c / T);
* tau2, tau2_l: between-sequence variances of m_seq and l_seq in the masked training data minus the mean sampling
  variances (method of moments, floored at 0); mu, lam: their training means;
* w = tau2 / (tau2 + sampling variance of the mean) (1 if the sampling variance is 0, 0 if c = 0);
  w_l likewise for the log scale (0 if c < 2);
* out-of-range rule: if l_seq lies outside the range of l_seq in the training sequences, w = w_l = 1;
* m* = w m_seq + (1 - w) mu, s* = exp(w_l l_seq + (1 - w_l) lam).
Input check done before this plan (Siemens MCAR 30% and 70%, seed 0): the 50th/99th/99.9th percentiles of the
normalized inputs equal those of per-sequence normalization (max 12 versus 5,570 for version 1).

## Design (as in Step 2, with two changes)
* Conditions: Siemens MCAR 30%, MAR 30%, MNAR 30%, consecutive gaps of length 30, MCAR 70%; ECG200 MCAR 30%, 70%.
  Seeds {SEEDS}; same splits and masks as before.
* Normalizations: global, seq, shrink (revised). Models: SAITS, KNN, the DTIN transformer (internal normalization
  off) in every condition; BRITS on ECG200 only. Settings unchanged; no tuning.
* Change 1: the model initialization seed no longer depends on the normalization (common random numbers), so that the
  three normalizations of one model, condition and seed are compared with the same initialization. In Step 2, two
  mathematically almost identical inputs (ECG200, global versus shrink with w = 0) differed by about 3% in RMSE for
  the transformer, which is larger than the 2% margin.
* Change 2: H2 (mixed versus point masking) is not re-tested; it was not supported in Step 2 and is not claimed.

## Decision rule (unchanged from Step 2)
Cells: every (model, condition, metric) - SAITS, KNN, Transformer in all conditions, BRITS in the ECG200 conditions;
both metrics on Siemens, RMSE on ECG200. ref = min(mean RMSE global, mean RMSE seq).
* H1 supported: mean RMSE shrink <= {NO_HARM} x ref in at least {int(NO_HARM_SHARE * 100)}% of the cells -> the revised
  normalization goes to Step 3 unchanged.
* H1 not supported: no further revision; the study is framed as an analysis of normalization under missingness.
* Reported descriptively: cells where shrink is more than 2% better than ref; weights; normalized-input percentiles.
"""


def _basic(X_nan):
    v = ~np.isnan(X_nan); c = v.sum(1).astype(float); x = np.nan_to_num(X_nan)
    m = (x * v).sum(1) / np.maximum(c, 1)
    var = (((x - m[:, None, :]) * v) ** 2).sum(1) / np.maximum(c, 1)
    return v, c, x, m, var
class ShrinkNormV2:
    """Revision: (1) sequence-specific sampling variance; (2) sampling variance of the masking itself
    (visible values as a random subset of the T values of the sequence, finite-population correction),
    instead of an AR(1) effective sample size."""
    def _sv_mean(self, c, var, T):
        s2 = np.where(c >= 2, var, self.sig2)
        return s2 / np.maximum(c, 1) * np.clip(1 - c / T, 0, 1)
    def _sv_log(self, c, T):
        return 1.0 / (2.0 * np.maximum(c - 1, 1)) * np.clip(1 - c / T, 0, 1)
    def fit(self, X_nan):
        v, c, x, m, var = _basic(X_nan); T = X_nan.shape[1]; ok = c >= 2
        wts = np.where(ok, c, 0.0)
        self.sig2 = (var * wts).sum(0) / np.maximum(wts.sum(0), 1)
        self.mu = (m * c).sum(0) / np.maximum(c.sum(0), 1)
        nm = lambda a: np.nan_to_num(np.nanmean(np.where(ok, a, np.nan), 0)); nv = lambda a: np.nan_to_num(np.nanvar(np.where(ok, a, np.nan), 0))
        self.tau2 = np.maximum(0.0, nv(m) - nm(self._sv_mean(c, var, T)))
        l = 0.5 * np.log(var + EPS)
        self.lam = nm(l); self.tau2_l = np.maximum(0.0, nv(l) - nm(self._sv_log(c, T)))
        lo = np.where(ok, l, np.inf).min(0); hi = np.where(ok, l, -np.inf).max(0)
        self.l_lo, self.l_hi = lo, hi                      # training range of the log standard deviations
        return self
    def stats(self, X_nan):
        v, c, x, m, var = _basic(X_nan); T = X_nan.shape[1]
        sv = self._sv_mean(c, var, T)
        w = np.where(sv > 0, self.tau2 / (self.tau2 + sv + 1e-300), 1.0); w = np.where(c > 0, w, 0.0)
        svl = self._sv_log(c, T)
        wl = np.where(svl > 0, self.tau2_l / (self.tau2_l + svl + 1e-300), 1.0); wl = np.where(c >= 2, wl, 0.0)
        l_seq = 0.5 * np.log(var + EPS)
        out = (c >= 2) & ((l_seq > self.l_hi) | (l_seq < self.l_lo))   # outside the training range: keep own statistics
        w = np.where(out, 1.0, w); wl = np.where(out, 1.0, wl)
        ms = w * m + (1 - w) * self.mu
        ls = wl * l_seq + (1 - wl) * self.lam
        return ms[:, None, :], np.exp(ls)[:, None, :], w, wl


def seq_stats(X_nan):
    v = ~np.isnan(X_nan); c = v.sum(1, keepdims=True).astype(float); x = np.nan_to_num(X_nan)
    m = (x * v).sum(1, keepdims=True) / np.maximum(c, 1)
    s = np.sqrt((((x - m) * v) ** 2).sum(1, keepdims=True) / np.maximum(c, 1) + EPS)
    return np.where(c > 0, m, 0.0), np.where(c > 1, s, 1.0)


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


def job_list():
    jobs = []
    for ds, mech, lv in CONDITIONS:
        for seed in SEEDS:
            add = lambda method, norm: jobs.append(dict(dataset=ds, mech=mech, level=lv, seed=seed, method=method, norm=norm))
            for mdl in PLUGIN_MODELS + (ECG_ONLY if ds == "ECG200" else []):
                for norm in NORMS: add(mdl, norm)
    for j in jobs:
        j["id"] = f'{j["dataset"]}|{j["mech"]}|{j["level"]}|{j["seed"]}|{j["method"]}|{j["norm"]}'
    return jobs


def res_path(j):
    return os.path.join(OUT, "results", hashlib.md5(j["id"].encode()).hexdigest() + ".json")


def run_job(j, dc, di, v2, ev):
    import torch
    ds, mech, lv, seed, method, norm = j["dataset"], j["mech"], j["level"], j["seed"], j["method"], j["norm"]
    D = dc.get_data(ds); Xtr, Xte = D["Xtr"], D["Xte"]; sp = di.dev_split(ds); tr, st = sp["train"], sp["stop"]
    Mtr = dc.make_mask(ds, Xtr, mech, lv, seed, "train"); Mte = dc.make_mask(ds, Xte, mech, lv, seed, "test")
    Xtr_m, Xte_m = dc.apply_mask(Xtr, Mtr), dc.apply_mask(Xte, Mte)
    s = dc.stable_seed("step2b", ds, mech, lv, seed, method); info = {}      # common seed across normalizations
    if True:
        Xst_m = Xtr_m[st]
        if norm == "global":
            Ztr, Zte, Zst = Xtr_m, Xte_m, Xtr[st]; back = lambda Z: Z
        else:
            if norm == "seq":
                f = seq_stats
            else:
                sn = ShrinkNormV2().fit(Xtr_m)
                f = lambda X: sn.stats(X)[:2]
                _, _, w, wl = sn.stats(Xte_m)
                info.update(w_mean=float(w.mean()), wl_mean=float(wl.mean()))
            (mtr, s_tr), (mte, s_te), (mst, s_st) = f(Xtr_m), f(Xte_m), f(Xst_m)
            Ztr, Zte, Zst = (Xtr_m - mtr) / s_tr, (Xte_m - mte) / s_te, (Xtr[st] - mst) / s_st
            back = lambda Z: Z * s_te + mte
        za = np.abs(Zte[~np.isnan(Zte)])
        info.update(zin_p999=float(np.percentile(za, 99.9)), zin_max=float(za.max()))
        if method == "KNN":
            Zimp = dc.impute_knn(Ztr, Zte, dc.CFG["knn_k"])
        elif method in ("SAITS", "BRITS"):
            hp = ev.select_saits()["cfg"] if method == "SAITS" else ev.BASE_DEFAULT[method]
            Zimp, val = ev.pypots_fit_impute(method, hp, Ztr[tr], Zst, Mtr[st], Zte, s); info["val_stop_rmse_model_space"] = val
        elif method == "Transformer":
            cfg = v2.imputation_config(**TRANSFORMER)
            model = v2.DTINv2Imputer(cfg, seed=s).fit(Ztr[tr], Zst, Mtr[st]); Zimp = model.impute(Zte); del model
        else:
            raise ValueError(method)
        imp = back(Zimp)
    imp = np.where(np.isnan(Xte_m), imp, Xte_m)
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    res = dict(j, rmse=dc.rmse_at(Xte, imp, Mte), **info)
    if ds == "Siemens":
        k = ev.shifted_index(); M2 = Mte.copy(); M2[:, :, k] = False; res["rmse_wo_shifted"] = dc.rmse_at(Xte, imp, M2)
    return res


def run(worker=0, n_workers=1):
    if not os.path.exists(os.path.join(OUT, "PLAN_step2b.md")):
        sys.exit("Write and commit the plan first: python step2b_shrink.py plan")
    os.makedirs(os.path.join(OUT, "results"), exist_ok=True); os.makedirs(os.path.join(OUT, "errors"), exist_ok=True)
    dc, di, v2, ev = modules(); import torch
    jobs = [j for i, j in enumerate(job_list()) if i % n_workers == worker]
    for i, j in enumerate(jobs, 1):
        p = res_path(j)
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
            res["seconds"] = round(time.time() - t0, 1); tmp = p + ".tmp"
            json.dump(res, open(tmp, "w"), indent=1, default=float); os.replace(tmp, p)
    json.dump(dict(python=platform.python_version(), torch=torch.__version__, cuda=torch.version.cuda,
                   gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"),
              open(os.path.join(OUT, "environment.json"), "w"), indent=1)


def status():
    jobs = job_list(); done = sum(os.path.exists(res_path(j)) for j in jobs); errs = glob.glob(os.path.join(OUT, "errors", "*.txt"))
    print(f"finished {done} of {len(jobs)} jobs; errors: {len(errs)}")
    for e in errs[:5]: print("  ", open(e).read().splitlines()[0])


def lv_str(lv):
    lv = float(lv); return str(int(lv)) if lv.is_integer() else f"{lv:g}"


def report():
    rows = [json.load(open(p)) for p in glob.glob(os.path.join(OUT, "results", "*.json"))]
    if not rows: sys.exit("no results yet")
    d = pd.DataFrame(rows)
    d["cond"] = d.apply(lambda r: f'{r["dataset"]} {r["mech"]} {lv_str(r["level"])}', axis=1)
    d["label"] = d.apply(lambda r: r["method"] if r["norm"] in ("internal",) or r["method"] == "Linear regression" else f'{r["method"]}-{r["norm"]}', axis=1)
    L = ["# Step 2b report", "", f"Jobs finished: {len(d)} of {len(job_list())}", ""]
    metrics = [("rmse", "all variables"), ("rmse_wo_shifted", "without PI12002_PV_Out")]
    for col, name in metrics:
        if col not in d: continue
        piv = d.dropna(subset=[col]).groupby(["label", "cond"])[col].mean().unstack().round(4)
        L += [f"## Mean RMSE ({name})", "", "```", piv.to_string(), "```", ""]; piv.to_csv(os.path.join(OUT, f"step2b_mean_{col}.csv"))
    # H1
    cells = []
    for ds, mech, lv in CONDITIONS:
        c = f"{ds} {mech} {lv_str(lv)}"
        models = PLUGIN_MODELS + (ECG_ONLY if ds == "ECG200" else [])
        for col, name in (metrics if ds == "Siemens" else metrics[:1]):
            for mdl in models:
                mean = {n: d[(d.cond == c) & (d.label == f"{mdl}-{n}")][col].mean() for n in NORMS}
                if any(np.isnan(v) for v in mean.values()): continue
                ref = min(mean["global"], mean["seq"]); ratio = mean["shrink"] / ref
                cells.append(dict(condition=c, metric=name, model=mdl, global_=mean["global"], seq=mean["seq"], shrink=mean["shrink"],
                                  ratio=ratio, ok=ratio <= NO_HARM, better=ratio < 1 / NO_HARM))
    h = pd.DataFrame(cells)
    if len(h):
        share = h.ok.mean(); h1 = share >= NO_HARM_SHARE
        L += ["## H1 - revised shrink normalization versus the better of global and seq", "",
              "| condition | metric | model | global | seq | shrink | shrink / min(global, seq) | within 2% |", "|---|---|---|---|---|---|---|---|"]
        for r in h.itertuples():
            L.append(f"| {r.condition} | {r.metric} | {r.model} | {r.global_:.4f} | {r.seq:.4f} | {r.shrink:.4f} | {r.ratio:.3f} | {'yes' if r.ok else 'no'} |")
        L += ["", f"cells within 2%: {int(h.ok.sum())} of {len(h)} ({share:.0%}); cells more than 2% better than both: {int(h.better.sum())}",
              f"**H1 {'supported' if h1 else 'not supported'}**", ""]
        h.to_csv(os.path.join(OUT, "step2b_h1_cells.csv"), index=False)
    # shrink weights
    if "w_mean" in d:
        wt = d.dropna(subset=["w_mean"]).groupby("cond")[["w_mean", "wl_mean"]].mean().round(3)
        L += ["## Mean shrinkage weights on the test inputs (w: location, w_l: scale)", "", "```", wt.to_string(), "```", ""]
    if "zin_max" in d:
        zt = d.groupby(["cond", "norm"])[["zin_p999", "zin_max"]].max().round(1).unstack()
        L += ["## Normalized test inputs: 99.9th percentile and maximum of |z| (largest over models and seeds)", "", "```", zt.to_string(), "```", ""]
    if len(h):
        L += ["## Decision according to the plan", "",
              "H1 supported: the revised normalization is carried to Step 3 unchanged." if h1 else
              "H1 not supported: no further revision; the study is framed as an analysis of normalization under missingness.", ""]
    nd = int((~d["deterministic"].astype(bool)).sum()) if "deterministic" in d else 0
    L += [f"Jobs run without strict determinism: {nd}"]
    txt = "\n".join(L); open(os.path.join(OUT, "REPORT_step2b.md"), "w", encoding="utf-8").write(txt)
    d.to_csv(os.path.join(OUT, "step2b_all_runs.csv"), index=False); print(txt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["plan", "run", "status", "report"])
    ap.add_argument("--worker", type=int, default=0); ap.add_argument("--n-workers", type=int, default=1)
    a = ap.parse_args()
    if a.cmd == "plan":
        os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, "PLAN_step2b.md")
        if os.path.exists(p): sys.exit(f"{p} already exists; it must not be changed after results exist")
        open(p, "w", encoding="utf-8").write(PLAN + f"\nWritten: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(open(p, encoding="utf-8").read()); print("SHA-256:", hashlib.sha256(open(p, "rb").read()).hexdigest())
    elif a.cmd == "run": run(a.worker, a.n_workers)
    elif a.cmd == "status": status()
    else: report()
