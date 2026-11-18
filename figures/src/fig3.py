from jstyle import *
import numpy as np, pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, NullFormatter, FuncFormatter
setup()
import json
s3 = pd.DataFrame(json.load(open('figdata.json'))['f3'])
p = s3.pivot_table(index=['dataset', 'cond', 'method', 'seed'], columns='norm', values='rmse')
orc = p[['global', 'seq']].min(axis=1)
R = p.div(orc, axis=0)
SHR = "#6b6b6b"
meth = [("global", GLOB, "s", "Global standardization"), ("seq", SEQ, "^", "Per-sequence normalization"), ("shrink", SHR, "D", "Reliability-weighted shrinkage")]
models = ["KNN", "SAITS", "Transformer"]
rng = np.random.default_rng(7)
def fmt(v, _): return f"{v:g}"
def draw(ds, ylim, ticks):
    def f(ax, standalone):
        grid(ax)
        for i, mo in enumerate(models):
            for k, (nm, c, mk, lab) in enumerate(meth):
                y = R.xs((ds, mo), level=('dataset', 'method'))[nm].values
                x = i + (k - 1)*0.27 + rng.uniform(-0.07, 0.07, len(y))
                ax.scatter(x, y, s=9, marker=mk, facecolor=c, edgecolor="white", linewidth=0.3, alpha=0.9, zorder=3)
        ax.axhline(1, color=INK2, lw=0.7, ls=(0, (3, 2)), zorder=2)
        ax.set_yscale("log"); ax.set_ylim(*ylim)
        ax.yaxis.set_major_locator(FixedLocator(ticks)); ax.yaxis.set_major_formatter(FuncFormatter(fmt))
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_xticks(range(3)); ax.set_xticklabels(models); ax.set_xlim(-0.55, 2.55)
        ax.tick_params(axis="x", length=0)
        ax.set_ylabel("RMSE / better normalization (per seed)")
        if ds == "Motor":
            ax.text(1.0, 21, "seeds with motor M04 in the test set", ha="center", va="center", fontsize=7, color=INK2)
            ax.text(1.0, 2.55, "other seeds", ha="center", va="center", fontsize=7, color=INK2)
            h = [Line2D([], [], ls="", marker=mk, ms=4.2, mfc=c, mec="white", mew=0.3, label=lab) for nm, c, mk, lab in meth]
            ax.legend(handles=h, loc="center", bbox_to_anchor=(0.5, 0.40), handletextpad=0.2, borderaxespad=0.2, labelspacing=0.3)
    return f
panels("fig_3", [draw("Motor", (0.7, 170), [0.8, 1, 2, 5, 10, 20, 50, 100]), draw("Hydraulic", (0.8, 4.5), [0.8, 1, 1.5, 2, 3, 4])],
       pw=7.7, ph=6.6, margins=(1.25, 0.15, 0.6, 0.15))
print(R.groupby(level=['dataset','method']).agg(['min','max']).round(2))
