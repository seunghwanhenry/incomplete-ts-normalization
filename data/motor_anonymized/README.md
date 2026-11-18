# Industrial motor data (anonymized)

Fifteen motor lives from pump-duty motors at one manufacturing site, from installation to replacement,
recorded every 10 minutes. Released in anonymized form with the operator's written permission.

## Files

| File | Content |
| --- | --- |
| `M01.csv` ... `M15.csv` | one motor life each: `minute` since the first record (00:00 of the installation day) and seven variables |
| `motors.csv` | number of records and recorded length per motor |
| `load_motor_release.py` | loader that rebuilds the analysis windows (drop-in for `load_motor` in the step scripts) |

## Variables

`DP_Current`, `BP_Current`, `Exh_Pressur`, `Exh_Temperature`, `Casing_Temperature`, `N2T`, `N2F`, named as in the
operator's monitoring system; `N2F` is the nitrogen flow discussed in Section 5.3 of the paper. Units are those of
the source system and are not stated in the source files.

## What was removed

* Motor numbers and equipment codes: replaced by M01-M15, assigned in the ascending order of the operator's unit
  numbers. The step plans and reports, written before anonymization, use the unit numbers; there, unit 155 is M04.
* Calendar time: replaced by minutes since the first record. The last record of each file is 00:00 of the day
  after the recorded replacement, as in the source files.
* All other metadata (site, line, maintenance records).

## Reproducing the analysis windows

```python
from load_motor_release import load_motor_release
X, meta, cols = load_motor_release("data/motor_anonymized")   # X: (983, 144, 7)
```

Records start 48 h after the first record (running-in) and end at the start of the replacement day; windows are
144 points (one day) and windows with a missing record are dropped. With the units numbered 1-15 in this order, the
seed-wise splits of Steps 3 and 4 are identical to those in the study (checked for seeds 0-9: identical windows,
identical splits; motor M04 is in the test set for seeds 0, 5, 6 and 9).

## Licence

[To be confirmed with the data owner, e.g. CC BY 4.0.]
