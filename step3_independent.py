"""
step3_independent.py - Step 3 of the follow-up study: independent evaluation on data not used in development.

Datasets
  Motor      - industrial motors on pump duty at a manufacturing site (anonymized), installation to replacement,
               7 variables at 10-min intervals, 15 motor lives (data/motor_S/*.csv).
  Hydraulic  - UCI "Condition monitoring of hydraulic systems" (Helwig et al., 2015; CC BY 4.0), 2,205 cycles of 60 s,
               17 sensors (data/hydraulic/*.txt, downloaded with the `fetch` command).
The normalizations and models are frozen from Steps 1-2b (development data: Siemens, ECG200).

Commands (in this order):
  python step3_independent.py plan        # writes step3_outputs/PLAN_step3.md with the SHA-256 of this script
                                          # -> register the plan publicly (OSF or a public GitHub commit) first
  python step3_independent.py fetch       # downloads the UCI hydraulic data (73 MB) into data/hydraulic
  python step3_independent.py prepare     # builds the windows; prints structural counts only (no results)
  python step3_independent.py run [--worker k --n-workers K]      # resumable
  python step3_independent.py status
  python step3_independent.py report
"""
import argparse, glob, hashlib, json, os, platform, re, sys, time, traceback, zipfile
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import numpy as np
import pandas as pd

OUT = "step3_outputs"
MOTOR_DIR = os.path.join("data", "motor_S")
HYD_DIR = os.path.join("data", "hydraulic")
HYD_URL = "https://archive.ics.uci.edu/static/public/447/condition+monitoring+of+hydraulic+systems.zip"
EPS = 1e-5
SEEDS = list(range(10))
DATASETS = ["Motor", "Hydraulic"]
T_LEN = {"Motor": 144, "Hydraulic": 60}            # one day at 10-min intervals / one 60-s cycle at 1 Hz
GAP_L = {"Motor": 36, "Hydraulic": 12}             # 6 h / 12 s
GAP_FRAC = 0.4                                     # share of each variable removed in the GAP condition
CONDITIONS = [("MCAR", 0.3), ("MCAR", 0.7), ("MNAR", 0.3), ("GAP", 0.4)]
MODELS = ["KNN", "SAITS", "Transformer"]
NORMS = ["global", "seq", "shrink"]
TRANSFORMER = dict(revin=False, mask_input=True, mask_mode="mix")   # DTIN transformer, normalization outside the model
STAB_HOURS = 48                                    # excluded after installation (stabilization)
END_HOURS = 24                                     # excluded at the end: the replacement day (records end at 00:00 of replacement + 1 d)
EARLY_DAYS = 7                                     # early life: first 7 days after stabilization
LATE_DAYS = [3, 7, 14]                             # late life: last H days before the end of the record (replacement)
MOTOR_TEST, MOTOR_STOP = 5, 2                      # motors per split (the rest: training)
HYD_BLOCK, HYD_TEST, HYD_STOP = 25, 0.3, 0.1       # consecutive-cycle blocks and their shares
HYD_SENSORS = ["PS1", "PS2", "PS3", "PS4", "PS5", "PS6", "EPS1", "FS1", "FS2", "TS1", "TS2", "TS3", "TS4", "VS1", "CE", "CP", "SE"]
HYD_TARGETS = ["cooler", "valve", "pump_leakage", "accumulator"]
NO_HARM, NO_HARM_SHARE = 1.02, 0.90
H3_GAIN, H3_WINS = 0.03, 8
DOWN_MARGIN = 0.02


def script_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def sseed(*keys):
    return int(hashlib.sha256("|".join(map(str, keys)).encode()).hexdigest()[:8], 16)


