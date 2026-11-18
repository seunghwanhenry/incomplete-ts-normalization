"""
step6_controls.py - Step 6: controls for the Step 5 result (pre-specified before any Step 6 result).

Question: is the gain of dual normalization (Step 5) more than the gain of combining any two trained imputers?
  * Seed-ensemble control (new training): SAITS and the DTIN transformer are trained once more with each normalization
    and a different model seed (G', S'). The pairs G+G' and S+S' are combined with exactly the same validation-weight
    procedure as dual normalization (G+S). Same training cost as dual normalization.
  * Ablations (no new training, from the Step 5 predictions): equal weights, one pooled weight, per-variable selection,
    no window guard.
  * KNN is deterministic, so its Step 5 gain cannot come from seed diversity (reported as such).
Uses the Step 5 data, splits, masks and predictions (step5_outputs); step5_confirm.py must be in the same folder.

Commands:
  python step6_controls.py plan      # writes step6_outputs/PLAN_step6.md -> commit it before running
  python step6_controls.py run [--worker k --n-workers K]
  python step6_controls.py status
  python step6_controls.py report
"""
import argparse, glob, hashlib, importlib.util, json, os, platform, sys, time, traceback
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("s5", os.path.join(HERE, "step5_confirm.py"))
s5 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(s5)

OUT = "step6_outputs"
MODELS6 = ["SAITS", "Transformer"]
NORMS = ["global", "seq"]
SUPERIOR_CELLS, NONINF, NONINF_SHARE = 12, 1.02, 0.90


def script_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


PLAN = """# Step 6 - controls for dual normalization (pre-specified)

Written after the Step 5 report and before any Step 6 run. Script step6_controls.py, SHA-256 {sha};
step5_confirm.py SHA-256 {sha5}.

## Why
In Step 5 (pre-registered) dual normalization was better than both single normalizations in all 24 cells. Combining
two trained imputers can reduce error by itself (ensemble effect). This step asks whether combining two normalizations
is better than combining two seeds of the same normalization at the same training cost.

## Runs
* Data, splits, masks, conditions and seeds 0-9 of Step 5 (C-MAPSS FD001+FD003, MetroPT-3).
* SAITS and the DTIN transformer are trained once more with global and with seq normalization, with a second model
  seed (G', S'); everything else as in Step 5.
* Ensembles: G+G' and S+S' combined with the Step 5 procedure (per-variable convex weight estimated on the
  early-stopping windows; no window guard, which only applies when the two members differ in normalization).
* Dual normalization: the Step 5 predictions (G+S with the window guard), unchanged.

## Hypotheses (cells = dataset x condition x model = 16; mean RMSE over seeds)
* H4 (superiority): dual < min(ensemble G+G', ensemble S+S') in at least {sc} of 16 cells.
* H5 (non-inferiority): dual <= {ni} x min(ensemble G+G', ensemble S+S') in at least {ns:.0%} of the 16 cells.
* Reported descriptively: geometric-mean ratios; per-seed comparisons; ablations of dual normalization on the Step 5
  predictions for all three models (equal weights 0.5, one pooled weight, per-variable selection, no guard); training
  time of each member.
"""


def job_list():
    jobs = []
    for ds in s5.DATASETS:
        for mech, lv in s5.CONDITIONS:
            for seed in s5.SEEDS:
                for mdl in MODELS6:
                    for norm in NORMS:
                        jobs.append(dict(dataset=ds, mech=mech, level=lv, seed=seed, method=mdl, norm=norm, member="second"))
    for j in jobs:
        j["id"] = f'{j["dataset"]}|{j["mech"]}|{j["level"]}|{j["seed"]}|{j["method"]}|{j["norm"]}|second'
    return jobs


def res_path(j, ext):
    return os.path.join(OUT, "results", hashlib.md5(j["id"].encode()).hexdigest() + ext)


