"""
step2_shrink.py - Step 2 of the follow-up study: reliability-weighted (shrinkage) normalization.

H1: shrinkage of per-sequence normalization statistics towards training statistics, weighted by their
    reliability, is never clearly worse than the better of global and per-sequence normalization, for several
    imputation models (model-agnostic plug-in).
H2: the advantage of the transformer on structured missingness comes from mixed point/span masking in training.

Siemens and ECG200 (including their former test splits) are DEVELOPMENT data; nothing here is independent evidence.

  python step2_shrink.py plan                              # write step2_outputs/PLAN_step2.md -> commit it first
  python step2_shrink.py run [--worker k --n-workers K]    # resumable
  python step2_shrink.py status
  python step2_shrink.py report
"""
import argparse, glob, hashlib, json, os, platform, sys, time, traceback
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import numpy as np
import pandas as pd

OUT = "step2_outputs"
EPS = 1e-5
SEEDS = [0, 1, 2, 3, 4]
CONDITIONS = [("Siemens", "MCAR", 0.3), ("Siemens", "MAR", 0.3), ("Siemens", "MNAR", 0.3), ("Siemens", "GAP", 30),
              ("Siemens", "MCAR", 0.7), ("ECG200", "MCAR", 0.3), ("ECG200", "MCAR", 0.7)]
NORMS = ["global", "seq", "shrink"]
PLUGIN_MODELS = ["SAITS", "KNN", "Transformer"]        # every normalization, every condition
ECG_ONLY = ["BRITS"]                                   # every normalization, ECG200 only (cost on Siemens)
TRANSFORMER = dict(revin=False, mask_input=True, mask_mode="mix")       # DTIN backbone, external normalization
TRANSFORMER_POINT = dict(revin=False, mask_input=True, mask_mode="point")
NO_HARM = 1.02            # H1: shrink <= 1.02 x min(global, seq)
NO_HARM_SHARE = 0.90      # ... in at least 90 % of the cells
H2_GAIN = 0.03            # H2: mix at least 3 % lower than point, in >= 4 of 5 seeds

PLAN = f"""# Step 2 - reliability-weighted normalization (pre-specified)

Written before any Step 2 result was computed. Commit this file (with its date) before running the jobs.

## Background (Step 1, development data)
Per-sequence normalization of the visible values reduced the RMSE of every model on Siemens (mostly through the
variable PI12002_PV_Out, whose test variance is 10.9 times its training variance) and increased it on ECG200,
whose series are already z-normalized (every series has mean 0 and standard deviation 1). Normalization with
statistics of the observed entries only has been proposed for forecasting with missing values (mask-aware
normalization, Timeflies, arXiv 2606.13571); it is the "seq" option here.

## Method fixed now (no tuning parameter)
For variable d, from the masked training sequences: global mean mu, pooled within-sequence variance sigma2, lag-1
autocorrelation rho, between-sequence variance of the sequence means tau2 and of the log standard deviations
tau2_l (method of moments, sampling variance removed). For a sequence with c visible values,
n_eff = max(1, c (1 - rho) / (1 + rho)),
m* = w m_seq + (1 - w) mu with w = tau2 / (tau2 + sigma2 / n_eff) (w = 0 if c = 0),
log s* = w_l log s_seq + (1 - w_l) lam with w_l = tau2_l / (tau2_l + 1 / (2 (n_eff - 1))) (w_l = 0 if c < 2),
where lam is the mean training log standard deviation and s_seq = sqrt(var + {EPS}).

## Design
* Conditions: Siemens MCAR 30%, MAR 30%, MNAR 30%, consecutive gaps of length 30, MCAR 70%;
  ECG200 MCAR 30%, MCAR 70%. Seeds {SEEDS}. Same splits and masks as in Step 1.
* Normalizations (applied outside the model, identical for every model): global (none beyond the global
  standardization), seq (per-sequence statistics of the visible values), shrink (above). Validation targets are
  normalized with the statistics of the masked validation inputs.
* Models: SAITS, KNN and the transformer of DTIN (mask input, mixed masking, internal normalization off) with all
  three normalizations in every condition; BRITS with all three normalizations on ECG200 only (one BRITS job on
  Siemens took 2.4-3.1 h in Step 1; BRITS is included in Step 3). References: linear regression; DTIN-v2 with its
  internal per-sequence normalization; the transformer with point masking only and shrink normalization (H2).
* Fixed settings as in Step 1 (SAITS configuration selected earlier on development data, BRITS hidden 64, KNN k = 5,
  final DTIN-v2 training settings). No tuning.
* Metrics: RMSE at removed positions; on Siemens also without PI12002_PV_Out.

## Decision rules (fixed now)
Cells: every (model, condition, metric) with model in {{SAITS, KNN, Transformer}} for all conditions and BRITS for
the ECG200 conditions; on Siemens both metrics, on ECG200 the RMSE. ref = min(mean RMSE global, mean RMSE seq).
* H1 supported: mean RMSE shrink <= {NO_HARM} x ref in at least {int(NO_HARM_SHARE * 100)}% of the cells.
  Then shrink normalization is carried to Step 3 unchanged. Otherwise at most one revision on development data,
  documented with its reason; if H1 still fails, the follow-up study is framed as an analysis of normalization
  under missingness, without a new normalization method.
* Reported descriptively: cells in which shrink is more than 2% better than ref; the mean weights w and w_l.
* H2 supported: on Siemens GAP 30 and MNAR 30 (both metrics, 4 cells), the transformer with mixed masking has a
  mean RMSE at least {int(H2_GAIN * 100)}% lower than with point masking and is lower in at least 4 of 5 seeds,
  in at least 3 of the 4 cells.
"""


