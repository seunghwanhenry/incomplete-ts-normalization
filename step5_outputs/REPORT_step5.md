# Step 5 report (confirmation)

Script versions in the results: ['f3492a1c5edd50c845b4509ed4108883f64e8390ac4748c4164f32d72a08658d']

## Mean RMSE per cell and ratio of dual to the better single normalization

```
                                dual  global     seq  oracle   ratio      LR
dataset cond     model                                                      
CMAPSS  GAP 0.4  KNN          0.4906  0.5184  0.5163  0.5163  0.9502  0.4861
                 SAITS        0.4503  0.4562  0.4706  0.4562  0.9870  0.4861
                 Transformer  0.4425  0.4446  0.4677  0.4446  0.9954  0.4861
        MCAR 0.3 KNN          0.4895  0.5157  0.5169  0.5157  0.9492  0.4820
                 SAITS        0.4454  0.4505  0.4639  0.4505  0.9887  0.4820
                 Transformer  0.4394  0.4405  0.4623  0.4405  0.9976  0.4820
        MCAR 0.7 KNN          0.5035  0.5543  0.5339  0.5339  0.9430  0.5404
                 SAITS        0.4647  0.4717  0.4996  0.4717  0.9852  0.5404
                 Transformer  0.4580  0.4622  0.4962  0.4622  0.9911  0.5404
        MNAR 0.3 KNN          0.5201  0.5577  0.5411  0.5411  0.9613  0.5117
                 SAITS        0.4779  0.4907  0.4943  0.4907  0.9740  0.5117
                 Transformer  0.4690  0.4726  0.4948  0.4726  0.9925  0.5117
MetroPT GAP 0.4  KNN          0.4515  0.4753  0.5346  0.4753  0.9501  0.8898
                 SAITS        0.1846  0.2013  0.2735  0.2013  0.9173  0.8898
                 Transformer  0.1481  0.1533  0.2599  0.1533  0.9658  0.8898
        MCAR 0.3 KNN          0.3721  0.4104  0.4017  0.4017  0.9262  0.7807
                 SAITS        0.1124  0.1251  0.1400  0.1251  0.8986  0.7807
                 Transformer  0.1176  0.1189  0.2501  0.1189  0.9892  0.7807
        MCAR 0.7 KNN          0.4935  0.5307  0.5518  0.5307  0.9299  0.8113
                 SAITS        0.1798  0.1951  0.2810  0.1951  0.9215  0.8113
                 Transformer  0.1773  0.1852  0.3198  0.1852  0.9575  0.8113
        MNAR 0.3 KNN          0.4965  0.5498  0.5342  0.5342  0.9295  0.9540
                 SAITS        0.1552  0.1722  0.2039  0.1722  0.9010  0.9540
                 Transformer  0.1517  0.1633  0.2376  0.1633  0.9293  0.9540
```

* H1: cells with dual <= 1.02 x oracle: 24 of 24 (rule: at least 90%) -> **supported**
* H2: geometric mean dual / seq = 0.820, dual / global = 0.950 (rule: both <= 0.98) -> **supported**
* H3: worst ratio to the oracle = 0.998 (rule: every cell <= 1.1) -> **supported**

## Seed level: dual / better single normalization in the same seed

```
                                min    50%    max
dataset cond     model                           
CMAPSS  GAP 0.4  KNN          0.949  0.950  0.954
                 SAITS        0.982  0.987  0.992
                 Transformer  0.990  0.996  1.000
        MCAR 0.3 KNN          0.948  0.949  0.953
                 SAITS        0.987  0.988  0.994
                 Transformer  0.995  0.998  0.999
        MCAR 0.7 KNN          0.937  0.941  0.953
                 SAITS        0.981  0.986  0.989
                 Transformer  0.988  0.991  0.996
        MNAR 0.3 KNN          0.948  0.962  0.968
                 SAITS        0.970  0.981  0.992
                 Transformer  0.978  0.995  0.998
MetroPT GAP 0.4  KNN          0.916  0.949  0.975
                 SAITS        0.847  0.933  1.064
                 Transformer  0.923  0.984  1.017
        MCAR 0.3 KNN          0.918  0.929  0.948
                 SAITS        0.812  0.922  1.018
                 Transformer  0.948  0.993  1.026
        MCAR 0.7 KNN          0.900  0.930  0.965
                 SAITS        0.864  0.934  0.961
                 Transformer  0.905  0.957  1.013
        MNAR 0.3 KNN          0.915  0.937  0.971
                 SAITS        0.835  0.908  0.976
                 Transformer  0.840  0.950  0.996
```

