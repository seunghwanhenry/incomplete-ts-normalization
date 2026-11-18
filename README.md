# Normalization in deep imputation of industrial time series: a staged study with pre-specified decision rules

Code, plans, reports and per-run results for

> Song, S., & Jung, H. Dual normalization for deep imputation of incomplete industrial time series: a staged
> evaluation with pre-specified decision rules. Manuscript submitted to the *Journal of Computational Design and Engineering*.

## Steps

| Step | Question | Plan | Script | Report |
| --- | --- | --- | --- | --- |
| 1 | Architecture or normalization? | `step1_outputs/PLAN_step1.md` | `step1_decompose.py` | `step1_outputs/REPORT_step1.md` |
| 2, 2b | Reliability-weighted shrinkage on development data | `step2_outputs/PLAN_step2.md`, `step2b_outputs/PLAN_step2b.md` | `step2_shrink.py`, `step2b_shrink.py` | `step2*_outputs/REPORT_*.md` |
| 3 | Shrinkage on independent data (motors, hydraulic rig) | `step3_outputs/PLAN_step3.md` | `step3_independent.py` | `step3_outputs/REPORT_step3.md` |
| 4 | Development of dual normalization | `step4_outputs/PLAN_step4.md`, `step4_outputs/DEV_DECISION_step4.md` | `step4_dual.py`, `step4_guard_analysis.py` | `step4_outputs/REPORT_step4.md` |
| 5 | Pre-specified confirmation (C-MAPSS, MetroPT-3) | `step5_outputs/PLAN_step5.md` | `step5_confirm.py` | `step5_outputs/REPORT_step5.md` |
| 6 | Controls on the Step 5 test data: seed ensembles and ablations | `step6_outputs/PLAN_step6.md` | `step6_controls.py` | `step6_outputs/REPORT_step6.md` |
| 7 | Post hoc robustness: observed-only global statistics, separate calibration units, guard stress test, unit-level bootstrap | `step7_outputs/PLAN_step7.md` | `step7_robustness.py` | `step7_outputs/REPORT_step7.md`, `step7_outputs/REPORT_units_step5.md` |

Each plan was written by its analysis script, with a time stamp, before the first job of its step; from Step 3 on it
records the SHA-256 hash of the script, and every result file records the hash of the script that produced it. The
plans were not lodged with an independent registry, and the commit dates of this repository are upload dates, not
plan dates; the time stamp is the "Written" line of each plan. Table S10 of the supplementary material compares plan,
result and data time stamps.

The run tables in each `stepN_outputs/` folder (`step*_all_runs.csv`, `step5_jobs.csv`, `step6_runs.csv`,
`step7_jobs.csv`) hold one row per job: settings, RMSE, run time and, from Step 3 on, the hash of the script that
produced it. The per-job result files and the stored imputations (about 1 GB) are not included; the scripts recreate
them. `step4_outputs/step4_step3_reproduction.csv` lists the 280 reproduction jobs (Step 3 RMSE, rerun RMSE,
difference).

## Running

Python 3.12, PyTorch 2.11 (CUDA 12.8), PyPOTS, scikit-learn, pandas. Run every command from the repository root.
Shared code: `dtin_core.py`, `dtin_v2.py`, `dtin_v2_eval.py`, `dtin_improve.py`; settings in `dtin_outputs/config.json`
and the SAITS configuration selected on development data in `dtin_outputs/final_v2/selected_saits.json`. Each step
script has the commands `plan`, `run`, `status` and `report` (Steps 3 and 5 also `fetch`/`prepare`, Step 7 also
`check` and `units`); `run --worker k --n-workers K` splits the jobs over parallel workers on one GPU. A plan file that
already exists is never overwritten. Runs use deterministic algorithms; a rerun of the 280 Step 3 jobs of seeds 0-4
reproduced their results to within 5.9e-9 in RMSE.

Data placement: the Siemens file `SmA-Four-Tank-Batch-Process_V2.csv` in the repository root (download it from the
source below); ECG200 is downloaded into `data/` on first use; the hydraulic, C-MAPSS and MetroPT-3 data are
downloaded by the `fetch` commands of Steps 3 and 5. For the motors, replace `load_motor` in `step3_independent.py`
and `step4_dual.py` by `load_motor_release` from `data/motor_anonymized/load_motor_release.py`, which rebuilds the 983
analysis windows and the splits of every seed exactly (see `data/motor_anonymized/README.md`).

## Data

| Dataset | Source | Licence |
| --- | --- | --- |
| Siemens SmA four-tank batch process | https://github.com/thomasbierweiler/FaultsOf4-TankBatchProcess | see source |
| ECG200 | UCR Time Series Classification Archive | see source |
| Hydraulic test rig | UCI, https://doi.org/10.24432/C5CW21 | CC BY 4.0 |
| C-MAPSS (FD001, FD003) | NASA Prognostics Center of Excellence data repository | see source |
| MetroPT-3 | UCI, https://doi.org/10.24432/C5VW3R | CC BY 4.0 |
| Industrial motors | this repository, `data/motor_anonymized/` (see its README) | released with the operator's permission (licence to be added) |

C-MAPSS is a widely used public benchmark; its general properties were known to the authors from the literature
before Step 5, but it had not been used in any earlier step of this study. The public datasets are downloaded by the
`fetch` commands and are not redistributed here.

## Figures

`figures/src/` rebuilds every figure of the paper from `figdata.json` (extracted from the per-run result files).
