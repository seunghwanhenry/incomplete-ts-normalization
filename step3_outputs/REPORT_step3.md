# Step 3 report

Jobs finished: 800 of 800
Script versions in the results: ['1ccb47c1f3adda966c2549bea317ebba6f1188315b676b50311c2d82fb1269d3']

## Motor: mean RMSE

```
cond                GAP 0.4  MCAR 0.3  MCAR 0.7  MNAR 0.3
label                                                    
KNN-global          25.2367   25.3789   25.2630   35.5389
KNN-seq              0.9830    0.9634    1.0517    1.1763
KNN-shrink           0.9830    0.9646    1.0612    1.1946
Linear regression    0.9212    0.9767    1.0124    1.1495
SAITS-global        24.9818   25.1875   25.1035   35.2983
SAITS-seq            0.8105    0.5987    0.8668    0.6936
SAITS-shrink         0.8503    0.6195    0.8440    0.7572
Transformer-global  25.3286   25.3725   25.2652   35.7749
Transformer-seq      0.7928    0.6110    0.8530    0.7172
Transformer-shrink   0.8370    0.5971    0.8947    0.8147
```

## Hydraulic: mean RMSE

```
cond                GAP 0.4  MCAR 0.3  MCAR 0.7  MNAR 0.3
label                                                    
KNN-global           0.1117    0.0999    0.1265    0.1268
KNN-seq              0.3168    0.1083    0.2091    0.1484
KNN-shrink           0.3110    0.0999    0.1837    0.1433
Linear regression    0.6318    0.5150    0.5400    0.5899
SAITS-global         0.1150    0.0706    0.1035    0.1045
SAITS-seq            0.2670    0.0541    0.1460    0.0905
SAITS-shrink         0.2639    0.0535    0.1362    0.0864
Transformer-global   0.0892    0.0743    0.0957    0.0920
Transformer-seq      0.2736    0.0960    0.1756    0.1270
Transformer-shrink   0.2723    0.0861    0.1693    0.1222
```

## H1' - shrink versus the better of global and seq (RMSE)

| dataset | condition | model | global | seq | shrink | shrink / better | within 2% | seeds within 2% | worse / better |
|---|---|---|---|---|---|---|---|---|---|
| Motor | MCAR 0.3 | KNN | 25.3789 | 0.9634 | 0.9646 | 1.001 | yes | 10/10 | 26.343 |
| Motor | MCAR 0.3 | SAITS | 25.1875 | 0.5987 | 0.6195 | 1.035 | no | 4/10 | 42.070 |
| Motor | MCAR 0.3 | Transformer | 25.3725 | 0.6110 | 0.5971 | 0.977 | yes | 6/10 | 41.527 |
| Motor | MCAR 0.7 | KNN | 25.2630 | 1.0517 | 1.0612 | 1.009 | yes | 8/10 | 24.020 |
| Motor | MCAR 0.7 | SAITS | 25.1035 | 0.8668 | 0.8440 | 0.974 | yes | 8/10 | 28.961 |
| Motor | MCAR 0.7 | Transformer | 25.2652 | 0.8530 | 0.8947 | 1.049 | no | 3/10 | 29.618 |
| Motor | MNAR 0.3 | KNN | 35.5389 | 1.1763 | 1.1946 | 1.016 | yes | 8/10 | 30.213 |
| Motor | MNAR 0.3 | SAITS | 35.2983 | 0.6936 | 0.7572 | 1.092 | no | 5/10 | 50.893 |
| Motor | MNAR 0.3 | Transformer | 35.7749 | 0.7172 | 0.8147 | 1.136 | no | 3/10 | 49.880 |
| Motor | GAP 0.4 | KNN | 25.2367 | 0.9830 | 0.9830 | 1.000 | yes | 10/10 | 25.673 |
| Motor | GAP 0.4 | SAITS | 24.9818 | 0.8105 | 0.8503 | 1.049 | no | 8/10 | 30.823 |
| Motor | GAP 0.4 | Transformer | 25.3286 | 0.7928 | 0.8370 | 1.056 | no | 7/10 | 31.949 |
| Hydraulic | MCAR 0.3 | KNN | 0.0999 | 0.1083 | 0.0999 | 1.001 | yes | 4/10 | 1.085 |
| Hydraulic | MCAR 0.3 | SAITS | 0.0706 | 0.0541 | 0.0535 | 0.989 | yes | 5/10 | 1.304 |
| Hydraulic | MCAR 0.3 | Transformer | 0.0743 | 0.0960 | 0.0861 | 1.159 | no | 3/10 | 1.292 |
| Hydraulic | MCAR 0.7 | KNN | 0.1265 | 0.2091 | 0.1837 | 1.452 | no | 0/10 | 1.653 |
| Hydraulic | MCAR 0.7 | SAITS | 0.1035 | 0.1460 | 0.1362 | 1.316 | no | 0/10 | 1.410 |
| Hydraulic | MCAR 0.7 | Transformer | 0.0957 | 0.1756 | 0.1693 | 1.770 | no | 0/10 | 1.836 |
| Hydraulic | MNAR 0.3 | KNN | 0.1268 | 0.1484 | 0.1433 | 1.131 | no | 2/10 | 1.170 |
| Hydraulic | MNAR 0.3 | SAITS | 0.1045 | 0.0905 | 0.0864 | 0.955 | yes | 9/10 | 1.155 |
| Hydraulic | MNAR 0.3 | Transformer | 0.0920 | 0.1270 | 0.1222 | 1.329 | no | 0/10 | 1.381 |
| Hydraulic | GAP 0.4 | KNN | 0.1117 | 0.3168 | 0.3110 | 2.785 | no | 0/10 | 2.837 |
| Hydraulic | GAP 0.4 | SAITS | 0.1150 | 0.2670 | 0.2639 | 2.294 | no | 0/10 | 2.320 |
| Hydraulic | GAP 0.4 | Transformer | 0.0892 | 0.2736 | 0.2723 | 3.052 | no | 0/10 | 3.066 |