def _basic(X_nan):
    v = ~np.isnan(X_nan); c = v.sum(1).astype(float)                    # (N, D)
    x = np.nan_to_num(X_nan)
    m = (x * v).sum(1) / np.maximum(c, 1)
    var = (((x - m[:, None, :]) * v) ** 2).sum(1) / np.maximum(c, 1)
    return v, c, x, m, var

class ShrinkNorm:
    """Reliability-weighted (empirical-Bayes) shrinkage of per-sequence normalization statistics.

    Location: m* = w m_seq + (1 - w) mu,  w = tau2 / (tau2 + sigma2 / n_eff)
    Scale (log): l* = w_l l_seq + (1 - w_l) lam,  w_l = tau2_l / (tau2_l + 1 / (2 (n_eff - 1)))
    tau2, tau2_l: between-sequence variances of the means / log-scales (method of moments, training data);
    n_eff = c (1 - rho) / (1 + rho): effective number of visible values under lag-1 autocorrelation rho.
    """
    def fit(self, X_nan):
        v, c, x, m, var = _basic(X_nan)
        d = x - m[:, None, :]
        pair = v[:, 1:, :] & v[:, :-1, :]
        num = (d[:, 1:, :] * d[:, :-1, :] * pair).sum((0, 1)) / np.maximum(pair.sum((0, 1)), 1)
        den = ((d ** 2) * v).sum((0, 1)) / np.maximum(v.sum((0, 1)), 1)
        self.rho = np.clip(num / np.maximum(den, 1e-12), 0.0, 0.99)
        neff = self._neff(c)
        ok = c >= 2
        wts = np.where(ok, c, 0.0)
        self.sig2 = (var * wts).sum(0) / np.maximum(wts.sum(0), 1)
        self.mu = (m * c).sum(0) / np.maximum(c.sum(0), 1)
        samp = self.sig2 / neff
        mm = np.where(ok, m, np.nan)
        self.tau2 = np.maximum(0.0, np.nan_to_num(np.nanvar(mm, 0)) - np.nan_to_num(np.nanmean(np.where(ok, samp, np.nan), 0)))
        l = np.where(ok, 0.5 * np.log(var + EPS), np.nan)
        samp_l = np.where(ok, 1.0 / (2.0 * np.maximum(neff - 1.0, 1.0)), np.nan)
        self.lam = np.nan_to_num(np.nanmean(l, 0))
        self.tau2_l = np.maximum(0.0, np.nan_to_num(np.nanvar(l, 0)) - np.nan_to_num(np.nanmean(samp_l, 0)))
        return self

    def _neff(self, c):
        return np.clip(c * (1 - self.rho) / (1 + self.rho), 1.0, None)

    def stats(self, X_nan):
        v, c, x, m, var = _basic(X_nan)
        neff = self._neff(c)
        w = self.tau2 / (self.tau2 + self.sig2 / neff + 1e-12); w = np.where(c > 0, w, 0.0)
        ms = w * m + (1 - w) * self.mu
        wl = self.tau2_l / (self.tau2_l + 1.0 / (2.0 * np.maximum(neff - 1.0, 1.0)) + 1e-12); wl = np.where(c >= 2, wl, 0.0)
        ls = wl * 0.5 * np.log(var + EPS) + (1 - wl) * self.lam
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
            add("Linear regression", "global"); add("DTIN-v2", "internal"); add("Transformer-point", "shrink")
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
    s = dc.stable_seed("step2", ds, mech, lv, seed, method, norm); info = {}
    if method == "Linear regression":
        imp = dc.impute_lr_time(Xte_m)
    elif method == "DTIN-v2":
        model = v2.DTINv2Imputer(v2.imputation_config(), seed=s).fit(Xtr_m[tr], Xtr[st], Mtr[st]); imp = model.impute(Xte_m); del model
    else:
        Xst_m = Xtr_m[st]
        if norm == "global":
            Ztr, Zte, Zst = Xtr_m, Xte_m, Xtr[st]; back = lambda Z: Z
        else:
            if norm == "seq":
                f = seq_stats
            else:
                sn = ShrinkNorm().fit(Xtr_m)
                f = lambda X: sn.stats(X)[:2]
                _, _, w, wl = sn.stats(Xte_m)
                info.update(w_mean=float(w.mean()), wl_mean=float(wl.mean()), rho_mean=float(sn.rho.mean()))
            (mtr, s_tr), (mte, s_te), (mst, s_st) = f(Xtr_m), f(Xte_m), f(Xst_m)
            Ztr, Zte, Zst = (Xtr_m - mtr) / s_tr, (Xte_m - mte) / s_te, (Xtr[st] - mst) / s_st
            back = lambda Z: Z * s_te + mte
        if method == "KNN":
            Zimp = dc.impute_knn(Ztr, Zte, dc.CFG["knn_k"])
        elif method in ("SAITS", "BRITS"):
            hp = ev.select_saits()["cfg"] if method == "SAITS" else ev.BASE_DEFAULT[method]
            Zimp, val = ev.pypots_fit_impute(method, hp, Ztr[tr], Zst, Mtr[st], Zte, s); info["val_stop_rmse_model_space"] = val
        elif method in ("Transformer", "Transformer-point"):
            cfg = v2.imputation_config(**(TRANSFORMER if method == "Transformer" else TRANSFORMER_POINT))
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
    if not os.path.exists(os.path.join(OUT, "PLAN_step2.md")):
        sys.exit("Write and commit the plan first: python step2_shrink.py plan")
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
    L = ["# Step 2 report", "", f"Jobs finished: {len(d)} of {len(job_list())}", ""]
    metrics = [("rmse", "all variables"), ("rmse_wo_shifted", "without PI12002_PV_Out")]
    for col, name in metrics:
        if col not in d: continue
        piv = d.dropna(subset=[col]).groupby(["label", "cond"])[col].mean().unstack().round(4)
        L += [f"## Mean RMSE ({name})", "", "```", piv.to_string(), "```", ""]; piv.to_csv(os.path.join(OUT, f"step2_mean_{col}.csv"))
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
        L += ["## H1 - shrink normalization versus the better of global and seq", "",
              "| condition | metric | model | global | seq | shrink | shrink / min(global, seq) | within 2% |", "|---|---|---|---|---|---|---|---|"]
        for r in h.itertuples():
            L.append(f"| {r.condition} | {r.metric} | {r.model} | {r.global_:.4f} | {r.seq:.4f} | {r.shrink:.4f} | {r.ratio:.3f} | {'yes' if r.ok else 'no'} |")
        L += ["", f"cells within 2%: {int(h.ok.sum())} of {len(h)} ({share:.0%}); cells more than 2% better than both: {int(h.better.sum())}",
              f"**H1 {'supported' if h1 else 'not supported'}**", ""]
        h.to_csv(os.path.join(OUT, "step2_h1_cells.csv"), index=False)
    # shrink weights
    if "w_mean" in d:
        wt = d.dropna(subset=["w_mean"]).groupby("cond")[["w_mean", "wl_mean", "rho_mean"]].mean().round(3)
        L += ["## Mean shrinkage weights on the test inputs (w: location, w_l: scale)", "", "```", wt.to_string(), "```", ""]
    # H2
    h2 = []
    for c in ("Siemens GAP 30", "Siemens MNAR 0.3"):
        for col, name in metrics:
            a = d[(d.cond == c) & (d.label == "Transformer-shrink")].set_index("seed")[col]
            b = d[(d.cond == c) & (d.label == "Transformer-point-shrink")].set_index("seed")[col]
            k = sorted(set(a.index) & set(b.index))
            if not k: continue
            gain = (b[k].mean() - a[k].mean()) / b[k].mean(); wins = int((a[k] < b[k]).sum())
            h2.append(dict(c=c, m=name, gain=gain, wins=wins, n=len(k), ok=gain >= H2_GAIN and wins >= 4))
    if h2:
        L += ["## H2 - mixed versus point masking (transformer, shrink normalization)", "",
              "| condition | metric | RMSE reduction by mixed masking | mixed better | meets H2 |", "|---|---|---|---|---|"]
        L += [f"| {r['c']} | {r['m']} | {r['gain']:+.3f} | {r['wins']}/{r['n']} | {'yes' if r['ok'] else 'no'} |" for r in h2]
        L += ["", f"**H2 {'supported' if sum(r['ok'] for r in h2) >= 3 else 'not supported'}**", ""]
    nd = int((~d["deterministic"].astype(bool)).sum()) if "deterministic" in d else 0
    L += [f"Jobs run without strict determinism: {nd}"]
    txt = "\n".join(L); open(os.path.join(OUT, "REPORT_step2.md"), "w", encoding="utf-8").write(txt)
    d.to_csv(os.path.join(OUT, "step2_all_runs.csv"), index=False); print(txt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["plan", "run", "status", "report"])
    ap.add_argument("--worker", type=int, default=0); ap.add_argument("--n-workers", type=int, default=1)
    a = ap.parse_args()
    if a.cmd == "plan":
        os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, "PLAN_step2.md")
        if os.path.exists(p): sys.exit(f"{p} already exists; it must not be changed after results exist")
        open(p, "w", encoding="utf-8").write(PLAN + f"\nWritten: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(open(p, encoding="utf-8").read()); print("SHA-256:", hashlib.sha256(open(p, "rb").read()).hexdigest())
    elif a.cmd == "run": run(a.worker, a.n_workers)
    elif a.cmd == "status": status()
    else: report()
