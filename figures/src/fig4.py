from jstyle import *
import json, numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, NullFormatter, FuncFormatter
setup()
D = json.load(open('figdata.json'))
GRY = "#7a7a7a"
var = [("seq", "Per-\nsequence", SEQ, "^", True), ("global", "Global", GLOB, "s", True),
       ("sel_var", "Selection", GRY, "D", False), ("comb_var", "Combination", GRY, "o", False),
       ("comb_var_wg", "Combination\n+ guard", DUAL, "o", True)]
rng = np.random.default_rng(11)
def fmt(v, _): return f"{v:g}"
def drawA(ax, standalone):
    grid(ax)
    for i, (k, lab, c, mk, filled) in enumerate(var):
        y = np.array([r["r"] for r in D["f4a"][k]])
        x = i + rng.uniform(-0.2, 0.2, len(y))
        if filled:
            ax.scatter(x, y, s=10, marker=mk, facecolor=c, edgecolor="white", linewidth=0.3, zorder=3)
        else:
            ax.scatter(x, y, s=10, marker=mk, facecolor="white", edgecolor=c, linewidth=0.7, zorder=3)
        n = int((y <= 1.02).sum())
        ax.text(i, 1.035, f"{n}/48", transform=ax.get_xaxis_transform(), clip_on=False, ha="center", va="bottom", fontsize=7.5, color=INK, weight="bold" if k == "comb_var_wg" else "normal")
    ax.axhline(1, color=INK2, lw=0.7, ls=(0, (3, 2)), zorder=2)
    ax.set_yscale("log"); ax.set_ylim(0.5, 45)
    ax.yaxis.set_major_locator(FixedLocator([0.5, 1, 2, 5, 10, 20])); ax.yaxis.set_major_formatter(FuncFormatter(fmt))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks(range(len(var))); ax.set_xticklabels([v[1] for v in var], fontsize=6.9)
    ax.set_xlim(-0.5, len(var) - 0.5); ax.tick_params(axis="x", length=0)
    ax.set_ylabel("RMSE / better single normalization")
kap = ["0", "0.1", "0.25", "0.5", "1", "2", "5", "10", "∞"]
def drawB(ax, standalone):
    grid(ax)
    ax.axvspan(3.6, 4.4, color="#eef3fb", zorder=0, lw=0)
    for v, c, mk, lab, mfc in [("sel_var", GRY, "D", "Selection per variable", "white"), ("comb_var", DUAL, "o", "Combination per variable", DUAL)]:
        rows = [r for r in D["f4b"] if r["variant"] == v]
        y = [r["worst"] for r in rows]
        ax.plot(range(9), y, color=c, lw=1.0, marker=mk, ms=4.2, mfc=mfc, mec=c, mew=0.8, label=lab, zorder=3)
    ax.axhline(1.02, color=INK2, lw=0.7, ls=(0, (3, 2)), zorder=2)
    ax.text(8.45, 1.032, "1.02", ha="right", va="bottom", fontsize=6.8, color=INK2)
    ax.text(4, 2.75, "frozen", ha="center", va="center", fontsize=7, color=DUAL)
    ax.set_yscale("log"); ax.set_ylim(0.98, 3.2)
    ax.yaxis.set_major_locator(FixedLocator([1, 1.1, 1.25, 1.5, 2, 3])); ax.yaxis.set_major_formatter(FuncFormatter(fmt))
    ax.yaxis.set_minor_formatter(NullFormatter()); ax.yaxis.set_minor_locator(FixedLocator([]))
    ax.set_xticks(range(9)); ax.set_xticklabels(kap); ax.set_xlim(-0.5, 8.5)
    ax.set_xlabel(r"Guard margin $\kappa$")
    ax.set_ylabel("Worst cell: RMSE / better normalization")
    ax.legend(loc="center", bbox_to_anchor=(0.5, 0.47), handlelength=1.8, labelspacing=0.3)
panels("fig_4", [drawA, drawB], pw=[9.0, 6.4], ph=6.6, margins=(1.25, 0.15, 1.0, 0.5))
