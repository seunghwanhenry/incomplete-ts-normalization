# Step 2 - reliability-weighted normalization (pre-specified)

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
where lam is the mean training log standard deviation and s_seq = sqrt(var + 1e-05).

## Design
* Conditions: Siemens MCAR 30%, MAR 30%, MNAR 30%, consecutive gaps of length 30, MCAR 70%;
  ECG200 MCAR 30%, MCAR 70%. Seeds [0, 1, 2, 3, 4]. Same splits and masks as in Step 1.
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
Cells: every (model, condition, metric) with model in {SAITS, KNN, Transformer} for all conditions and BRITS for
the ECG200 conditions; on Siemens both metrics, on ECG200 the RMSE. ref = min(mean RMSE global, mean RMSE seq).
* H1 supported: mean RMSE shrink <= 1.02 x ref in at least 90% of the cells.
  Then shrink normalization is carried to Step 3 unchanged. Otherwise at most one revision on development data,
  documented with its reason; if H1 still fails, the follow-up study is framed as an analysis of normalization
  under missingness, without a new normalization method.
* Reported descriptively: cells in which shrink is more than 2% better than ref; the mean weights w and w_l.
* H2 supported: on Siemens GAP 30 and MNAR 30 (both metrics, 4 cells), the transformer with mixed masking has a
  mean RMSE at least 3% lower than with point masking and is lower in at least 4 of 5 seeds,
  in at least 3 of the 4 cells.

Written: 2026-11-13 23:33:48