cells within 2%: 9 of 24 (38%; 24 cells planned) -> **H1' not supported**

## H3 - transformer versus SAITS (both with seq normalization)

| dataset | condition | RMSE reduction | transformer lower | meets |
|---|---|---|---|---|
| Motor | MNAR 0.3 | -0.034 | 5/10 | no |
| Motor | GAP 0.4 | +0.022 | 5/10 | no |
| Hydraulic | MNAR 0.3 | -0.404 | 0/10 | no |
| Hydraulic | GAP 0.4 | -0.025 | 0/10 | no |

cells meeting the rule: 0 of 4 (4 planned) -> **H3 not supported**

## Motor: downstream down_auc3 (complete-data reference by condition: {'GAP 0.4': 0.92, 'MCAR 0.3': 0.92, 'MCAR 0.7': 0.92, 'MNAR 0.3': 0.92})

```
cond                GAP 0.4  MCAR 0.3  MCAR 0.7  MNAR 0.3
label                                                    
KNN-global            0.918     0.908     0.910     0.912
KNN-seq               0.919     0.920     0.917     0.918
KNN-shrink            0.919     0.919     0.915     0.919
Linear regression     0.919     0.919     0.917     0.917
SAITS-global          0.920     0.911     0.925     0.921
SAITS-seq             0.918     0.919     0.923     0.925
SAITS-shrink          0.918     0.920     0.922     0.925
Transformer-global    0.921     0.911     0.921     0.921
Transformer-seq       0.919     0.920     0.923     0.925
Transformer-shrink    0.920     0.920     0.922     0.925
```

## Motor: downstream down_auc7 (complete-data reference by condition: {'GAP 0.4': 0.911, 'MCAR 0.3': 0.911, 'MCAR 0.7': 0.911, 'MNAR 0.3': 0.911})

```
cond                GAP 0.4  MCAR 0.3  MCAR 0.7  MNAR 0.3
label                                                    
KNN-global            0.890     0.884     0.882     0.902
KNN-seq               0.909     0.910     0.910     0.910
KNN-shrink            0.909     0.910     0.910     0.910
Linear regression     0.908     0.909     0.907     0.909
SAITS-global          0.900     0.894     0.908     0.919
SAITS-seq             0.908     0.911     0.910     0.910
SAITS-shrink          0.909     0.911     0.910     0.910
Transformer-global    0.899     0.894     0.897     0.916
Transformer-seq       0.910     0.911     0.906     0.910
Transformer-shrink    0.910     0.910     0.907     0.910
```

## Motor: downstream down_auc14 (complete-data reference by condition: {'GAP 0.4': 0.911, 'MCAR 0.3': 0.911, 'MCAR 0.7': 0.911, 'MNAR 0.3': 0.911})

```
cond                GAP 0.4  MCAR 0.3  MCAR 0.7  MNAR 0.3
label                                                    
KNN-global            0.883     0.894     0.864     0.879
KNN-seq               0.906     0.911     0.903     0.907
KNN-shrink            0.906     0.910     0.904     0.907
Linear regression     0.903     0.909     0.901     0.907
SAITS-global          0.892     0.902     0.892     0.898
SAITS-seq             0.904     0.911     0.907     0.911
SAITS-shrink          0.905     0.911     0.908     0.911
Transformer-global    0.891     0.897     0.878     0.894
Transformer-seq       0.906     0.912     0.907     0.911
Transformer-shrink    0.906     0.912     0.908     0.910
```

## Hydraulic: downstream down_bacc_mean (complete-data reference by condition: {'GAP 0.4': 0.908, 'MCAR 0.3': 0.908, 'MCAR 0.7': 0.908, 'MNAR 0.3': 0.908})

