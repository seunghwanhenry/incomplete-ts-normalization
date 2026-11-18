# Step 5 - unit-level analysis (descriptive; written by step7_robustness.py units)

Recomputed cell results (must equal REPORT_step5.md):

* R1: cells with dual <= 1.02 x oracle: 24 of 24 (rule: at least 90% of 24) -> **supported**
* R2: geometric mean dual / seq = 0.821, dual / global = 0.950 (rule: both <= 0.98) -> **supported**
* R3: worst dual / oracle = 0.998 (rule: every cell <= 1.1) -> **supported**

## Bootstrap over test units

```
dataset         stat  n_cells  estimate      lo      hi
 CMAPSS  dual/oracle       12    0.9760  0.9751  0.9770
 CMAPSS  dual/global       12    0.9702  0.9683  0.9723
 CMAPSS     dual/seq       12    0.9485  0.9456  0.9517
 CMAPSS cells_within       12   12.0000 12.0000 12.0000
MetroPT  dual/oracle       12    0.9346  0.9246  0.9471
MetroPT  dual/global       12    0.9307  0.9183  0.9452
MetroPT     dual/seq       12    0.7105  0.6936  0.7274
MetroPT cells_within       12   12.0000 12.0000 12.0000
```

## Unit level: dual / better normalization of the cell

```
                              median    p95          max  share_above_102  n_units
dataset cond     model                                                            
CMAPSS  GAP 0.4  KNN           0.953  0.973        1.009            0.000      600
                 SAITS         0.990  1.003        1.048            0.010      600
                 Transformer   0.998  1.003        1.045            0.003      600
        MCAR 0.3 KNN           0.953  0.977        0.999            0.000      600
                 SAITS         0.992  1.003        1.054            0.008      600
                 Transformer   0.999  1.004        1.022            0.002      600
        MCAR 0.7 KNN           0.939  0.965        1.027            0.002      600
                 SAITS         0.989  1.000        1.054            0.005      600
                 Transformer   0.997  1.003        1.031            0.003      600
        MNAR 0.3 KNN           0.964  0.988        1.078            0.003      600
                 SAITS         0.984  1.007        1.046            0.013      600
                 Transformer   0.997  1.007        1.031            0.002      600
MetroPT GAP 0.4  KNN           0.982  1.055        1.142            0.135      630
                 SAITS         0.973  1.173        1.717            0.240      630
                 Transformer   1.000  1.126        1.407            0.300      630
        MCAR 0.3 KNN           0.914  1.099  4046048.453            0.094      630
                 SAITS         0.971  1.062        1.363            0.148      630
                 Transformer   1.002  1.089        1.511            0.235      630
        MCAR 0.7 KNN           0.971  1.007        1.035            0.017      630
                 SAITS         0.968  1.031        1.463            0.076      630
                 Transformer   0.998  1.064        1.209            0.224      630
        MNAR 0.3 KNN           0.920  1.051  2550035.608            0.068      630
                 SAITS         0.964  1.031        1.366            0.062      630
                 Transformer   1.003  1.096        1.271            0.332      630
```
