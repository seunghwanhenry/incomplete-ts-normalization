# Step 2b report

Jobs finished: 345 of 345

## Mean RMSE (all variables)

```
cond                ECG200 MCAR 0.3  ECG200 MCAR 0.7  Siemens GAP 30  Siemens MAR 0.3  Siemens MCAR 0.3  Siemens MCAR 0.7  Siemens MNAR 0.3
label                                                                                                                                      
BRITS-global                 0.3345           0.4397             NaN              NaN               NaN               NaN               NaN
BRITS-seq                    0.3457           0.4812             NaN              NaN               NaN               NaN               NaN
BRITS-shrink                 0.3345           0.4481             NaN              NaN               NaN               NaN               NaN
KNN-global                   0.3880           0.5224          0.6227           0.5756            0.5995            0.6314            0.6350
KNN-seq                      0.4086           0.5792          0.3721           0.4077            0.3938            0.4234            0.4209
KNN-shrink                   0.3908           0.5278          0.3706           0.4078            0.3922            0.4219            0.4213
SAITS-global                 0.4176           0.5083          0.5216           0.4703            0.5011            0.5414            0.5677
SAITS-seq                    0.4228           0.5486          0.3021           0.2833            0.2708            0.3231            0.3647
SAITS-shrink                 0.3950           0.4819          0.3028           0.2922            0.2588            0.3231            0.3684
Transformer-global           0.3609           0.4274          0.5133           0.4669            0.5017            0.5225            0.5125
Transformer-seq              0.3993           0.4977          0.2847           0.2794            0.2570            0.3078            0.3526
Transformer-shrink           0.3686           0.4319          0.2803           0.2798            0.2563            0.3107            0.3513
```

## Mean RMSE (without PI12002_PV_Out)

```
cond                Siemens GAP 30  Siemens MAR 0.3  Siemens MCAR 0.3  Siemens MCAR 0.7  Siemens MNAR 0.3
label                                                                                                    
KNN-global                  0.3397           0.3493            0.3330            0.3698            0.4338
KNN-seq                     0.3337           0.3287            0.3147            0.3270            0.4009
KNN-shrink                  0.3328           0.3280            0.3142            0.3250            0.4010
SAITS-global                0.2703           0.2657            0.2602            0.3083            0.4214
SAITS-seq                   0.2760           0.2506            0.2250            0.2821            0.3510
SAITS-shrink                0.2760           0.2505            0.2240            0.2816            0.3514
Transformer-global          0.2801           0.2837            0.2662            0.3145            0.3545
Transformer-seq             0.2573           0.2529            0.2169            0.2774            0.3315
Transformer-shrink          0.2556           0.2512            0.2158            0.2740            0.3326
```

## H1 - revised shrink normalization versus the better of global and seq

