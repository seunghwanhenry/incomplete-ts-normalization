# Step 2 report

Jobs finished: 450 of 450

## Mean RMSE (all variables)

```
cond                      ECG200 MCAR 0.3  ECG200 MCAR 0.7  Siemens GAP 30  Siemens MAR 0.3  Siemens MCAR 0.3  Siemens MCAR 0.7  Siemens MNAR 0.3
label                                                                                                                                            
BRITS-global                       0.3222           0.4435             NaN              NaN               NaN               NaN               NaN
BRITS-seq                          0.3326           0.4819             NaN              NaN               NaN               NaN               NaN
BRITS-shrink                       0.3083           0.4489             NaN              NaN               NaN               NaN               NaN
DTIN-v2                            0.4174           0.5456          0.2869           0.3097            0.2720            0.3263            0.3630
KNN-global                         0.3880           0.5224          0.6227           0.5756            0.5995            0.6314            0.6350
KNN-seq                            0.4086           0.5792          0.3721           0.4077            0.3938            0.4234            0.4209
KNN-shrink                         0.3880           0.5224          0.3715           0.3777            0.3804            0.3795            0.4343
Linear regression                  0.9804           1.0014          0.3671           0.3696            0.3620            0.3647            0.4557
SAITS-global                       0.4133           0.4890          0.5223           0.4719            0.5000            0.5412            0.5657
SAITS-seq                          0.4170           0.6039          0.3018           0.2837            0.2580            0.3140            0.3655
SAITS-shrink                       0.4002           0.4645          0.3221           0.3458            0.3096            0.3701            0.4073
Transformer-global                 0.3477           0.4211          0.5131           0.4762            0.5003            0.5275            0.5130
Transformer-point-shrink           0.3277           0.4191          0.3388           0.3793            0.3426            0.4277            0.4064
Transformer-seq                    0.3858           0.4954          0.2780           0.2871            0.2431            0.3093            0.3546
Transformer-shrink                 0.3591           0.4326          0.3279           0.3468            0.3299            0.4262            0.4024
```

## Mean RMSE (without PI12002_PV_Out)

```
cond                      Siemens GAP 30  Siemens MAR 0.3  Siemens MCAR 0.3  Siemens MCAR 0.7  Siemens MNAR 0.3
label                                                                                                          
DTIN-v2                           0.2503           0.2540            0.2189            0.2817            0.3331
KNN-global                        0.3397           0.3493            0.3330            0.3698            0.4338
KNN-seq                           0.3337           0.3287            0.3147            0.3270            0.4009
KNN-shrink                        0.3445           0.3415            0.3220            0.3391            0.4092
Linear regression                 0.3413           0.3504            0.3388            0.3437            0.4465
SAITS-global                      0.2683           0.2658            0.2561            0.3012            0.4244
SAITS-seq                         0.2761           0.2518            0.2242            0.2792            0.3536
SAITS-shrink                      0.2947           0.3015            0.2548            0.3345            0.3830
Transformer-global                0.2713           0.2696            0.2741            0.3090            0.3576
Transformer-point-shrink          0.3154           0.3378            0.2901            0.3973            0.3813
Transformer-seq                   0.2565           0.2525            0.2171            0.2784            0.3332
Transformer-shrink                0.3063           0.3032            0.2812            0.3962            0.3781
```

## H1 - shrink normalization versus the better of global and seq

