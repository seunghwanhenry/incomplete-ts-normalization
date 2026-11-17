# Step 7 - robustness re-analysis of Step 5 (post hoc; decision rules fixed before any Step 7 run)

Written after a pre-submission review of the manuscript and before any Step 7 job was run. Script step7_robustness.py,
SHA-256 ea8893efbbf37f8cade41a0afdcf929de3dd1295d044d84d6adc9f8fa42e8979; it imports the unchanged step5_confirm.py (SHA-256 f3492a1c5edd50c845b4509ed4108883f64e8390ac4748c4164f32d72a08658d).

## Status of the data
The Step 5 data (C-MAPSS FD001 + FD003, MetroPT-3) and the Step 5 and Step 6 results are known. Step 7 is therefore
not an independent confirmation; it asks whether the Step 5 conclusions depend on features of the Step 5 protocol.
Done before this plan, from existing files only: the size of the statistics difference (below), validation-selected
baselines from the Step 5 and Step 6 predictions (reported separately as post hoc), and the reproduction check of this
script (`check`: Step 5 protocol, KNN, four jobs; the test imputations equal the Step 5 files exactly). No job of the
clean protocol had been run on real data.

## Why
1. In Step 5 the global mean and standard deviation of each variable were computed from all values of the training
   and early-stopping windows before any value was removed. A deployed system only has the observed values, and the
   early-stopping windows also selected the checkpoints and estimated the dual weights. Under MNAR, the observed-only
   statistics of the training units differ by a median of about -0.2 standard deviations in the mean and a factor of
   about 0.9 in the standard deviation; under MCAR and gaps by at most 0.07 standard deviations and a factor of 0.89-1.08
   (computed from the data and masks only; no model was run).
2. The same early-stopping windows chose the checkpoints and estimated the dual weights.
3. The window guard was almost never active in Step 5, so its effect on new data was not tested.

## Protocol ("clean"; everything not listed is identical to Step 5)
* Global standardization: mean and standard deviation of the observed (unmasked) values of the training units' windows
  (standard deviation 1 if it is 0 or undefined, mean 0 if no value is observed).
* The early-stopping units of each seed are split by unit into two halves (seeded permutation; the calibration half has
  floor(n/2) units): ES windows select the checkpoint of SAITS and the transformer and, with the training windows, form
  the KNN reference set; CAL windows are imputed by every model and only estimate the dual weights.
* Dual weights, window guard (kappa = 1, ranges from the masked training windows) and combination as in Step 5.
* Same model seeds as Step 5 (common random numbers). Metric: RMSE at the removed test positions on the Step 5 reporting
  scale (Step 5 standardization, used by no model).
* Stress test (descriptive): copies of the test windows with one variable per window shifted by k standard deviations of
  the observed training values, k in [3, 10, 100]; every model imputes them without retraining.

## Decision rules (24 cells = dataset x condition x model, mean RMSE over seeds 0-9; oracle = better of global and seq)
* R1: dual <= 1.02 x oracle in at least 90% of the cells.
* R2: geometric mean over the cells of dual / seq <= 0.98 and of dual / global <= 0.98.
* R3: dual / oracle <= 1.1 in every cell.
If R1-R3 hold, the manuscript states that the Step 5 conclusions do not depend on the Step 5 statistics or on the shared
early-stopping windows. If any fails, the manuscript reports the Step 7 result next to Step 5 and qualifies the claims.

## Reported descriptively
Ratio of every variant's cell RMSE to Step 5; dual weights; guard activation on the normal and the stressed test windows;
stress-test RMSE of global, seq, dual without guard and dual (all removed positions, and the shifted variable only).
Unit level, for Step 5 and Step 7: per-unit RMSE; bootstrap over test units (resampled within each seed, the same draw
for all cells of a dataset; 2000 replicates; percentile 95% intervals) of the geometric-mean ratios per dataset and of
the number of cells within 1.02 x oracle; median, 95th percentile and maximum over units of dual / better normalization.

Written: 2026-11-17 23:27:24
