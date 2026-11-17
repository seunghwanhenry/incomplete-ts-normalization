# Step 6 - controls for dual normalization (pre-specified)

Written after the Step 5 report and before any Step 6 run. Script step6_controls.py, SHA-256 7d8a2ff8d587587373ba7973409fbe44e0b0cf0eda2b0de65d48bc4c67c52ed1;
step5_confirm.py SHA-256 f3492a1c5edd50c845b4509ed4108883f64e8390ac4748c4164f32d72a08658d.

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
* H4 (superiority): dual < min(ensemble G+G', ensemble S+S') in at least 12 of 16 cells.
* H5 (non-inferiority): dual <= 1.02 x min(ensemble G+G', ensemble S+S') in at least 90% of the 16 cells.
* Reported descriptively: geometric-mean ratios; per-seed comparisons; ablations of dual normalization on the Step 5
  predictions for all three models (equal weights 0.5, one pooled weight, per-variable selection, no guard); training
  time of each member.

Written: 2026-11-17 14:29:56