PLAN = """# Step 3 - independent evaluation (pre-specified)

Written before the Step 3 datasets were used for any model or result. Register this file publicly (OSF registration or a
public GitHub commit) before running `fetch`, `prepare` and `run`. Script: step3_independent.py, SHA-256 {sha}.

## What was known about the data when this plan was written
* Motor: only structural information - 15 motor lives (installation to replacement; 28-113 days of records), 7 variables
  (DP_Current, BP_Current, Exh_Pressur, Exh_Temperature, Casing_Temperature, N2T, N2F) at 10-min intervals, 0.44% of
  the 10-min timestamps missing (gaps longer than 1 h almost only on the installation day; one gap of 74.5 h on days
  2-4 of one motor), records from 00:00 of the installation date to 00:00 of the day after the recorded replacement
  date, maintenance-event metadata whose times are reported to be inaccurate, and a stabilization period after
  installation. The data were analysed by the authors' group in 2022 (remaining-life
  models), and project slides showing raw trends of some motors were seen while this plan was prepared. No model or
  normalization was developed or tuned on these data.
* Hydraulic: only the public documentation (UCI dataset 447): 2,205 cycles of 60 s, 17 sensors at 1/10/100 Hz,
  four component conditions and a stable flag in profile.txt. The data files have not been opened.

## Frozen methods (from Steps 1-2b, development data Siemens and ECG200)
* Normalizations applied outside the model: global (training standardization only), seq (per-sequence mean and
  standard deviation of the visible values), shrink (revised reliability-weighted shrinkage of Step 2b, unchanged).
* Imputation models with the settings fixed in development, no tuning on Step 3 data: KNN (k = 5), SAITS (configuration
  selected on development data), the DTIN transformer (final DTIN-v2 imputation settings, mask input, mixed masking,
  internal normalization off); per-sequence linear regression on time as a reference. KNN uses the training and
  early-stopping windows as its reference set; SAITS and the transformer stop early on the early-stopping windows.
* BRITS is not included: one BRITS job took 2.4-3.1 h in Step 1. It may be added later only as a labelled post hoc check.

## Preprocessing (fixed now)
* Motor: per motor life, records from {stab} h after the first record (stabilization) to the start of the replacement
  day, i.e. the last {eh} h are excluded because they may contain the stop, the exchange and the start of the new
  motor; this point is the end of life. 10-min grid; non-overlapping windows of {tm} points (one day) counted from the
  end of stabilization; windows with a missing timestamp are dropped.
* Both datasets: global standardization with the statistics of the training and early-stopping windows of each split.
* Hydraulic: every sensor averaged to 1 Hz within the cycle (60 points; 100 Hz: means of 100 samples, 10 Hz: means of
  10); one window per cycle (60 x 17); all cycles used.

## Splits, conditions, seeds
* Seeds {seeds}. Each seed defines a different split, the masks and the model initialization (common to the three
  normalizations of a model).
* Motor: per seed, motors are permuted; {mt} test motors, {ms} motors for early stopping, the rest for training.
* Hydraulic: blocks of {hb} consecutive cycles; per seed, {ht:.0%} of the blocks for testing, {hs:.0%} for early
  stopping, the rest for training.
* Missingness, applied to training and test windows (same generators as in development): MCAR 30%, MCAR 70%,
  MNAR 30% (values above the 70th percentile of their variable removed with probability 0.6, the other values with
  the probability that gives 30% overall), consecutive gaps with
  {gf:.0%} of each variable removed (gap length {gm} points = 6 h for Motor, {gh} points = 12 s for Hydraulic).
* Imputation metric: RMSE at the removed positions (standardized scale).

## Downstream tasks (impute, then classify; the classifier is fixed and trained on complete training windows)
* Features per window: mean, standard deviation, minimum, maximum and last-minus-first of every variable;
  standardization + logistic regression (class-balanced, max_iter 2000); no tuning.
* Motor health state: early-life windows (ending within {ed} days after stabilization) versus late-life windows
  (starting within H days before the end of life), H in {ld}; all three reported; a window meeting both definitions
  is excluded. Metric: AUROC on the test motors' windows. The maintenance-event times are not used.
* Hydraulic condition diagnosis: cooler (3 classes), valve (4), internal pump leakage (3) and accumulator (4); metric:
  balanced accuracy,
  averaged over the four targets (each target also reported).
* Reference: the same classifier on the complete (unmasked) test windows.

## Hypotheses and decision rules
* H1' (primary): cells = dataset x model (KNN, SAITS, Transformer) x condition = 24; ref = min(mean RMSE global, mean RMSE
  seq). Supported if mean RMSE shrink <= {nh} x ref in at least {nhs:.0%} of the cells.
* H3 (secondary): cells = dataset x condition in (MNAR 30%, GAP) = 4. In a cell, the transformer with seq normalization
  is better than SAITS with seq normalization if its mean RMSE is at least {g3:.0%} lower and lower in at least {w3}
  of 10 seeds. Supported if this holds in at least 3 of 4 cells. Caveat recorded now: in development the transformer
  configuration was chosen from 24 candidates and SAITS from 4.
* Downstream no-harm (secondary): cells = dataset x model x condition x metric (Motor: AUROC for H = 3, 7, 14;
  Hydraulic: mean balanced accuracy). Supported if mean(shrink) >= max(mean(global), mean(seq)) - {dm} in at least
  {nhs:.0%} of the cells.
* Reported descriptively: the cost of choosing the worse of global and seq (ratio of their mean RMSE) per cell;
  seed-level paired comparisons; shrinkage weights; all cells, including those not meeting a rule.
"""


