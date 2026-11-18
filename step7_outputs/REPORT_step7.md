# Step 7 report (robustness re-analysis of Step 5; post hoc)

Script versions in the results: ['ea8893efbbf37f8cade41a0afdcf929de3dd1295d044d84d6adc9f8fa42e8979']

## Mean RMSE per cell (clean protocol; Step 5 reporting scale)

```
variant                       global     seq  dual_noguard    dual  oracle   ratio
dataset cond     model                                                            
CMAPSS  GAP 0.4  KNN          0.5213  0.5163        0.4913  0.4913  0.5163  0.9515
                 SAITS        0.4578  0.4697        0.4506  0.4506  0.4578  0.9842
                 Transformer  0.4442  0.4676        0.4433  0.4433  0.4442  0.9978
        MCAR 0.3 KNN          0.5182  0.5172        0.4902  0.4902  0.5172  0.9479
                 SAITS        0.4526  0.4673        0.4480  0.4480  0.4526  0.9897
                 Transformer  0.4403  0.4607        0.4393  0.4393  0.4403  0.9977
        MCAR 0.7 KNN          0.5586  0.5340        0.5048  0.5048  0.5340  0.9454
                 SAITS        0.4740  0.5001        0.4664  0.4664  0.4740  0.9840
                 Transformer  0.4631  0.4977        0.4590  0.4590  0.4631  0.9912
        MNAR 0.3 KNN          0.5589  0.5408        0.5208  0.5208  0.5408  0.9630
                 SAITS        0.4911  0.4939        0.4774  0.4774  0.4911  0.9722
                 Transformer  0.4740  0.4946        0.4695  0.4695  0.4740  0.9905
MetroPT GAP 0.4  KNN          0.4814  0.5390        0.4569  0.4569  0.4814  0.9491
                 SAITS        0.1973  0.2724        0.1849  0.1849  0.1973  0.9375
                 Transformer  0.1533  0.2789        0.1496  0.1496  0.1533  0.9758
        MCAR 0.3 KNN          0.4166  0.4059        0.3769  0.3769  0.4059  0.9284
                 SAITS        0.1254  0.1361        0.1154  0.1154  0.1254  0.9208
                 Transformer  0.1224  0.2580        0.1221  0.1221  0.1224  0.9971
        MCAR 0.7 KNN          0.5359  0.5553        0.4987  0.4987  0.5359  0.9305
                 SAITS        0.2015  0.2826        0.1874  0.1874  0.2015  0.9298
                 Transformer  0.1863  0.3386        0.1815  0.1815  0.1863  0.9740
        MNAR 0.3 KNN          0.5549  0.5405        0.5070  0.5070  0.5405  0.9381
                 SAITS        0.1774  0.2112        0.1587  0.1587  0.1774  0.8949
                 Transformer  0.1684  0.2421        0.1568  0.1568  0.1684  0.9306
```

* R1: cells with dual <= 1.02 x oracle: 24 of 24 (rule: at least 90% of 24) -> **supported**
* R2: geometric mean dual / seq = 0.822, dual / global = 0.953 (rule: both <= 0.98) -> **supported**
* R3: worst dual / oracle = 0.998 (rule: every cell <= 1.1) -> **supported**

## Step 7 / Step 5 cell RMSE

```
variant                       global 7/5  seq 7/5  dual 7/5
dataset cond     model                                     
CMAPSS  GAP 0.4  KNN               1.005    1.000     1.001
                 SAITS             1.004    0.998     1.001
                 Transformer       0.999    1.000     1.002
        MCAR 0.3 KNN               1.005    1.000     1.002
                 SAITS             1.005    1.007     1.006
                 Transformer       1.000    0.996     1.000
        MCAR 0.7 KNN               1.008    1.000     1.003
                 SAITS             1.005    1.001     1.004
                 Transformer       1.002    1.003     1.002
        MNAR 0.3 KNN               1.002    0.999     1.001
                 SAITS             1.001    0.999     0.999
                 Transformer       1.003    1.000     1.001
MetroPT GAP 0.4  KNN               1.013    1.008     1.012
                 SAITS             0.980    0.996     1.002
                 Transformer       0.985    1.070     0.992
        MCAR 0.3 KNN               1.015    1.011     1.013
                 SAITS             1.002    0.972     1.027
                 Transformer       1.029    1.032     1.038
        MCAR 0.7 KNN               1.010    1.006     1.010
                 SAITS             1.033    1.006     1.042
                 Transformer       1.006    1.059     1.024
        MNAR 0.3 KNN               1.009    1.012     1.021
                 SAITS             1.030    1.036     1.023
                 Transformer       1.032    1.019     1.033
```

Geometric mean Step 7 / Step 5: global 1.008, seq 1.009, dual 1.011

## Bootstrap over test units (clean protocol)

```
dataset         stat  n_cells  estimate      lo      hi
 CMAPSS  dual/oracle       12    0.9761  0.9750  0.9772
 CMAPSS  dual/global       12    0.9688  0.9665  0.9714
 CMAPSS     dual/seq       12    0.9498  0.9471  0.9526
 CMAPSS cells_within       12   12.0000 12.0000 12.0000
MetroPT  dual/oracle       12    0.9418  0.9312  0.9544
MetroPT  dual/global       12    0.9377  0.9247  0.9529
MetroPT     dual/seq       12    0.7112  0.6928  0.7291
MetroPT cells_within       12   12.0000 12.0000 12.0000
```

## Unit level: dual / better normalization of the cell (clean protocol)

