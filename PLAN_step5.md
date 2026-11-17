# Step 5 - confirmation of dual normalization (pre-specified)

Written before the Step 5 datasets were downloaded or opened. Register this file (public GitHub commit) before running
`fetch`, `prepare` and `run`. Script: step5_confirm.py, SHA-256 f3492a1c5edd50c845b4509ed4108883f64e8390ac4748c4164f32d72a08658d.

## History that led to this test
Steps 1-3 showed that the advantage of the earlier DTIN model came from per-sequence normalization, that the better of
global and per-sequence normalization changes between datasets, and that a reliability-weighted shrinkage (Steps 2-2b)
did not choose between them on independent data (Step 3, pre-registered, not supported). In Step 4 (exploratory,
development data Siemens, ECG200, Motor, Hydraulic) dual normalization was developed. The variant list and choice
rule were written before Step 4, and the rule selected per-variable selection. After inspecting the Step 4 failures,
which all came from one test motor outside the training range, a window-level guard with a margin was added and the
per-variable convex combination with this guard was chosen (step4_guard_analysis.py, DEV_DECISION_step4.md). On the
development data it was within 2% of the better single normalization in 47 of 48 cells (worst ratio 1.023;
geometric-mean ratio 0.911; 47-48 of 48 cells for margins from 0.25 to 10 range widths). These figures are optimistic
because the guard was chosen on these data; this step tests the frozen method on new data.

## Method (frozen; functions dual_weights and window_guard in this script)
1. Each model is trained twice on the same masked training windows and with the same model seed: (G) global
   standardization only; (S) per-sequence normalization with the mean and standard deviation of the visible values of
   each window, inverted after imputation.
2. Both imputers impute the masked early-stopping windows. For every variable d, a_d = clip((Es - C) / (Eg + Es - 2C),
   0, 1), where Eg and Es are the validation MSEs of G and S at the removed positions of d and C is the mean product of
   their errors (a_d = 0.5 if the denominator is 0; the pooled value if d has no removed validation value).
3. Window guard: for every test window and variable with at least two visible values, the visible mean and log
   standard deviation are compared with their ranges over the masked training windows; the exceedance is the distance
   outside the range divided by the range width (floor 1e-6). If the largest exceedance of the window exceeds 1,
   a_d = 0 for all variables of that window.
4. Imputed value = a_d * G + (1 - a_d) * S at the removed positions.

## Data (fixed now, from the public documentation only)
C-MAPSS is a widely used benchmark whose general properties are known from the literature; MetroPT-3 is less used.
* CMAPSS: training files of FD001 and FD003 (200 engines, run to failure); sensors s2, s3, s4, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21; one value per cycle;
  per engine, non-overlapping windows of 30 cycles from the first cycle; an incomplete last window is dropped.
  Units = engines (FD003 engine numbers offset by 1000).
* MetroPT: the seven analogue signals TP2, TP3, H1, DV_pressure, Reservoirs, Oil_temperature, Motor_current; 1-min means on a regular grid; non-overlapping windows of 60 minutes
  aligned to full hours; windows with an empty minute are dropped. Units = calendar days.
* Both: global standardization with the statistics of the training and early-stopping windows of each split.

## Splits, conditions, seeds
* Seeds [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]; each seed gives a different split, masks and model seed (the same model seed for both normalizations).
* Units are permuted per seed: 30% test, 10% early stopping (also used for the dual weights), the rest training.
* Missingness on training and test windows: MCAR 30%, MCAR 70%, MNAR 30% (values above the 70th percentile removed
  with probability 0.6), consecutive gaps with 40% of each variable removed (gap length CMAPSS 6, MetroPT 12).
* Models (settings fixed in development, no tuning on these data): KNN (k = 5), SAITS (development configuration), the
  DTIN transformer (internal normalization off); linear regression on time as a reference.
* Metric: RMSE at the removed positions (standardized scale), averaged over seeds.

## Hypotheses and decision rules
Cells = dataset x condition x model = 24; oracle = min(mean RMSE global, mean RMSE seq) in the cell.
* H1 (primary): mean RMSE dual <= 1.02 x oracle in at least 90% of the cells.
* H2 (secondary): the geometric mean over the cells of RMSE dual / RMSE seq <= 0.98, and the same for dual / global.
* H3 (secondary): RMSE dual / oracle <= 1.1 in every cell.
* Reported descriptively: per-seed and per-unit results, guard activation, the weights, linear regression, and the
  downstream tasks below (no decision rule).

## Downstream tasks (descriptive)
Features per window: mean, standard deviation, minimum, maximum, last-minus-first per variable; standardization +
logistic regression (class-balanced, max_iter 2000), trained on complete training windows, evaluated on imputed and on
complete test windows (AUROC).
* CMAPSS: early life (window ends within the first 60 cycles) versus late life (window starts within H cycles of
  the last cycle), H in [60, 90]; a window meeting both is excluded.
* MetroPT: windows overlapping a documented air-leak failure versus the others (seeds whose test or training set has
  no failure window are reported as missing).

Written: 2026-11-17 09:37:37
