# Step 1 report

Jobs finished: 275 of 275

## Mean RMSE (all variables)

```
cond                                      ECG200 MCAR 0.3  Siemens GAP 30  Siemens MAR 0.3  Siemens MCAR 0.3  Siemens MNAR 0.3
label                                                                                                                         
BRITS-global                                       0.3305          0.5897           0.4975            0.5337            0.5518
BRITS-seq                                          0.3636          0.3034           0.3078            0.2913            0.3799
DTIN-v2 (mask input + seq-norm)                    0.4161          0.2867           0.3008            0.2767            0.3533
DTIN-v2 w/o mask input                             0.4565          0.2846           0.3007            0.2728            0.3600
DTIN-v2 w/o seq-norm                               0.3525          0.5192           0.4664            0.5061            0.5132
KNN-global                                         0.3880          0.6227           0.5756            0.5995            0.6350
KNN-seq                                            0.4086          0.3721           0.4077            0.3938            0.4209
Linear regression                                  0.9804          0.3671           0.3696            0.3620            0.4557
SAITS-global                                       0.4069          0.5196           0.4735            0.4998            0.5637
SAITS-seq                                          0.4139          0.2976           0.2909            0.2490            0.3632
Transformer (no mask input, no seq-norm)           0.3637          0.5143           0.4730            0.5090            0.5181
```

## Mean RMSE (without PI12002_PV_Out)

```
cond                                      Siemens GAP 30  Siemens MAR 0.3  Siemens MCAR 0.3  Siemens MNAR 0.3
label                                                                                                        
BRITS-global                                      0.2903           0.2495            0.2294            0.3520
BRITS-seq                                         0.2706           0.2475            0.2217            0.3509
DTIN-v2 (mask input + seq-norm)                   0.2517           0.2580            0.2197            0.3306
DTIN-v2 w/o mask input                            0.2508           0.2473            0.2199            0.3355
DTIN-v2 w/o seq-norm                              0.2714           0.2741            0.2729            0.3480
KNN-global                                        0.3397           0.3493            0.3330            0.4338
KNN-seq                                           0.3337           0.3287            0.3147            0.4009
Linear regression                                 0.3413           0.3504            0.3388            0.4465
SAITS-global                                      0.2706           0.2676            0.2594            0.4225
SAITS-seq                                         0.2743           0.2515            0.2238            0.3522
Transformer (no mask input, no seq-norm)          0.2682           0.2661            0.2578            0.3474
```

## R1 check (all variables)

| condition | best normalized baseline B* | RMSE B* | RMSE DTIN-v2 | G | DTIN-v2 better | meets R1 |
|---|---|---|---|---|---|---|
| Siemens MCAR 0.3 | SAITS-seq | 0.2490 | 0.2767 | -0.111 | 0/5 | no |
| Siemens MAR 0.3 | SAITS-seq | 0.2909 | 0.3008 | -0.034 | 1/5 | no |
| Siemens MNAR 0.3 | SAITS-seq | 0.3632 | 0.3533 | +0.027 | 4/5 | no |
| Siemens GAP 30 | SAITS-seq | 0.2976 | 0.2867 | +0.036 | 4/5 | no |

conditions meeting R1: 0 of 4

## R1 check (without PI12002_PV_Out)

| condition | best normalized baseline B* | RMSE B* | RMSE DTIN-v2 | G | DTIN-v2 better | meets R1 |
|---|---|---|---|---|---|---|
| Siemens MCAR 0.3 | BRITS-seq | 0.2217 | 0.2197 | +0.009 | 5/5 | no |
| Siemens MAR 0.3 | BRITS-seq | 0.2475 | 0.2580 | -0.043 | 1/5 | no |
| Siemens MNAR 0.3 | BRITS-seq | 0.3509 | 0.3306 | +0.058 | 5/5 | yes |
| Siemens GAP 30 | BRITS-seq | 0.2706 | 0.2517 | +0.070 | 5/5 | yes |

conditions meeting R1: 2 of 4

## Normalization effects (relative RMSE change, global -> seq; positive = normalization helps)

| condition | KNN | BRITS | SAITS |
|---|---|---|---|
| Siemens MCAR 0.3 | +0.343 | +0.454 | +0.502 |
| Siemens MAR 0.3 | +0.292 | +0.381 | +0.386 |
| Siemens MNAR 0.3 | +0.337 | +0.312 | +0.356 |
| Siemens GAP 30 | +0.402 | +0.485 | +0.427 |
| ECG200 MCAR 0.3 | -0.053 | -0.100 | -0.017 |

N1 (normalization helps on Siemens): yes
N2 (normalization harms on ECG200): yes

## Decision according to the plan: **R2 - normalization explains the advantage**

The transformer architecture is not claimed as a contribution; Step 2 develops the normalization as a model-agnostic component.
Step 2 must include an adaptive rule that is never more than 2% worse than global standardization on development data.

Jobs run without strict determinism: 0