from jstyle import *
import json, numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, NullFormatter, FuncFormatter, NullLocator
setup()
D = json.load(open('figdata.json'))
models = ["KNN", "SAITS", "Transformer"]
def fmt(v, _): return f"{v:g}"
def rows_layout():
    ys, heads = {}, {}
    y = 0
    for mo in models:
        heads[mo] = y; y -= 1.0
        for c in CONDS:
            ys[(mo, c)] = y; y -= 1.0
        y -= 0.35
    return ys, heads, y
SER = [("global", "Global standardization"), ("seq", "Per-sequence normalization"), ("dual", "Dual normalization")]
def handles(keys=SER, ms=4.6):
    return [Line2D([], [], ls="", marker=MK[k], ms=ms, mfc=COL[k], mec="white", mew=0.4, label=l) for k, l in keys]
def dotplot(rows, keys, xlim, ticks, xlabel, legend_above):
    def f(ax, standalone):
        ys, heads, ymin = rows_layout()
        for r in rows:
            y = ys[(r["model"], r["cond"])]
            vals = [r[k] for k, _ in keys]
            ax.plot([min(vals), max(vals)], [y, y], color="#cfcfcf", lw=1.2, zorder=2, solid_capstyle="round")
            for k, _ in keys:
                ax.scatter(r[k], y, s=20, marker=MK.get(k, "o"), facecolor=COL[k], edgecolor="white", linewidth=0.4, zorder=4 if k == "dual" else 3)
        ax.axvline(1, color=INK2, lw=0.7, ls=(0, (3, 2)), zorder=1)
        ax.set_xscale("log"); ax.set_xlim(*xlim)
        ax.xaxis.set_major_locator(FixedLocator(ticks)); ax.xaxis.set_major_formatter(FuncFormatter(fmt))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_yticks([ys[k] for k in ys]); ax.set_yticklabels([COND[k[1]] for k in ys])
        ax.tick_params(axis="y", length=0, pad=2)
        for mo, yh in heads.items():
            ax.text(0.015, yh, mo, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=7.4, weight="bold", color=INK, bbox=dict(fc="white", ec="none", pad=0.8), zorder=6)
        ax.set_ylim(ymin + 0.6, 0.7)
        ax.grid(True, axis="x", color=GRID, lw=0.5, zorder=0); ax.set_axisbelow(True)
        ax.spines["left"].set_visible(False)
        ax.set_xlabel(xlabel)
        if standalone and legend_above:
            ax.legend(handles=handles(keys), loc="lower left", bbox_to_anchor=(-0.22, 1.0), ncol=2, columnspacing=0.8, handletextpad=0.1, labelspacing=0.3, fontsize=6.8)
    return f
if __name__ == "__main__":
    f5 = D["f5"]
    cm = [r for r in f5 if r["ds"] == "CMAPSS"]; mp = [r for r in f5 if r["ds"] == "MetroPT"]
    def leg(fig, W, H):
        fig.legend(handles=handles(), loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=3, columnspacing=1.6, handletextpad=0.2)
    panels("fig_5", [dotplot(cm, SER, (0.92, 1.1), [0.94, 0.97, 1, 1.03, 1.06, 1.09], "RMSE / better single normalization", True),
                     dotplot(mp, SER, (0.87, 2.3), [0.9, 1, 1.25, 1.5, 2], "RMSE / better single normalization", False)],
           pw=7.8, ph=8.4, margins=(1.6, 0.25, 0.95, 0.75), legend=leg, legend_h=0.45, solo_top=[0.55, 0])