```
cond                GAP 0.4  MCAR 0.3  MCAR 0.7  MNAR 0.3
label                                                    
KNN-global            0.784     0.806     0.698     0.773
KNN-seq               0.495     0.390     0.311     0.421
KNN-shrink            0.497     0.398     0.317     0.437
Linear regression     0.444     0.514     0.425     0.518
SAITS-global          0.449     0.337     0.334     0.364
SAITS-seq             0.505     0.379     0.328     0.440
SAITS-shrink          0.510     0.389     0.345     0.413
Transformer-global    0.487     0.356     0.332     0.400
Transformer-seq       0.507     0.376     0.354     0.416
Transformer-shrink    0.508     0.392     0.336     0.422
```

## Downstream no-harm (shrink >= better of global and seq - 0.02)

```
       ds         metric        c       model   diff    ok
    Motor      down_auc3 MCAR 0.3         KNN -0.000  True
    Motor      down_auc3 MCAR 0.3       SAITS  0.000  True
    Motor      down_auc3 MCAR 0.3 Transformer  0.000  True
    Motor      down_auc3 MCAR 0.7         KNN -0.002  True
    Motor      down_auc3 MCAR 0.7       SAITS -0.002  True
    Motor      down_auc3 MCAR 0.7 Transformer -0.001  True
    Motor      down_auc3 MNAR 0.3         KNN  0.001  True
    Motor      down_auc3 MNAR 0.3       SAITS  0.000  True
    Motor      down_auc3 MNAR 0.3 Transformer  0.000  True
    Motor      down_auc3  GAP 0.4         KNN  0.000  True
    Motor      down_auc3  GAP 0.4       SAITS -0.002  True
    Motor      down_auc3  GAP 0.4 Transformer -0.001  True
    Motor      down_auc7 MCAR 0.3         KNN -0.001  True
    Motor      down_auc7 MCAR 0.3       SAITS  0.001  True
    Motor      down_auc7 MCAR 0.3 Transformer -0.001  True
    Motor      down_auc7 MCAR 0.7         KNN -0.000  True
    Motor      down_auc7 MCAR 0.7       SAITS  0.000  True
    Motor      down_auc7 MCAR 0.7 Transformer  0.001  True
    Motor      down_auc7 MNAR 0.3         KNN -0.001  True
    Motor      down_auc7 MNAR 0.3       SAITS -0.009  True
    Motor      down_auc7 MNAR 0.3 Transformer -0.006  True
    Motor      down_auc7  GAP 0.4         KNN  0.000  True
    Motor      down_auc7  GAP 0.4       SAITS  0.001  True
    Motor      down_auc7  GAP 0.4 Transformer -0.000  True
    Motor     down_auc14 MCAR 0.3         KNN -0.000  True
    Motor     down_auc14 MCAR 0.3       SAITS -0.000  True
    Motor     down_auc14 MCAR 0.3 Transformer  0.000  True
    Motor     down_auc14 MCAR 0.7         KNN  0.001  True
    Motor     down_auc14 MCAR 0.7       SAITS  0.001  True
    Motor     down_auc14 MCAR 0.7 Transformer  0.001  True
    Motor     down_auc14 MNAR 0.3         KNN  0.001  True
    Motor     down_auc14 MNAR 0.3       SAITS -0.000  True
    Motor     down_auc14 MNAR 0.3 Transformer -0.000  True
    Motor     down_auc14  GAP 0.4         KNN  0.000  True
    Motor     down_auc14  GAP 0.4       SAITS  0.001  True
    Motor     down_auc14  GAP 0.4 Transformer  0.000  True
Hydraulic down_bacc_mean MCAR 0.3         KNN -0.407 False
Hydraulic down_bacc_mean MCAR 0.3       SAITS  0.010  True
Hydraulic down_bacc_mean MCAR 0.3 Transformer  0.016  True
Hydraulic down_bacc_mean MCAR 0.7         KNN -0.380 False
Hydraulic down_bacc_mean MCAR 0.7       SAITS  0.012  True
Hydraulic down_bacc_mean MCAR 0.7 Transformer -0.018  True
Hydraulic down_bacc_mean MNAR 0.3         KNN -0.336 False
Hydraulic down_bacc_mean MNAR 0.3       SAITS -0.028 False
Hydraulic down_bacc_mean MNAR 0.3 Transformer  0.006  True
Hydraulic down_bacc_mean  GAP 0.4         KNN -0.287 False
Hydraulic down_bacc_mean  GAP 0.4       SAITS  0.005  True
Hydraulic down_bacc_mean  GAP 0.4 Transformer  0.001  True
```

cells meeting the rule: 43 of 48 (90%; 48 planned) -> **downstream no-harm not supported**

## Mean shrinkage weights on the test inputs

```
                    w_mean  wl_mean
dataset   cond                     
Hydraulic GAP 0.4    0.969    0.961
          MCAR 0.3   0.960    0.878
          MCAR 0.7   0.887    0.802
          MNAR 0.3   0.916    0.885
Motor     GAP 0.4    0.994    0.993
          MCAR 0.3   0.994    0.994
          MCAR 0.7   0.977    0.971
          MNAR 0.3   0.994    0.994
```

Jobs run without strict determinism: 0