```
                              median    p95          max  share_above_102  n_units
dataset cond     model                                                            
CMAPSS  GAP 0.4  KNN           0.949  0.972        1.018            0.000      600
                 SAITS         0.989  1.003        1.096            0.010      600
                 Transformer   0.999  1.005        1.145            0.015      600
        MCAR 0.3 KNN           0.953  0.976        0.998            0.000      600
                 SAITS         0.990  1.006        1.124            0.030      600
                 Transformer   0.999  1.006        1.041            0.007      600
        MCAR 0.7 KNN           0.939  0.966        1.081            0.007      600
                 SAITS         0.988  1.002        1.055            0.015      600
                 Transformer   0.997  1.005        1.089            0.007      600
        MNAR 0.3 KNN           0.965  0.990        1.072            0.003      600
                 SAITS         0.983  1.007        1.062            0.010      600
                 Transformer   0.998  1.008        1.026            0.005      600
MetroPT GAP 0.4  KNN           0.982  1.050        1.165            0.135      630
                 SAITS         0.976  1.162        1.430            0.259      630
                 Transformer   1.003  1.142        1.583            0.300      630
        MCAR 0.3 KNN           0.916  1.142  4256745.859            0.095      630
                 SAITS         0.976  1.093        1.716            0.178      630
                 Transformer   1.002  1.154        1.537            0.330      630
        MCAR 0.7 KNN           0.969  1.006        1.035            0.010      630
                 SAITS         0.968  1.047        1.274            0.105      630
                 Transformer   1.005  1.070        1.271            0.337      630
        MNAR 0.3 KNN           0.927  1.064  7452461.938            0.076      630
                 SAITS         0.964  1.075        2.245            0.110      630
                 Transformer   1.006  1.134        1.402            0.341      630
```

## Window guard: share of test windows using seq only

```
k                    0       3       10   100
dataset cond                                 
CMAPSS  GAP 0.4   0.0000  0.0000  0.5901  1.0
        MCAR 0.3  0.0000  0.0000  0.5893  1.0
        MCAR 0.7  0.0007  0.0007  0.5830  1.0
        MNAR 0.3  0.0000  0.0000  0.5624  1.0
MetroPT GAP 0.4   0.0000  0.0103  0.7882  1.0
        MCAR 0.3  0.0000  0.0104  0.7908  1.0
        MCAR 0.7  0.0000  0.0102  0.7891  1.0
        MNAR 0.3  0.0000  0.0136  0.7663  1.0
```

## Mean dual weight on global (calibration half)

```
model              KNN  SAITS  Transformer
dataset cond                              
CMAPSS  GAP 0.4   0.47   0.59         0.78
        MCAR 0.3  0.47   0.55         0.76
        MCAR 0.7  0.44   0.66         0.79
        MNAR 0.3  0.41   0.54         0.76
MetroPT GAP 0.4   0.65   0.71         0.86
        MCAR 0.3  0.50   0.64         0.92
        MCAR 0.7  0.57   0.69         0.83
        MNAR 0.3  0.49   0.62         0.77
```

## Stress test (mean over conditions and seeds)

```
                          rmse                             rmse_shifted                             rmse_other                           
variant                   dual dual_noguard  global    seq         dual dual_noguard  global    seq       dual dual_noguard global    seq
dataset k   model                                                                                                                        
CMAPSS  3   KNN          0.623        0.623   0.940  0.527        1.418        1.418   2.805  0.525      0.511        0.511  0.587  0.527
            SAITS        0.676        0.676   0.909  0.483        1.752        1.752   2.685  0.481      0.504        0.504  0.578  0.483
            Transformer  0.761        0.761   0.883  0.480        2.122        2.122   2.582  0.478      0.525        0.525  0.571  0.480
        10  KNN          0.822        1.319   2.629  0.527        2.289        4.446   9.314  0.525      0.556        0.585  0.859  0.527
            SAITS        0.996        1.638   2.537  0.483        2.872        5.571   8.766  0.481      0.650        0.706  1.008  0.483
            Transformer  1.233        2.053   2.527  0.480        3.471        6.900   8.493  0.478      0.837        0.933  1.148  0.480
        100 KNN          0.527       12.223  26.023  0.527        0.525       45.656  97.257  0.525      0.527        0.687  1.161  0.527
            SAITS        0.483       15.946  25.610  0.483        0.481       59.531  95.597  0.481      0.483        1.108  1.750  0.483
            Transformer  0.480       20.260  25.430  0.480        0.478       75.505  94.768  0.478      0.480        1.784  2.290  0.480
MetroPT 3   KNN          0.859        0.863   1.246  0.510        1.828        1.841   2.890  0.510      0.546        0.547  0.643  0.510
            SAITS        0.885        0.889   1.191  0.226        1.809        1.821   2.467  0.227      0.606        0.607  0.800  0.225
            Transformer  1.110        1.116   1.251  0.279        2.129        2.147   2.424  0.279      0.823        0.826  0.917  0.279
        10  KNN          0.743        2.255   3.567  0.510        0.953        5.559   8.938  0.510      0.688        0.868  1.214  0.510
            SAITS        0.874        2.481   3.434  0.226        1.857        6.102   8.485  0.227      0.503        0.984  1.321  0.225
            Transformer  1.097        3.177   3.629  0.279        2.471        7.758   8.869  0.279      0.580        1.317  1.497  0.279
        100 KNN          0.510       22.308  36.842  0.510        0.510       58.989  97.425  0.510      0.510        0.846  1.263  0.510
            SAITS        0.226       25.587  36.336  0.226        0.227       67.644  96.063  0.227      0.225        1.135  1.532  0.225
            Transformer  0.279       31.580  36.532  0.279        0.279       83.460  96.541  0.279      0.279        1.652  1.900  0.279
```

Runs without strict determinism: 0