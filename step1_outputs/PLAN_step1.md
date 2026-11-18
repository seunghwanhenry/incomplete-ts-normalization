# Step 1 - decomposition of the DTIN-v2 advantage (pre-specified)

Written before any Step 1 result was computed. Commit this file (with its date) before running the jobs.

## Question
Is the lower imputation RMSE of DTIN-v2 on Siemens explained by the transformer and its mask input, or by the
mask-aware per-sequence normalization, which any imputation model can use?

## Data status
Siemens and ECG200, including their former test splits, are development data in the follow-up study. The
results of Step 1 guide the method design and are not reported as independent evidence.

## Design
* Conditions: Siemens MCAR 30%, MAR 30%, MNAR 30%, consecutive gaps of length 30 (40% removed); ECG200 MCAR 30%.
* Seeds: [0, 1, 2, 3, 4]. Missing masks as in the earlier experiments (same mask generator and seeds).
* Training data: development-training part of the training set; early stopping on the early-stopping part
  (same splits as before); evaluation on the former test split.
* Normalization wrapper (identical to the one inside DTIN-v2): per sequence and variable, mean m and standard
  deviation s of the visible values, s = sqrt(sum v (x - m)^2 / c + 1e-05); m = 0 if c = 0 and s = 1 if c < 2.
  Inputs are normalized with their own statistics, the model imputes in the normalized space, and the
  output is transformed back. Validation targets are normalized with the statistics of the masked validation inputs.
* Methods: linear regression (invariant to the wrapper; reference), KNN, BRITS and SAITS each with
  global standardization only ("global") and with the wrapper ("seq"); DTIN-v2 variants:
  DTIN-v2 (mask input + seq-norm), DTIN-v2 w/o seq-norm, DTIN-v2 w/o mask input, Transformer (no mask input, no seq-norm).
* Fixed settings: BRITS hidden 64; SAITS = configuration selected earlier on development data; KNN k = 5;
  DTIN-v2 = final imputation configuration (lambda = 0). No tuning in Step 1. CSDI is excluded
  (unstable and slow in the earlier experiments).
* Metrics: RMSE at removed positions; on Siemens also without PI12002_PV_Out.

## Decision rules (fixed now)
For each Siemens condition c and each metric, let B* be the method with the lowest mean RMSE among the
baselines with the wrapper (linear regression, KNN-seq, BRITS-seq, SAITS-seq), G_c = (RMSE(B*) - RMSE(DTIN-v2)) / RMSE(B*)
and W_c the number of seeds in which DTIN-v2 has a lower RMSE than B*.

* R1 - architecture advantage: G_c >= 0.05 and W_c >= 4 of 5 in at least 3 of the 4 Siemens conditions,
  on both metrics. Then the follow-up study may claim the mask-aware transformer as part of its contribution.
* R2 - normalization explains the advantage: R1 does not hold. Then the transformer architecture is not claimed
  as a contribution, and Step 2 develops the normalization as a model-agnostic component evaluated with several
  imputation models.
* N1 - normalization helps on Siemens: (RMSE(global) - RMSE(seq)) / RMSE(global) >= 0.05 for at least
  2 of the 3 baselines (KNN, BRITS, SAITS) in at least 3 of the 4 Siemens conditions (primary metric).
* N2 - normalization harms on ECG200: the same relative change is <= -0.05 for at least 2 of the 3
  baselines. Then Step 2 must include an adaptive rule whose design target is never to be more than 2% worse
  than global standardization on development data.
The mask-input effect (DTIN-v2 with and without mask input) is reported descriptively.

Written: 2026-11-11 16:36:23
