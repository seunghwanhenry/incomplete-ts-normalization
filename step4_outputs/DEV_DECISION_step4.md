# Step 4 - development decision (written after REPORT_step4.md; exploratory)

## What the pre-written rule chose
Among the variants listed in PLAN_step4.md the rule chose **sel_var** (per-variable selection): 43 of 48 cells within 2%
of the better single normalization (oracle), worst ratio 2.371. Seq alone: 28 of 48 (worst 3.009); global alone: 22 of
48 (worst 31.970).

## Why it failed where it failed
All five failing cells were Motor cells (four with the transformer, one with SAITS), and the failures came from seed 0, the only Step 4 seed
with motor 155 in the test set. Motor 155 has an N2F level about 50 times that of the other motors (cause unknown).
Whenever the validation weights put some weight on the global imputation, the global imputer fails on all
variables of that motor's windows, not only on N2F, because its whole input is outside the training distribution.
The pre-listed guard works per variable and therefore removed only part of the error (sel_var+guard: 39 of 48,
worst 1.948).

## Post hoc additions (after seeing the results)
1. Window-level guard: if any variable of a test window lies outside the range of the masked training windows by more
   than kappa range widths (visible mean, or visible mean and log standard deviation), the whole window uses seq.
2. Range floor 1e-6: Siemens has variables that are constant in all training windows (range 0). Without a floor,
   float32 rounding of the stored window statistics made the guard fire on every Siemens test window.

## Sensitivity (step4_guard_analysis.py; cells within 2% of 48, worst ratio, geometric mean of ratio to oracle)
| variant | guard | kappa 0.25 | 0.5 | 1 | 2 | 5 | 10 | none |
|---|---|---|---|---|---|---|---|---|
| comb_var | mean + log sd | 48, 1.014, 0.915 | 48, 1.020, 0.911 | 47, 1.023, 0.911 | 47, 1.023, 0.909 | 47, 1.023, 0.910 | 47, 1.023, 0.910 | 42, 2.862, 0.975 |
| sel_var | mean + log sd | 48, 1.020, 0.932 | 47, 1.092, 0.930 | 47, 1.098, 0.930 | 47, 1.098, 0.928 | 47, 1.098, 0.928 | 47, 1.098, 0.928 | 43, 2.371, 0.959 |

The result is flat for kappa from 0.25 to 10, and the convex combination is better than selection (lower worst ratio and
geometric mean) at every kappa; kappa = 1 ("more than one range width outside") was chosen as a round
value inside the plateau, and both location and scale are checked because a window with an unusual spread is also
outside the training distribution of the global imputer.

## Frozen method for Step 5
comb_var (per-variable convex combination of the global and seq imputations, weights from the validation windows) +
window guard on mean and log standard deviation, kappa = 1, range floor 1e-6.
Development results (optimistic, chosen on these data): 47 of 48 cells within 2% of the oracle (worst 1.023, Motor
MCAR 70% transformer); 40 of 48 cells at or below the oracle; geometric mean ratio to the oracle 0.911, to seq 0.794,
to global 0.380; by dataset (ratio to the oracle): ECG200 0.993, Hydraulic 0.725, Motor 0.985, Siemens 0.971.

## Reproducibility
Motor and Hydraulic reruns with Step 3's splits, masks and seeds reproduced Step 3: 280 runs, largest absolute RMSE
difference 5.9e-09; all runs under strict determinism.