| condition | metric | model | global | seq | shrink | shrink / min(global, seq) | within 2% |
|---|---|---|---|---|---|---|---|
| Siemens MCAR 0.3 | all variables | SAITS | 0.5011 | 0.2708 | 0.2588 | 0.956 | yes |
| Siemens MCAR 0.3 | all variables | KNN | 0.5995 | 0.3938 | 0.3922 | 0.996 | yes |
| Siemens MCAR 0.3 | all variables | Transformer | 0.5017 | 0.2570 | 0.2563 | 0.997 | yes |
| Siemens MCAR 0.3 | without PI12002_PV_Out | SAITS | 0.2602 | 0.2250 | 0.2240 | 0.996 | yes |
| Siemens MCAR 0.3 | without PI12002_PV_Out | KNN | 0.3330 | 0.3147 | 0.3142 | 0.998 | yes |
| Siemens MCAR 0.3 | without PI12002_PV_Out | Transformer | 0.2662 | 0.2169 | 0.2158 | 0.995 | yes |
| Siemens MAR 0.3 | all variables | SAITS | 0.4703 | 0.2833 | 0.2922 | 1.031 | no |
| Siemens MAR 0.3 | all variables | KNN | 0.5756 | 0.4077 | 0.4078 | 1.000 | yes |
| Siemens MAR 0.3 | all variables | Transformer | 0.4669 | 0.2794 | 0.2798 | 1.001 | yes |
| Siemens MAR 0.3 | without PI12002_PV_Out | SAITS | 0.2657 | 0.2506 | 0.2505 | 0.999 | yes |
| Siemens MAR 0.3 | without PI12002_PV_Out | KNN | 0.3493 | 0.3287 | 0.3280 | 0.998 | yes |
| Siemens MAR 0.3 | without PI12002_PV_Out | Transformer | 0.2837 | 0.2529 | 0.2512 | 0.993 | yes |
| Siemens MNAR 0.3 | all variables | SAITS | 0.5677 | 0.3647 | 0.3684 | 1.010 | yes |
| Siemens MNAR 0.3 | all variables | KNN | 0.6350 | 0.4209 | 0.4213 | 1.001 | yes |
| Siemens MNAR 0.3 | all variables | Transformer | 0.5125 | 0.3526 | 0.3513 | 0.996 | yes |
| Siemens MNAR 0.3 | without PI12002_PV_Out | SAITS | 0.4214 | 0.3510 | 0.3514 | 1.001 | yes |
| Siemens MNAR 0.3 | without PI12002_PV_Out | KNN | 0.4338 | 0.4009 | 0.4010 | 1.000 | yes |
| Siemens MNAR 0.3 | without PI12002_PV_Out | Transformer | 0.3545 | 0.3315 | 0.3326 | 1.003 | yes |
| Siemens GAP 30 | all variables | SAITS | 0.5216 | 0.3021 | 0.3028 | 1.002 | yes |
| Siemens GAP 30 | all variables | KNN | 0.6227 | 0.3721 | 0.3706 | 0.996 | yes |
| Siemens GAP 30 | all variables | Transformer | 0.5133 | 0.2847 | 0.2803 | 0.985 | yes |
| Siemens GAP 30 | without PI12002_PV_Out | SAITS | 0.2703 | 0.2760 | 0.2760 | 1.021 | no |
| Siemens GAP 30 | without PI12002_PV_Out | KNN | 0.3397 | 0.3337 | 0.3328 | 0.998 | yes |
| Siemens GAP 30 | without PI12002_PV_Out | Transformer | 0.2801 | 0.2573 | 0.2556 | 0.993 | yes |
| Siemens MCAR 0.7 | all variables | SAITS | 0.5414 | 0.3231 | 0.3231 | 1.000 | yes |
| Siemens MCAR 0.7 | all variables | KNN | 0.6314 | 0.4234 | 0.4219 | 0.997 | yes |
| Siemens MCAR 0.7 | all variables | Transformer | 0.5225 | 0.3078 | 0.3107 | 1.009 | yes |
| Siemens MCAR 0.7 | without PI12002_PV_Out | SAITS | 0.3083 | 0.2821 | 0.2816 | 0.998 | yes |
| Siemens MCAR 0.7 | without PI12002_PV_Out | KNN | 0.3698 | 0.3270 | 0.3250 | 0.994 | yes |
| Siemens MCAR 0.7 | without PI12002_PV_Out | Transformer | 0.3145 | 0.2774 | 0.2740 | 0.988 | yes |
| ECG200 MCAR 0.3 | all variables | SAITS | 0.4176 | 0.4228 | 0.3950 | 0.946 | yes |
| ECG200 MCAR 0.3 | all variables | KNN | 0.3880 | 0.4086 | 0.3908 | 1.007 | yes |
| ECG200 MCAR 0.3 | all variables | Transformer | 0.3609 | 0.3993 | 0.3686 | 1.021 | no |
| ECG200 MCAR 0.3 | all variables | BRITS | 0.3345 | 0.3457 | 0.3345 | 1.000 | yes |
| ECG200 MCAR 0.7 | all variables | SAITS | 0.5083 | 0.5486 | 0.4819 | 0.948 | yes |
| ECG200 MCAR 0.7 | all variables | KNN | 0.5224 | 0.5792 | 0.5278 | 1.010 | yes |
| ECG200 MCAR 0.7 | all variables | Transformer | 0.4274 | 0.4977 | 0.4319 | 1.011 | yes |
| ECG200 MCAR 0.7 | all variables | BRITS | 0.4397 | 0.4812 | 0.4481 | 1.019 | yes |

cells within 2%: 35 of 38 (92%); cells more than 2% better than both: 3
**H1 supported**

## Mean shrinkage weights on the test inputs (w: location, w_l: scale)

```
                  w_mean  wl_mean
cond                             
ECG200 MCAR 0.3    0.093    0.230
ECG200 MCAR 0.7    0.096    0.296
Siemens GAP 30     0.985    0.715
Siemens MAR 0.3    0.989    0.716
Siemens MCAR 0.3   0.989    0.716
Siemens MCAR 0.7   0.966    0.710
Siemens MNAR 0.3   0.987    0.716
```

## Normalized test inputs: 99.9th percentile and maximum of |z| (largest over models and seeds)

```
                 zin_p999             zin_max             
norm               global  seq shrink  global   seq shrink
cond                                                      
ECG200 MCAR 0.3       3.7  3.6    3.7     4.2   4.1    4.2
ECG200 MCAR 0.7       3.5  3.6    3.6     4.2   3.7    4.1
Siemens GAP 30        5.4  5.6    5.6    70.3  10.3   10.5
Siemens MAR 0.3       5.4  6.1    6.1    70.3  13.4   13.4
Siemens MCAR 0.3      5.4  5.8    5.8    70.3  11.8   11.9
Siemens MCAR 0.7      5.4  5.8    5.8    70.1   8.2    9.5
Siemens MNAR 0.3      4.9  6.1    6.1    70.3  12.2   12.2
```

## Decision according to the plan

H1 supported: the revised normalization is carried to Step 3 unchanged.

Jobs run without strict determinism: 0