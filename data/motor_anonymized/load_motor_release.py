"""Loader for the anonymized motor release (drop-in for load_motor in step3_independent.py and step4_dual.py).
Each file M01.csv ... M15.csv holds one motor life: 'minute' since the first record (00:00 of the installation day)
and the seven variables. The unit number is the integer of the code (M04 -> 4); the codes follow the ascending order
of the operator's internal unit numbers, so splits drawn from the sorted units are the same as in the study."""
import glob, os, re
import numpy as np, pandas as pd

STAB_HOURS, END_HOURS, T_LEN = 48, 24, 144
BASE = pd.Timestamp("2000-01-01")             # arbitrary origin; only differences matter


def load_motor_release(motor_dir):
    W, meta, cols = [], [], None
    for f in sorted(glob.glob(os.path.join(motor_dir, "M[0-9][0-9].csv"))):
        code = os.path.basename(f)[:-4]; uid = int(code[1:])
        df = pd.read_csv(f)
        df.index = BASE + pd.to_timedelta(df.pop("minute"), unit="min")
        df = df[~df.index.duplicated()].sort_index()
        if cols is None: cols = list(df.columns)
        assert list(df.columns) == cols, (f, list(df.columns))
        t0, t1 = df.index.min(), df.index.max()
        stab = (t0 + pd.Timedelta(hours=STAB_HOURS)).ceil("10min")
        t_end = (t1 - pd.Timedelta(hours=END_HOURS)).floor("10min")       # end of life = start of the replacement day
        g = df.reindex(pd.date_range(stab, t_end, freq="10min", inclusive="left"))
        for k in range(len(g) // T_LEN):
            w = g.iloc[k * T_LEN:(k + 1) * T_LEN]
            if w.isna().any().any():
                continue
            ws, we = w.index[0], w.index[-1]
            W.append(w.to_numpy(np.float64))
            meta.append(dict(unit=uid, name=code, days_end_from_stab=(we - stab).total_seconds() / 86400,
                             days_start_to_end=(t_end - ws).total_seconds() / 86400))
    return np.stack(W), pd.DataFrame(meta), cols