# ------------------------------------------------------------------------------------------- data
def load_motor():
    files = sorted(glob.glob(os.path.join(MOTOR_DIR, "*.csv")))
    W, meta, seen, cols = [], [], set(), None
    for f in files:
        m = re.match(r"(\d+)_([A-Za-z0-9]+)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv$", os.path.basename(f))
        if not m:
            continue                                   # skips copies such as "... - 복사본.csv"
        mid = int(m.group(1))
        if mid in seen:
            continue
        seen.add(mid)
        df = pd.read_csv(f, encoding="utf-8-sig")
        df["SAMP"] = pd.to_datetime(df["SAMP"])
        df = df.drop_duplicates("SAMP").sort_values("SAMP").set_index("SAMP")
        if cols is None: cols = list(df.columns)
        assert list(df.columns) == cols, (f, list(df.columns))
        t0, t1 = df.index.min(), df.index.max()
        stab = (t0 + pd.Timedelta(hours=STAB_HOURS)).ceil("10min")
        t_end = (t1 - pd.Timedelta(hours=END_HOURS)).floor("10min")     # end of life = start of the replacement day
        g = df.reindex(pd.date_range(stab, t_end, freq="10min", inclusive="left"))
        L = T_LEN["Motor"]
        for k in range(len(g) // L):
            w = g.iloc[k * L:(k + 1) * L]
            if w.isna().any().any():
                continue
            ws, we = w.index[0], w.index[-1]
            W.append(w.to_numpy(np.float64))
            meta.append(dict(unit=mid, name=m.group(2), group=m.group(2)[:4], start=str(ws),
                             days_end_from_stab=(we - stab).total_seconds() / 86400,
                             days_start_to_end=(t_end - ws).total_seconds() / 86400))
    if not W:
        raise SystemExit(f"no motor files found in {MOTOR_DIR}")
    return np.stack(W), pd.DataFrame(meta), cols


def find_hyd_file(name):
    hits = glob.glob(os.path.join(HYD_DIR, "**", f"{name}.txt"), recursive=True)
    if not hits:
        raise SystemExit(f"{name}.txt not found under {HYD_DIR}; run: python step3_independent.py fetch")
    return hits[0]


def load_hydraulic():
    arrs = []
    for s in HYD_SENSORS:
        a = pd.read_csv(find_hyd_file(s), sep=r"\s+", header=None).to_numpy(np.float64)
        n, w = a.shape
        assert w % T_LEN["Hydraulic"] == 0, (s, a.shape)
        arrs.append(a.reshape(n, T_LEN["Hydraulic"], w // T_LEN["Hydraulic"]).mean(axis=2))
    X = np.stack(arrs, axis=2)
    prof = pd.read_csv(find_hyd_file("profile"), sep=r"\s+", header=None).to_numpy()
    assert prof.shape[0] == X.shape[0] and prof.shape[1] >= 5, prof.shape
    meta = pd.DataFrame(dict(unit=np.arange(len(X)), block=np.arange(len(X)) // HYD_BLOCK))
    for i, t in enumerate(HYD_TARGETS):
        meta[t] = prof[:, i]
    meta["stable_flag"] = prof[:, 4]
    return X, meta, HYD_SENSORS


def cache_path(ds):
    return os.path.join(OUT, "cache", f"{ds}.npz"), os.path.join(OUT, "cache", f"{ds}_windows.csv")


def prepare():
    os.makedirs(os.path.join(OUT, "cache"), exist_ok=True)
    for ds, f in (("Motor", load_motor), ("Hydraulic", load_hydraulic)):
        X, meta, cols = f()
        p, q = cache_path(ds)
        np.savez_compressed(p, X=X, cols=np.array(cols)); meta.to_csv(q, index=False)
        print(f"{ds}: windows {X.shape[0]}, length {X.shape[1]}, variables {X.shape[2]}, units {meta.unit.nunique()}, "
              f"non-finite values {int((~np.isfinite(X)).sum())}")
        if ds == "Motor":
            print("   windows per motor:", meta.groupby("unit").size().to_dict())
            print("   groups:", meta.groupby("group").unit.nunique().to_dict())
            for H in LATE_DAYS:
                e, l = early_late(meta, H)
                print(f"   early-life windows {int(e.sum())}, late-life windows (H = {H} d) {int(l.sum())}")
        else:
            print("   blocks:", meta.block.nunique(), "| stable flag = 0:", int((meta.stable_flag == 0).sum()))


def load_cache(ds):
    p, q = cache_path(ds)
    if not os.path.exists(p):
        raise SystemExit("run first: python step3_independent.py prepare")
    return np.load(p)["X"], pd.read_csv(q)


def early_late(meta, H):
    early = meta.days_end_from_stab.to_numpy() <= EARLY_DAYS
    late = meta.days_start_to_end.to_numpy() <= H
    both = early & late
    return early & ~both, late & ~both


def split_idx(ds, meta, seed):
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


# ------------------------------------------------------------------------------------------- normalization (frozen, Step 2b)
def _basic(X_nan):
    v = ~np.isnan(X_nan); c = v.sum(1).astype(float); x = np.nan_to_num(X_nan)
    m = (x * v).sum(1) / np.maximum(c, 1)
    var = (((x - m[:, None, :]) * v) ** 2).sum(1) / np.maximum(c, 1)
    return v, c, x, m, var


class ShrinkNormV2:
    """Step 2b: sequence-specific sampling variance of the visible-value mean (finite-population correction),
    normal-theory sampling variance of the log standard deviation, out-of-training-range rule."""
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
        nm = lambda a: np.nan_to_num(np.nanmean(np.where(ok, a, np.nan), 0))
        nv = lambda a: np.nan_to_num(np.nanvar(np.where(ok, a, np.nan), 0))
        self.tau2 = np.maximum(0.0, nv(m) - nm(self._sv_mean(c, var, T)))
        l = 0.5 * np.log(var + EPS)
        self.lam = nm(l); self.tau2_l = np.maximum(0.0, nv(l) - nm(self._sv_log(c, T)))
        self.l_lo = np.where(ok, l, np.inf).min(0); self.l_hi = np.where(ok, l, -np.inf).max(0)
        return self

    def stats(self, X_nan):
        v, c, x, m, var = _basic(X_nan); T = X_nan.shape[1]
        sv = self._sv_mean(c, var, T)
        w = np.where(sv > 0, self.tau2 / (self.tau2 + sv + 1e-300), 1.0); w = np.where(c > 0, w, 0.0)
        svl = self._sv_log(c, T)
        wl = np.where(svl > 0, self.tau2_l / (self.tau2_l + svl + 1e-300), 1.0); wl = np.where(c >= 2, wl, 0.0)
        l_seq = 0.5 * np.log(var + EPS)
        out = (c >= 2) & ((l_seq > self.l_hi) | (l_seq < self.l_lo))
        w = np.where(out, 1.0, w); wl = np.where(out, 1.0, wl)
        ms = w * m + (1 - w) * self.mu
        ls = wl * l_seq + (1 - wl) * self.lam
        return ms[:, None, :], np.exp(ls)[:, None, :], w, wl


def seq_stats(X_nan):
    v = ~np.isnan(X_nan); c = v.sum(1, keepdims=True).astype(float); x = np.nan_to_num(X_nan)
    m = (x * v).sum(1, keepdims=True) / np.maximum(c, 1)
    s = np.sqrt((((x - m) * v) ** 2).sum(1, keepdims=True) / np.maximum(c, 1) + EPS)
    return np.where(c > 0, m, 0.0), np.where(c > 1, s, 1.0)


# ------------------------------------------------------------------------------------------- downstream
def feats(X):
    return np.concatenate([X.mean(1), X.std(1), X.min(1), X.max(1), X[:, -1] - X[:, 0]], axis=1)


def _clf():
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    return make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))


def downstream(ds, meta, itrain, ite, Xtrain_complete, Xte_imputed, Xte_complete):
    from sklearn.metrics import roc_auc_score, balanced_accuracy_score
    out = {}
    Ftr, Fim, Fco = feats(Xtrain_complete), feats(Xte_imputed), feats(Xte_complete)
    mtr, mte = meta.iloc[itrain].reset_index(drop=True), meta.iloc[ite].reset_index(drop=True)
    if ds == "Motor":
        for H in LATE_DAYS:
            e_tr, l_tr = early_late(mtr, H); e_te, l_te = early_late(mte, H)
            str_, ste = e_tr | l_tr, e_te | l_te
            ytr, yte = l_tr[str_].astype(int), l_te[ste].astype(int)
            if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
                out[f"down_auc{H}"] = out[f"down_auc{H}_complete"] = np.nan; continue
            clf = _clf().fit(Ftr[str_], ytr)
            out[f"down_auc{H}"] = float(roc_auc_score(yte, clf.predict_proba(Fim[ste])[:, 1]))
            out[f"down_auc{H}_complete"] = float(roc_auc_score(yte, clf.predict_proba(Fco[ste])[:, 1]))
    else:
        a, b = [], []
        for t in HYD_TARGETS:
            clf = _clf().fit(Ftr, mtr[t].to_numpy())
            yte = mte[t].to_numpy()
            out[f"down_bacc_{t}"] = float(balanced_accuracy_score(yte, clf.predict(Fim)))
            out[f"down_bacc_{t}_complete"] = float(balanced_accuracy_score(yte, clf.predict(Fco)))
            a.append(out[f"down_bacc_{t}"]); b.append(out[f"down_bacc_{t}_complete"])
        out["down_bacc_mean"], out["down_bacc_mean_complete"] = float(np.mean(a)), float(np.mean(b))
    return out


# ------------------------------------------------------------------------------------------- jobs
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
    import dtin_v2 as v2, dtin_v2_eval as ev
    return dc, v2, ev


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
    jobs = lr + knn + heavy                         # quick jobs first; round-robin over workers stays balanced
    for j in jobs:
        j["id"] = f'{j["dataset"]}|{j["mech"]}|{j["level"]}|{j["seed"]}|{j["method"]}|{j["norm"]}'
    return jobs


def res_path(j):
    return os.path.join(OUT, "results", hashlib.md5(j["id"].encode()).hexdigest() + ".json")


def make_mask(dc, ds, X, mech, lv, seed, split):
    rng = np.random.default_rng(sseed("step3-mask", ds, mech, lv, seed, split))
    if mech == "MCAR":
        return dc.mask_mcar(X.shape, lv, rng)
    if mech == "MNAR":
        return dc.mask_mnar(X, lv, rng, dc.CFG["mnar_quantile"], dc.CFG["mnar_p_high"])
    if mech == "GAP":
        return dc.mask_gaps(X.shape, GAP_L[ds], int(round(GAP_FRAC * X.shape[1])), rng)
    raise ValueError(mech)


def run_job(j, dc, v2, ev, data):
    import torch
    ds, mech, lv, seed, method, norm = j["dataset"], j["mech"], j["level"], j["seed"], j["method"], j["norm"]
    X, meta = data[ds]
    itr, ist, ite = split_idx(ds, meta, seed)
    itrain = np.r_[itr, ist]
    Xa, Xte, _ = dc.standardize(X[itrain], X[ite])
    tr, st = np.arange(len(itr)), np.arange(len(itr), len(itrain))
    Mtr = make_mask(dc, ds, Xa, mech, lv, seed, "train"); Mte = make_mask(dc, ds, Xte, mech, lv, seed, "test")
    Xtr_m, Xte_m = dc.apply_mask(Xa, Mtr), dc.apply_mask(Xte, Mte)
    s = sseed("step3-init", ds, mech, lv, seed, method); info = {}
    if method == "Linear regression":
        imp = dc.impute_lr_time(Xte_m)
    else:
        if norm == "global":
            Ztr, Zte, Zst = Xtr_m, Xte_m, Xa[st]; back = lambda Z: Z
        else:
            if norm == "seq":
                f = seq_stats
            else:
                sn = ShrinkNormV2().fit(Xtr_m); f = lambda A: sn.stats(A)[:2]
                _, _, w, wl = sn.stats(Xte_m); info.update(w_mean=float(w.mean()), wl_mean=float(wl.mean()))
            (mtr, s_tr), (mte, s_te), (mst, s_st) = f(Xtr_m), f(Xte_m), f(Xtr_m[st])
            Ztr, Zte, Zst = (Xtr_m - mtr) / s_tr, (Xte_m - mte) / s_te, (Xa[st] - mst) / s_st
            back = lambda Z: Z * s_te + mte
        za = np.abs(Zte[~np.isnan(Zte)])
        info.update(zin_p999=float(np.percentile(za, 99.9)), zin_max=float(za.max()))
        if method == "KNN":
            Zimp = dc.impute_knn(Ztr, Zte, dc.CFG["knn_k"])
        elif method == "SAITS":
            Zimp, val = ev.pypots_fit_impute("SAITS", ev.select_saits()["cfg"], Ztr[tr], Zst, Mtr[st], Zte, s)
            info["val_stop_rmse_model_space"] = val
        elif method == "Transformer":
            model = v2.DTINv2Imputer(v2.imputation_config(**TRANSFORMER), seed=s).fit(Ztr[tr], Zst, Mtr[st])
            Zimp = model.impute(Zte); del model
        else:
            raise ValueError(method)
        imp = back(Zimp)
    imp = np.where(np.isnan(Xte_m), imp, Xte_m)
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    res = dict(j, rmse=dc.rmse_at(Xte, imp, Mte), n_train=len(itr), n_stop=len(ist), n_test=len(ite), **info)
    res.update(downstream(ds, meta, itrain, ite, Xa, imp, Xte))
    return res


def run(worker=0, n_workers=1):
    plan = os.path.join(OUT, "PLAN_step3.md")
    if not os.path.exists(plan):
        sys.exit("Write and register the plan first: python step3_independent.py plan")
    sha = script_sha()
    if sha not in open(plan, encoding="utf-8").read():
        print("WARNING: this script differs from the version recorded in PLAN_step3.md; document the change as an amendment.")
    os.makedirs(os.path.join(OUT, "results"), exist_ok=True); os.makedirs(os.path.join(OUT, "errors"), exist_ok=True)
    data = {ds: load_cache(ds) for ds in DATASETS}
    dc, v2, ev = modules(); import torch
    jobs = [j for i, j in enumerate(job_list()) if i % n_workers == worker]
    for i, j in enumerate(jobs, 1):
        p = res_path(j)
        if os.path.exists(p): continue
        print(f"[{i}/{len(jobs)}] {j['id']}", flush=True); t0 = time.time(); res = None
        for strict in (True, False):
            strict_mode(strict)
            try:
                res = run_job(j, dc, v2, ev, data); res["deterministic"] = strict; break
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
    jobs = job_list(); done = sum(os.path.exists(res_path(j)) for j in jobs)
    errs = glob.glob(os.path.join(OUT, "errors", "*.txt"))
    print(f"finished {done} of {len(jobs)} jobs; errors: {len(errs)}")
    for e in errs[:5]: print("  ", open(e).read().splitlines()[0])


def fetch():
    import urllib.request
    os.makedirs(HYD_DIR, exist_ok=True)
    z = os.path.join(HYD_DIR, "hydraulic.zip")
    if not os.path.exists(z):
        print("downloading", HYD_URL); urllib.request.urlretrieve(HYD_URL, z)
    def extract(zf):
        for i in zf.infolist():
            b = os.path.basename(i.filename)
            if b.lower().endswith(".zip"):
                import io; extract(zipfile.ZipFile(io.BytesIO(zf.read(i))))
            elif b.lower().endswith(".txt"):
                open(os.path.join(HYD_DIR, b), "wb").write(zf.read(i))
    extract(zipfile.ZipFile(z))
    missing = [s for s in HYD_SENSORS + ["profile"] if not glob.glob(os.path.join(HYD_DIR, "**", f"{s}.txt"), recursive=True)]
    print("hydraulic files ready" if not missing else f"missing files: {missing}")


# ------------------------------------------------------------------------------------------- report
def verdict(ok, n, need):
    return ("supported" if ok else "not supported") if n == need else f"no decision yet ({n} of {need} cells complete)"


def report():
    rows = [json.load(open(p)) for p in glob.glob(os.path.join(OUT, "results", "*.json"))]
    if not rows: sys.exit("no results yet")
    d = pd.DataFrame(rows)
    d["cond"] = d.mech + " " + d.level.map(lambda x: f"{float(x):g}")
    d["label"] = d.apply(lambda r: r.method if r.method == "Linear regression" else f"{r.method}-{r.norm}", axis=1)
    L = ["# Step 3 report", "", f"Jobs finished: {len(d)} of {len(job_list())}",
         f"Script versions in the results: {sorted(d.script_sha256.unique())}", ""]
    for ds in DATASETS:
        sub = d[d.dataset == ds]
        if sub.empty: continue
        piv = sub.groupby(["label", "cond"]).rmse.mean().unstack().round(4)
        L += [f"## {ds}: mean RMSE", "", "```", piv.to_string(), "```", ""]; piv.to_csv(os.path.join(OUT, f"step3_rmse_{ds}.csv"))
    # H1'
    cells = []
    for ds in DATASETS:
        for mech, lv in CONDITIONS:
            c = f"{mech} {lv:g}"
            for mdl in MODELS:
                g = d[(d.dataset == ds) & (d.cond == c) & (d.method == mdl)]
                p = g.pivot(index="seed", columns="norm", values="rmse")
                if not set(NORMS) <= set(p.columns) or p.isna().any().any(): continue
                mean = p.mean(); refn = "global" if mean["global"] <= mean["seq"] else "seq"; ref = mean[refn]
                r = mean["shrink"] / ref
                cells.append(dict(dataset=ds, condition=c, model=mdl, n=len(p), global_=mean["global"], seq=mean["seq"], shrink=mean["shrink"],
                                  ratio=r, ok=r <= NO_HARM, wrong_choice_cost=max(mean["global"], mean["seq"]) / ref,
                                  seeds_within=int((p["shrink"] / p[refn] <= NO_HARM).sum())))
    h = pd.DataFrame(cells)
    if len(h):
        share = h.ok.mean(); h1 = share >= NO_HARM_SHARE
        L += ["## H1' - shrink versus the better of global and seq (RMSE)", "",
              "| dataset | condition | model | global | seq | shrink | shrink / better | within 2% | seeds within 2% | worse / better |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        L += [f"| {r.dataset} | {r.condition} | {r.model} | {r.global_:.4f} | {r.seq:.4f} | {r.shrink:.4f} | {r.ratio:.3f} | {'yes' if r.ok else 'no'} | {r.seeds_within}/{r.n} | {r.wrong_choice_cost:.3f} |"
              for r in h.itertuples()]
        need = len(DATASETS) * len(CONDITIONS) * len(MODELS)
        L += ["", f"cells within 2%: {int(h.ok.sum())} of {len(h)} ({share:.0%}; {need} cells planned) -> "
              f"**H1' {verdict(h1, len(h), need)}**", ""]
        h.to_csv(os.path.join(OUT, "step3_h1_cells.csv"), index=False)
    # H3
    h3 = []
    for ds in DATASETS:
        for c in ("MNAR 0.3", "GAP 0.4"):
            g = d[(d.dataset == ds) & (d.cond == c) & (d.norm == "seq")]
            p = g.pivot(index="seed", columns="method", values="rmse")
            if not {"Transformer", "SAITS"} <= set(p.columns): continue
            p = p[["Transformer", "SAITS"]].dropna()
            gain = (p.SAITS.mean() - p.Transformer.mean()) / p.SAITS.mean(); wins = int((p.Transformer < p.SAITS).sum())
            h3.append(dict(ds=ds, c=c, gain=gain, wins=wins, n=len(p), ok=gain >= H3_GAIN and wins >= H3_WINS))
    if h3:
        L += ["## H3 - transformer versus SAITS (both with seq normalization)", "",
              "| dataset | condition | RMSE reduction | transformer lower | meets |", "|---|---|---|---|---|"]
        L += [f"| {r['ds']} | {r['c']} | {r['gain']:+.3f} | {r['wins']}/{r['n']} | {'yes' if r['ok'] else 'no'} |" for r in h3]
        L += ["", f"cells meeting the rule: {sum(r['ok'] for r in h3)} of {len(h3)} (4 planned) -> "
              f"**H3 {verdict(sum(r['ok'] for r in h3) >= 3, len(h3), 4)}**", ""]
    # downstream
    metrics = [("Motor", f"down_auc{H}") for H in LATE_DAYS] + [("Hydraulic", "down_bacc_mean")]
    dcells = []
    for ds, col in metrics:
        sub = d[d.dataset == ds]
        if sub.empty or col not in sub: continue
        piv = sub.groupby(["label", "cond"])[col].mean().unstack().round(3)
        comp = sub.groupby("cond")[col + "_complete"].mean().round(3)
        L += [f"## {ds}: downstream {col} (complete-data reference by condition: {comp.to_dict()})", "", "```", piv.to_string(), "```", ""]
        for mech, lv in CONDITIONS:
            c = f"{mech} {lv:g}"
            for mdl in MODELS:
                m = sub[(sub.cond == c) & (sub.method == mdl)].groupby("norm")[col].mean()
                if not set(NORMS) <= set(m.index) or m.isna().any(): continue
                dcells.append(dict(ds=ds, metric=col, c=c, model=mdl, diff=m["shrink"] - max(m["global"], m["seq"]),
                                   ok=m["shrink"] >= max(m["global"], m["seq"]) - DOWN_MARGIN))
    if dcells:
        t = pd.DataFrame(dcells); share = t.ok.mean(); need_d = (len(LATE_DAYS) + 1) * len(MODELS) * len(CONDITIONS)
        L += ["## Downstream no-harm (shrink >= better of global and seq - 0.02)", "", "```",
              t.round(3).to_string(index=False), "```", "",
              f"cells meeting the rule: {int(t.ok.sum())} of {len(t)} ({share:.0%}; {need_d} planned) -> "
              f"**downstream no-harm {verdict(share >= NO_HARM_SHARE, len(t), need_d)}**", ""]
        t.to_csv(os.path.join(OUT, "step3_downstream_cells.csv"), index=False)
    if "w_mean" in d:
        wt = d.dropna(subset=["w_mean"]).groupby(["dataset", "cond"])[["w_mean", "wl_mean"]].mean().round(3)
        L += ["## Mean shrinkage weights on the test inputs", "", "```", wt.to_string(), "```", ""]
    L += [f"Jobs run without strict determinism: {int((~d.deterministic.astype(bool)).sum())}"]
    txt = "\n".join(L); open(os.path.join(OUT, "REPORT_step3.md"), "w", encoding="utf-8").write(txt)
    d.to_csv(os.path.join(OUT, "step3_all_runs.csv"), index=False); print(txt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["plan", "fetch", "prepare", "run", "status", "report"])
    ap.add_argument("--worker", type=int, default=0); ap.add_argument("--n-workers", type=int, default=1)
    a = ap.parse_args()
    if a.cmd == "plan":
        os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, "PLAN_step3.md")
        if os.path.exists(p): sys.exit(f"{p} already exists; it must not be changed after results exist")
        txt = PLAN.format(sha=script_sha(), stab=STAB_HOURS, tm=T_LEN["Motor"], seeds=SEEDS, mt=MOTOR_TEST, ms=MOTOR_STOP,
                          eh=END_HOURS, hb=HYD_BLOCK, ht=HYD_TEST, hs=HYD_STOP, gf=GAP_FRAC, gm=GAP_L["Motor"], gh=GAP_L["Hydraulic"],
                          ed=EARLY_DAYS, ld=LATE_DAYS, nh=NO_HARM, nhs=NO_HARM_SHARE, g3=H3_GAIN, w3=H3_WINS, dm=DOWN_MARGIN)
        open(p, "w", encoding="utf-8").write(txt + f"\nWritten: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(open(p, encoding="utf-8").read()); print("SHA-256 of the plan:", hashlib.sha256(open(p, "rb").read()).hexdigest())
    elif a.cmd == "fetch": fetch()
    elif a.cmd == "prepare": prepare()
    elif a.cmd == "run": run(a.worker, a.n_workers)
    elif a.cmd == "status": status()
    else: report()