## Median over test units of the per-unit RMSE (mean over seeds)

```
variant                         dual  global     seq
dataset cond     model                              
CMAPSS  GAP 0.4  KNN          0.4567  0.4788  0.4819
                 SAITS        0.4362  0.4410  0.4488
                 Transformer  0.4318  0.4328  0.4477
        MCAR 0.3 KNN          0.4568  0.4802  0.4821
                 SAITS        0.4366  0.4408  0.4459
                 Transformer  0.4313  0.4321  0.4447
        MCAR 0.7 KNN          0.4671  0.4945  0.4988
                 SAITS        0.4421  0.4476  0.4684
                 Transformer  0.4367  0.4386  0.4660
        MNAR 0.3 KNN          0.5143  0.5452  0.5319
                 SAITS        0.4793  0.4882  0.4953
                 Transformer  0.4738  0.4756  0.4959
MetroPT GAP 0.4  KNN          0.4374  0.4497  0.5348
                 SAITS        0.1636  0.1709  0.2629
                 Transformer  0.1218  0.1214  0.2486
        MCAR 0.3 KNN          0.3498  0.3806  0.3810
                 SAITS        0.1004  0.1031  0.1342
                 Transformer  0.0980  0.0975  0.2412
        MCAR 0.7 KNN          0.4796  0.5014  0.5460
                 SAITS        0.1618  0.1677  0.2796
                 Transformer  0.1546  0.1556  0.3203
        MNAR 0.3 KNN          0.4826  0.5051  0.5253
                 SAITS        0.1367  0.1436  0.2026
                 Transformer  0.1351  0.1350  0.2394
```

## Window guard: share of test windows using seq only

```
dataset  cond    
CMAPSS   GAP 0.4     0.0000
         MCAR 0.3    0.0000
         MCAR 0.7    0.0007
         MNAR 0.3    0.0000
MetroPT  GAP 0.4     0.0000
         MCAR 0.3    0.0000
         MCAR 0.7    0.0000
         MNAR 0.3    0.0000
```

## Mean dual weight on global (validation estimate)

```
model              KNN  SAITS  Transformer
dataset cond                              
CMAPSS  GAP 0.4   0.46   0.62         0.79
        MCAR 0.3  0.45   0.59         0.78
        MCAR 0.7  0.43   0.69         0.79
        MNAR 0.3  0.41   0.57         0.78
MetroPT GAP 0.4   0.62   0.69         0.86
        MCAR 0.3  0.48   0.65         0.92
        MCAR 0.7  0.54   0.70         0.78
        MNAR 0.3  0.47   0.63         0.77
```

## Downstream AUROC (descriptive; mean over seeds with both classes present)

```
label                         KNN-dual  KNN-global  KNN-seq     LR  SAITS-dual  SAITS-global  SAITS-seq  Transformer-dual  Transformer-global  Transformer-seq  complete
dataset task        cond                                                                                                                                                
CMAPSS  auc_late60  GAP 0.4      1.000       1.000    1.000  1.000       1.000         1.000      1.000             1.000               1.000            1.000     1.000
                    MCAR 0.3     1.000       1.000    1.000  1.000       1.000         1.000      1.000             1.000               1.000            1.000     1.000
                    MCAR 0.7     1.000       1.000    1.000  1.000       1.000         1.000      1.000             1.000               1.000            1.000     1.000
                    MNAR 0.3     1.000       1.000    1.000  1.000       1.000         1.000      1.000             1.000               1.000            1.000     1.000
        auc_late90  GAP 0.4      0.994       0.994    0.995  0.995       0.994         0.994      0.994             0.994               0.994            0.994     0.994
                    MCAR 0.3     0.995       0.993    0.996  0.996       0.994         0.994      0.994             0.994               0.994            0.995     0.994
                    MCAR 0.7     0.988       0.984    0.987  0.991       0.990         0.990      0.989             0.990               0.989            0.990     0.994
                    MNAR 0.3     0.995       0.993    0.996  0.996       0.994         0.994      0.994             0.994               0.994            0.995     0.994
MetroPT auc_failure GAP 0.4      0.972       0.968    0.971  0.970       0.971         0.969      0.971             0.961               0.959            0.964     0.971
                    MCAR 0.3     0.970       0.961    0.971  0.968       0.971         0.968      0.972             0.967               0.966            0.973     0.971
                    MCAR 0.7     0.979       0.971    0.979  0.980       0.974         0.971      0.975             0.968               0.965            0.978     0.971
                    MNAR 0.3     0.969       0.965    0.969  0.970       0.971         0.969      0.972             0.970               0.968            0.972     0.971
```

Runs without strict determinism: 0