| condition | metric | model | global | seq | shrink | shrink / min(global, seq) | within 2% |
|---|---|---|---|---|---|---|---|
| Siemens MCAR 0.3 | all variables | SAITS | 0.5000 | 0.2580 | 0.3096 | 1.200 | no |
| Siemens MCAR 0.3 | all variables | KNN | 0.5995 | 0.3938 | 0.3804 | 0.966 | yes |
| Siemens MCAR 0.3 | all variables | Transformer | 0.5003 | 0.2431 | 0.3299 | 1.357 | no |
| Siemens MCAR 0.3 | without PI12002_PV_Out | SAITS | 0.2561 | 0.2242 | 0.2548 | 1.136 | no |
| Siemens MCAR 0.3 | without PI12002_PV_Out | KNN | 0.3330 | 0.3147 | 0.3220 | 1.023 | no |
| Siemens MCAR 0.3 | without PI12002_PV_Out | Transformer | 0.2741 | 0.2171 | 0.2812 | 1.295 | no |
| Siemens MAR 0.3 | all variables | SAITS | 0.4719 | 0.2837 | 0.3458 | 1.219 | no |
| Siemens MAR 0.3 | all variables | KNN | 0.5756 | 0.4077 | 0.3777 | 0.926 | yes |
| Siemens MAR 0.3 | all variables | Transformer | 0.4762 | 0.2871 | 0.3468 | 1.208 | no |
| Siemens MAR 0.3 | without PI12002_PV_Out | SAITS | 0.2658 | 0.2518 | 0.3015 | 1.197 | no |
| Siemens MAR 0.3 | without PI12002_PV_Out | KNN | 0.3493 | 0.3287 | 0.3415 | 1.039 | no |
| Siemens MAR 0.3 | without PI12002_PV_Out | Transformer | 0.2696 | 0.2525 | 0.3032 | 1.201 | no |
| Siemens MNAR 0.3 | all variables | SAITS | 0.5657 | 0.3655 | 0.4073 | 1.114 | no |
| Siemens MNAR 0.3 | all variables | KNN | 0.6350 | 0.4209 | 0.4343 | 1.032 | no |
| Siemens MNAR 0.3 | all variables | Transformer | 0.5130 | 0.3546 | 0.4024 | 1.135 | no |
| Siemens MNAR 0.3 | without PI12002_PV_Out | SAITS | 0.4244 | 0.3536 | 0.3830 | 1.083 | no |
| Siemens MNAR 0.3 | without PI12002_PV_Out | KNN | 0.4338 | 0.4009 | 0.4092 | 1.021 | no |
| Siemens MNAR 0.3 | without PI12002_PV_Out | Transformer | 0.3576 | 0.3332 | 0.3781 | 1.135 | no |
| Siemens GAP 30 | all variables | SAITS | 0.5223 | 0.3018 | 0.3221 | 1.067 | no |
| Siemens GAP 30 | all variables | KNN | 0.6227 | 0.3721 | 0.3715 | 0.998 | yes |
| Siemens GAP 30 | all variables | Transformer | 0.5131 | 0.2780 | 0.3279 | 1.179 | no |
| Siemens GAP 30 | without PI12002_PV_Out | SAITS | 0.2683 | 0.2761 | 0.2947 | 1.098 | no |
| Siemens GAP 30 | without PI12002_PV_Out | KNN | 0.3397 | 0.3337 | 0.3445 | 1.032 | no |
| Siemens GAP 30 | without PI12002_PV_Out | Transformer | 0.2713 | 0.2565 | 0.3063 | 1.194 | no |
| Siemens MCAR 0.7 | all variables | SAITS | 0.5412 | 0.3140 | 0.3701 | 1.179 | no |
| Siemens MCAR 0.7 | all variables | KNN | 0.6314 | 0.4234 | 0.3795 | 0.896 | yes |
| Siemens MCAR 0.7 | all variables | Transformer | 0.5275 | 0.3093 | 0.4262 | 1.378 | no |
| Siemens MCAR 0.7 | without PI12002_PV_Out | SAITS | 0.3012 | 0.2792 | 0.3345 | 1.198 | no |
| Siemens MCAR 0.7 | without PI12002_PV_Out | KNN | 0.3698 | 0.3270 | 0.3391 | 1.037 | no |
| Siemens MCAR 0.7 | without PI12002_PV_Out | Transformer | 0.3090 | 0.2784 | 0.3962 | 1.423 | no |
| ECG200 MCAR 0.3 | all variables | SAITS | 0.4133 | 0.4170 | 0.4002 | 0.968 | yes |
| ECG200 MCAR 0.3 | all variables | KNN | 0.3880 | 0.4086 | 0.3880 | 1.000 | yes |
| ECG200 MCAR 0.3 | all variables | Transformer | 0.3477 | 0.3858 | 0.3591 | 1.033 | no |
| ECG200 MCAR 0.3 | all variables | BRITS | 0.3222 | 0.3326 | 0.3083 | 0.957 | yes |
| ECG200 MCAR 0.7 | all variables | SAITS | 0.4890 | 0.6039 | 0.4645 | 0.950 | yes |
| ECG200 MCAR 0.7 | all variables | KNN | 0.5224 | 0.5792 | 0.5224 | 1.000 | yes |
| ECG200 MCAR 0.7 | all variables | Transformer | 0.4211 | 0.4954 | 0.4326 | 1.027 | no |
| ECG200 MCAR 0.7 | all variables | BRITS | 0.4435 | 0.4819 | 0.4489 | 1.012 | yes |

cells within 2%: 10 of 38 (26%); cells more than 2% better than both: 6
**H1 not supported**

## Mean shrinkage weights on the test inputs (w: location, w_l: scale)

```
                  w_mean  wl_mean  rho_mean
cond                                       
ECG200 MCAR 0.3    0.000    0.000     0.941
ECG200 MCAR 0.7    0.000    0.000     0.905
Siemens GAP 30     0.618    0.561     0.563
Siemens MAR 0.3    0.625    0.552     0.556
Siemens MCAR 0.3   0.632    0.560     0.562
Siemens MCAR 0.7   0.608    0.509     0.546
Siemens MNAR 0.3   0.652    0.567     0.549
```

## H2 - mixed versus point masking (transformer, shrink normalization)

| condition | metric | RMSE reduction by mixed masking | mixed better | meets H2 |
|---|---|---|---|---|
| Siemens GAP 30 | all variables | +0.032 | 3/5 | no |
| Siemens GAP 30 | without PI12002_PV_Out | +0.029 | 3/5 | no |
| Siemens MNAR 0.3 | all variables | +0.010 | 3/5 | no |
| Siemens MNAR 0.3 | without PI12002_PV_Out | +0.008 | 3/5 | no |

**H2 not supported**

Jobs run without strict determinism: 0