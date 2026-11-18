# Step 3 - independent evaluation (pre-specified)

Written before the Step 3 datasets were used for any model or result. Register this file publicly (OSF registration or a
public GitHub commit) before running `fetch`, `prepare` and `run`. Script: step3_independent.py, SHA-256 1ccb47c1f3adda966c2549bea317ebba6f1188315b676b50311c2d82fb1269d3.

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
* Motor: per motor life, records from 48 h after the first record (stabilization) to the start of the replacement
  day, i.e. the last 24 h are excluded because they may contain the stop, the exchange and the start of the new
  motor; this point is the end of life. 10-min grid; non-overlapping windows of 144 points (one day) counted from the
  end of stabilization; windows with a missing timestamp are dropped.
* Both datasets: global standardization with the statistics of the training and early-stopping windows of each split.
* Hydraulic: every sensor averaged to 1 Hz within the cycle (60 points; 100 Hz: means of 100 samples, 10 Hz: means of
  10); one window per cycle (60 x 17); all cycles used.

## Splits, conditions, seeds
* Seeds [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]. Each seed defines a different split, the masks and the model initialization (common to the three
  normalizations of a model).
* Motor: per seed, motors are permuted; 5 test motors, 2 motors for early stopping, the rest for training.
* Hydraulic: blocks of 25 consecutive cycles; per seed, 30% of the blocks for testing, 10% for early
  stopping, the rest for training.
* Missingness, applied to training and test windows (same generators as in development): MCAR 30%, MCAR 70%,
  MNAR 30% (values above the 70th percentile of their variable removed with probability 0.6, the other values with
  the probability that gives 30% overall), consecutive gaps with
  40% of each variable removed (gap length 36 points = 6 h for Motor, 12 points = 12 s for Hydraulic).
* Imputation metric: RMSE at the removed positions (standardized scale).

## Downstream tasks (impute, then classify; the classifier is fixed and trained on complete training windows)
* Features per window: mean, standard deviation, minimum, maximum and last-minus-first of every variable;
  standardization + logistic regression (class-balanced, max_iter 2000); no tuning.
* Motor health state: early-life windows (ending within 7 days after stabilization) versus late-life windows
  (starting within H days before the end of life), H in [3, 7, 14]; all three reported; a window meeting both definitions
  is excluded. Metric: AUROC on the test motors' windows. The maintenance-event times are not used.
* Hydraulic condition diagnosis: cooler (3 classes), valve (4), internal pump leakage (3) and accumulator (4); metric:
  balanced accuracy,
  averaged over the four targets (each target also reported).
* Reference: the same classifier on the complete (unmasked) test windows.

## Hypotheses and decision rules
* H1' (primary): cells = dataset x model (KNN, SAITS, Transformer) x condition = 24; ref = min(mean RMSE global, mean RMSE
  seq). Supported if mean RMSE shrink <= 1.02 x ref in at least 90% of the cells.
* H3 (secondary): cells = dataset x condition in (MNAR 30%, GAP) = 4. In a cell, the transformer with seq normalization
  is better than SAITS with seq normalization if its mean RMSE is at least 3% lower and lower in at least 8
  of 10 seeds. Supported if this holds in at least 3 of 4 cells. Caveat recorded now: in development the transformer
  configuration was chosen from 24 candidates and SAITS from 4.
* Downstream no-harm (secondary): cells = dataset x model x condition x metric (Motor: AUROC for H = 3, 7, 14;
  Hydraulic: mean balanced accuracy). Supported if mean(shrink) >= max(mean(global), mean(seq)) - 0.02 in at least
  90% of the cells.
* Reported descriptively: the cost of choosing the worse of global and seq (ratio of their mean RMSE) per cell;
  seed-level paired comparisons; shrinkage weights; all cells, including those not meeting a rule.

Written: 2026-11-15 19:39:46