def run_job(j, dc, v2, ev):
    """as step5_confirm.run_job, with a second model seed"""
    import torch
    ds, mech, lv, seed, method, norm = j["dataset"], j["mech"], j["level"], j["seed"], j["method"], j["norm"]
    S = s5.setting(dc, ds, seed); Xa, Xte, tr, st = S["Xa"], S["Xte"], S["tr"], S["st"]
    Mtr, Mte = s5.masks(dc, ds, S, mech, lv, seed)
    Xtr_m, Xte_m = dc.apply_mask(Xa, Mtr), dc.apply_mask(Xte, Mte); Xst_m = Xtr_m[st]
    s = s5.sseed("step6-init", ds, mech, lv, seed, method); info = {}
    if norm == "global":
        Ztr, Zte, Zst_true, Zst_m = Xtr_m, Xte_m, Xa[st], Xst_m
        back_te = back_st = (lambda Z: Z)
    else:
        (mtr, s_tr), (mte, s_te), (mst, s_st) = s5.seq_stats(Xtr_m), s5.seq_stats(Xte_m), s5.seq_stats(Xst_m)
        Ztr, Zte, Zst_true, Zst_m = (Xtr_m - mtr) / s_tr, (Xte_m - mte) / s_te, (Xa[st] - mst) / s_st, (Xst_m - mst) / s_st
        back_te = lambda Z: Z * s_te + mte; back_st = lambda Z: Z * s_st + mst
    if method == "SAITS":
        Zall, val = ev.pypots_fit_impute("SAITS", ev.select_saits()["cfg"], Ztr[tr], Zst_true, Mtr[st], np.concatenate([Zte, Zst_m]), s)
        Zte_i, Zst_i = Zall[:len(Zte)], Zall[len(Zte):]; info["val_stop_rmse_model_space"] = val
    else:
        model = v2.DTINv2Imputer(v2.imputation_config(**s5.TRANSFORMER), seed=s).fit(Ztr[tr], Zst_true, Mtr[st])
        Zte_i, Zst_i = model.impute(Zte), model.impute(Zst_m); del model
    imp_te, imp_st = back_te(Zte_i), back_st(Zst_i)
    imp_te = np.where(np.isnan(Xte_m), imp_te, Xte_m); imp_st = np.where(np.isnan(Xst_m), imp_st, Xst_m)
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    np.savez_compressed(res_path(j, ".npz"), te=imp_te[Mte].astype(np.float32), st=imp_st[Mtr[st]].astype(np.float32))
    return dict(j, rmse=dc.rmse_at(Xte, imp_te, Mte), **info)


