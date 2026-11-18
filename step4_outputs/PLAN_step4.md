# Step 4 - development of dual normalization (exploratory)

Script step4_dual.py, SHA-256 66b5b11c8bac19e466e2ad62e00086ad7f01404cad586b735a961e9dc48a2521. Written before any Step 4 result.

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
1. Highest number of cells with mean RMSE <= 1.02 x oracle.
2. Ties (within one cell): lower worst-case ratio to the oracle.
3. Remaining ties: the simpler variant (pool before var, sel before comb, no guard before guard).
Also reported: per-seed ratios, ratios per test unit (median over units), guard activation rates, linear regression.

Written: 2026-11-16 09:25:50
