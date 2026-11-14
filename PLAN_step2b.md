# Step 2b - revised reliability-weighted normalization (pre-specified; the single permitted revision)

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
deviation l_seq = 0.5 log(var + 1e-05):
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
  Seeds [0, 1, 2, 3, 4]; same splits and masks as before.
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
* H1 supported: mean RMSE shrink <= 1.02 x ref in at least 90% of the cells -> the revised
  normalization goes to Step 3 unchanged.
* H1 not supported: no further revision; the study is framed as an analysis of normalization under missingness.
* Reported descriptively: cells where shrink is more than 2% better than ref; weights; normalized-input percentiles.

Written: 2026-11-14 21:22:20