def run(worker=0, n_workers=1):
    if not os.path.exists(os.path.join(OUT, "PLAN_step6.md")): sys.exit("Write the plan first: python step6_controls.py plan")
    os.makedirs(os.path.join(OUT, "results"), exist_ok=True); os.makedirs(os.path.join(OUT, "errors"), exist_ok=True)
    dc, v2, ev = s5.modules(); import torch; sha = script_sha()
    jobs = [j for i, j in enumerate(job_list()) if i % n_workers == worker]
    for i, j in enumerate(jobs, 1):
        p = res_path(j, ".json")
        if os.path.exists(p): continue
        print(f"[{i}/{len(jobs)}] {j['id']}", flush=True); t0 = time.time(); res = None
        for strict in (True, False):
            s5.strict_mode(strict)
            try:
                res = run_job(j, dc, v2, ev); res["deterministic"] = strict; break
            except RuntimeError as e:
                if strict and "deterministic" in str(e).lower(): continue
                open(os.path.join(OUT, "errors", os.path.basename(p) + ".txt"), "w").write(j["id"] + "\n" + traceback.format_exc()); break
            except Exception:
                open(os.path.join(OUT, "errors", os.path.basename(p) + ".txt"), "w").write(j["id"] + "\n" + traceback.format_exc()); break
        if res is not None:
            res.update(seconds=round(time.time() - t0, 1), script_sha256=sha); tmp = p + ".tmp"
            json.dump(res, open(tmp, "w"), indent=1, default=float); os.replace(tmp, p)
    json.dump(dict(python=platform.python_version(), torch=torch.__version__,
                   gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"),
              open(os.path.join(OUT, "environment.json"), "w"), indent=1)


def status():
    jobs = job_list(); done = sum(os.path.exists(res_path(j, ".json")) for j in jobs)
    errs = glob.glob(os.path.join(OUT, "errors", "*.txt"))
    print(f"finished {done} of {len(jobs)} jobs; errors: {len(errs)}")
    for e in errs[:5]: print("  ", open(e).read().splitlines()[0])


def combine(a_d, d, first, second, guard_n=None):
    a = a_d[d] if guard_n is None else np.where(guard_n, 0.0, a_d[d])
    return a * first + (1 - a) * second


def report():
    dc, _, _ = s5.modules()
    j5 = {j["id"]: j for j in s5.job_list()}; j6 = {j["id"]: j for j in job_list()}
    rows = []
    for ds in s5.DATASETS:
        for mech, lv in s5.CONDITIONS:
            cond = f"{mech} {lv:g}"
            for seed in s5.SEEDS:
                S = s5.setting(dc, ds, seed); Mtr, Mte = s5.masks(dc, ds, S, mech, lv, seed)
                Xtr_m, Xte_m = dc.apply_mask(S["Xa"], Mtr), dc.apply_mask(S["Xte"], Mte)
                y = S["Xte"][Mte]; _, _, d = np.nonzero(Mte); n = np.nonzero(Mte)[0]
                ys = S["Xa"][S["st"]][Mtr[S["st"]]]; _, _, d_st = np.nonzero(Mtr[S["st"]]); D = S["Xa"].shape[2]
                guard = s5.window_guard(Xtr_m[S["tr"]], Xte_m)[n]
                def ld(paths, key):
                    p = paths
                    return np.load(p) if os.path.exists(p) else None
                def r5(m, nm): return ld(s5.res_path(j5[f"{ds}|{mech}|{lv}|{seed}|{m}|{nm}"], ".npz"), None)
                def r6(m, nm): return ld(res_path(j6[f"{ds}|{mech}|{lv}|{seed}|{m}|{nm}|second"], ".npz"), None)
                def add(model, variant, pred):
                    rows.append(dict(dataset=ds, cond=cond, seed=seed, model=model, variant=variant, rmse=float(np.sqrt(((pred - y) ** 2).mean()))))
                for mdl in s5.MODELS:
                    G, Sq = r5(mdl, "global"), r5(mdl, "seq")
                    if G is None or Sq is None: continue
                    g, s_, gs, ss = G["te"].astype(float), Sq["te"].astype(float), G["st"].astype(float), Sq["st"].astype(float)
                    a = s5.dual_weights(ys, gs, ss, d_st, D)
                    add(mdl, "global", g); add(mdl, "seq", s_)
                    add(mdl, "dual", combine(a, d, g, s_, guard))
                    add(mdl, "abl_no_guard", combine(a, d, g, s_))
                    add(mdl, "abl_equal", combine(np.full(D, 0.5), d, g, s_, guard))
                    eg, es = gs - ys, ss - ys
                    Eg, Es, C = (eg * eg).mean(), (es * es).mean(), (eg * es).mean(); den = Eg + Es - 2 * C
                    ap = 0.5 if den <= 1e-12 else float(np.clip((Es - C) / den, 0, 1))
                    add(mdl, "abl_pooled", combine(np.full(D, ap), d, g, s_, guard))
                    sel = np.array([float(((eg[d_st == k]) ** 2).mean() < ((es[d_st == k]) ** 2).mean()) if (d_st == k).any() else float(Eg < Es) for k in range(D)])
                    add(mdl, "abl_select", combine(sel, d, g, s_, guard))
                    if mdl in MODELS6:
                        G2, S2 = r6(mdl, "global"), r6(mdl, "seq")
                        if G2 is not None:
                            g2, g2s = G2["te"].astype(float), G2["st"].astype(float)
                            add(mdl, "global_seed2", g2); add(mdl, "ens_global", combine(s5.dual_weights(ys, gs, g2s, d_st, D), d, g, g2))
                        if S2 is not None:
                            s2, s2s = S2["te"].astype(float), S2["st"].astype(float)
                            add(mdl, "seq_seed2", s2); add(mdl, "ens_seq", combine(s5.dual_weights(ys, ss, s2s, d_st, D), d, s_, s2))
    r = pd.DataFrame(rows)
    if r.empty: sys.exit("no results")
    m = r.groupby(["dataset", "cond", "model", "variant"]).rmse.mean().unstack()
    gm = lambda x: float(np.exp(np.log(np.asarray(x, float)).mean()))
    L = ["# Step 6 report (controls)", ""]
    h = m.loc[m.index.get_level_values("model").isin(MODELS6), ["dual", "ens_global", "ens_seq", "global", "seq"]].dropna()
    complete = len(h) == 16
    if len(h):
        h = h.assign(best_ens=h[["ens_global", "ens_seq"]].min(axis=1)); h["ratio"] = h.dual / h.best_ens
        n_sup, n_ni = int((h.ratio < 1).sum()), int((h.ratio <= NONINF).sum())
        v = lambda ok: ("supported" if ok else "not supported") if complete else f"no decision yet ({len(h)} of 16 cells)"
        L += ["## Dual normalization versus seed ensembles of one normalization (same training cost)", "", "```", h.round(4).to_string(), "```", "",
              f"* H4: dual < better seed ensemble in {n_sup} of {len(h)} cells (rule: at least {SUPERIOR_CELLS}) -> **{v(n_sup >= SUPERIOR_CELLS)}**",
              f"* H5: dual <= {NONINF} x better seed ensemble in {n_ni} of {len(h)} cells (rule: at least {NONINF_SHARE:.0%}) -> **{v(n_ni >= NONINF_SHARE * 16)}**",
              f"* geometric mean dual / better seed ensemble = {gm(h.ratio):.3f}; dual / ensemble of global = {gm(h.dual / h.ens_global):.3f}; "
              f"dual / ensemble of seq = {gm(h.dual / h.ens_seq):.3f}", ""]
        p = r[r.model.isin(MODELS6)].pivot_table(index=["dataset", "cond", "model", "seed"], columns="variant", values="rmse")
        if {"ens_global", "ens_seq"} <= set(p.columns):
            q = p.dual / p[["ens_global", "ens_seq"]].min(axis=1)
            L += [f"Seed level: dual below the better seed ensemble in {(q < 1).mean():.0%} of {len(q.dropna())} seed-cells.", ""]
    ab = ["dual", "abl_no_guard", "abl_equal", "abl_pooled", "abl_select"]
    a = m[ab].div(m[["global", "seq"]].min(axis=1), axis=0)
    L += ["## Ablations on the Step 5 predictions: ratio to the better single normalization", "", "```", a.round(3).to_string(), "```", "",
          "Geometric means: " + ", ".join(f"{c} {gm(a[c]):.3f}" for c in ab), ""]
    jr = [json.load(open(q)) for q in glob.glob(os.path.join(s5.OUT, "results", "*.json"))]
    if jr:
        t = pd.DataFrame(jr); t = t[t.method != "Linear regression"]
        L += ["## Training and imputation time per member (seconds, Step 5 runs, median)", "", "```",
              t.groupby(["dataset", "method", "norm"]).seconds.median().unstack().round(0).to_string(), "```", ""]
    jr6 = [json.load(open(q)) for q in glob.glob(os.path.join(OUT, "results", "*.json"))]
    if jr6: L += [f"Step 6 runs without strict determinism: {int((~pd.DataFrame(jr6).deterministic.astype(bool)).sum())}"]
    txt = "\n".join(L); open(os.path.join(OUT, "REPORT_step6.md"), "w", encoding="utf-8").write(txt)
    r.to_csv(os.path.join(OUT, "step6_runs.csv"), index=False); print(txt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["plan", "run", "status", "report"])
    ap.add_argument("--worker", type=int, default=0); ap.add_argument("--n-workers", type=int, default=1)
    a = ap.parse_args()
    if a.cmd == "plan":
        os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, "PLAN_step6.md")
        if os.path.exists(p): sys.exit(f"{p} already exists")
        sha5 = hashlib.sha256(open(os.path.join(HERE, "step5_confirm.py"), "rb").read()).hexdigest()
        open(p, "w", encoding="utf-8").write(PLAN.format(sha=script_sha(), sha5=sha5, sc=SUPERIOR_CELLS, ni=NONINF, ns=NONINF_SHARE)
                                             + f"\nWritten: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(open(p, encoding="utf-8").read())
    elif a.cmd == "run": run(a.worker, a.n_workers)
    elif a.cmd == "status": status()
    else: report()
