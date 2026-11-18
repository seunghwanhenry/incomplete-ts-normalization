# Step 6 report (controls)

## Dual normalization versus seed ensembles of one normalization (same training cost)

```
variant                         dual  ens_global  ens_seq  global     seq  best_ens   ratio
dataset cond     model                                                                     
CMAPSS  GAP 0.4  SAITS        0.4503      0.4488   0.4687  0.4562  0.4706    0.4488  1.0032
                 Transformer  0.4425      0.4418   0.4653  0.4446  0.4677    0.4418  1.0017
        MCAR 0.3 SAITS        0.4454      0.4456   0.4619  0.4505  0.4639    0.4456  0.9996
                 Transformer  0.4394      0.4388   0.4597  0.4405  0.4623    0.4388  1.0014
        MCAR 0.7 SAITS        0.4647      0.4638   0.4955  0.4717  0.4996    0.4638  1.0020
                 Transformer  0.4580      0.4580   0.4939  0.4622  0.4962    0.4580  1.0000
        MNAR 0.3 SAITS        0.4779      0.4810   0.4877  0.4907  0.4943    0.4810  0.9937
                 Transformer  0.4690      0.4688   0.4882  0.4726  0.4948    0.4688  1.0006
MetroPT GAP 0.4  SAITS        0.1846      0.1863   0.2553  0.2013  0.2735    0.1863  0.9909
                 Transformer  0.1508      0.1490   0.2538  0.1556  0.2607    0.1490  1.0122
        MCAR 0.3 SAITS        0.1124      0.1193   0.1265  0.1251  0.1400    0.1193  0.9423
                 Transformer  0.1176      0.1147   0.2223  0.1189  0.2501    0.1147  1.0253
        MCAR 0.7 SAITS        0.1798      0.1821   0.2645  0.1951  0.2810    0.1821  0.9874
                 Transformer  0.1773      0.1770   0.3057  0.1852  0.3198    0.1770  1.0015
        MNAR 0.3 SAITS        0.1552      0.1624   0.1965  0.1722  0.2039    0.1624  0.9554
                 Transformer  0.1517      0.1570   0.2257  0.1633  0.2376    0.1570  0.9667
```

* H4: dual < better seed ensemble in 8 of 16 cells (rule: at least 12) -> **not supported**
* H5: dual <= 1.02 x better seed ensemble in 15 of 16 cells (rule: at least 90%) -> **supported**
* geometric mean dual / better seed ensemble = 0.993; dual / ensemble of global = 0.993; dual / ensemble of seq = 0.802

Seed level: dual below the better seed ensemble in 48% of 160 seed-cells.

## Ablations on the Step 5 predictions: ratio to the better single normalization

```
variant                        dual  abl_no_guard  abl_equal  abl_pooled  abl_select
dataset cond     model                                                              
CMAPSS  GAP 0.4  KNN          0.950         0.950      0.950       0.951       0.993
                 SAITS        0.987         0.987      0.990       0.988       1.001
                 Transformer  0.995         0.995      1.003       0.996       1.000
        MCAR 0.3 KNN          0.949         0.949      0.949       0.950       0.991
                 SAITS        0.989         0.989      0.994       0.991       0.999
                 Transformer  0.998         0.998      1.006       0.998       1.000
        MCAR 0.7 KNN          0.943         0.943      0.948       0.947       0.991
                 SAITS        0.985         0.985      0.992       0.986       1.001
                 Transformer  0.991         0.991      1.001       0.992       1.000
        MNAR 0.3 KNN          0.961         0.961      0.964       0.963       1.001
                 SAITS        0.974         0.974      0.978       0.978       0.985
                 Transformer  0.992         0.992      1.004       0.997       0.998
MetroPT GAP 0.4  KNN          0.950         0.950      0.973       0.963       0.973
                 SAITS        0.917         0.917      0.983       0.939       0.987
                 Transformer  0.969         0.969      1.121       0.969       1.016
        MCAR 0.3 KNN          0.926         0.926      0.940       0.943       0.959
                 SAITS        0.899         0.899      0.906       0.909       0.963
                 Transformer  0.989         0.989      1.302       0.989       1.019
        MCAR 0.7 KNN          0.930         0.930      0.946       0.945       0.962
                 SAITS        0.922         0.922      1.009       0.942       1.005
                 Transformer  0.957         0.957      1.138       0.971       1.005
        MNAR 0.3 KNN          0.930         0.930      0.955       0.958       0.957
                 SAITS        0.901         0.901      0.932       0.934       0.957
                 Transformer  0.929         0.929      1.042       0.963       0.994
```

Geometric means: dual 0.955, abl_no_guard 0.955, abl_equal 0.998, abl_pooled 0.965, abl_select 0.990

## Training and imputation time per member (seconds, Step 5 runs, median)

```
norm                 global    seq
dataset method                    
CMAPSS  KNN             1.0    1.0
        SAITS         174.0  114.0
        Transformer   196.0   44.0
MetroPT KNN             9.0    8.0
        SAITS         217.0  219.0
        Transformer   194.0  166.0
```

Step 6 runs without strict determinism: 0