from jstyle import *
import json, numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, NullFormatter, FuncFormatter, NullLocator
setup()
D = json.load(open('figdata.json'))
def fmt(v, _): return f"{v:g}"
GRY = "#7a7a7a"
groups = [("CMAPSS", "SAITS"), ("CMAPSS", "Transformer"), ("MetroPT", "SAITS"), ("MetroPT", "Transformer")]
KEYS = [("ens_global", GLOB, "s", "Two-seed ensemble, global"), ("ens_seq", SEQ, "^", "Two-seed ensemble, per-sequence"), ("dual", DUAL, "o", "Dual normalization")]
def handles(ms=4.6):
    return [Line2D([], [], ls="", marker=mk, ms=ms, mfc=c, mec="white", mew=0.4, label=l) for k, c, mk, l in KEYS]
def drawA(ax, standalone):
    ys, heads = {}, {}; y = 0
    for g in groups:
        heads[g] = y; y -= 1
        for c in CONDS:
            ys[g + (c,)] = y; y -= 1
        y -= 0.35
    for r in D["f6a"]:
        yy = ys[(r["ds"], r["model"], r["cond"])]
        vals = [r[k] for k, *_ in KEYS]
        ax.plot([min(vals), max(vals)], [yy, yy], color="#cfcfcf", lw=1.2, zorder=2, solid_capstyle="round")
        for k, c, mk, _ in KEYS:
            ax.scatter(r[k], yy, s=20, marker=mk, facecolor=c, edgecolor="white", linewidth=0.4, zorder=4 if k == "dual" else 3)
    ax.axvline(1, color=INK2, lw=0.7, ls=(0, (3, 2)), zorder=1)
    ax.axvline(1.02, color=INK2, lw=0.5, ls=(0, (1, 1.5)), zorder=1)
    ax.set_xscale("log"); ax.set_xlim(0.92, 2.1)
    ax.xaxis.set_major_locator(FixedLocator([1, 1.1, 1.25, 1.5, 2])); ax.xaxis.set_major_formatter(FuncFormatter(fmt))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_yticks(list(ys.values())); ax.set_yticklabels([COND[k[2]] for k in ys])
    ax.tick_params(axis="y", length=0, pad=2)
    for g, yh in heads.items():
        ax.text(0.015, yh, f"{DSN[g[0]]}, {g[1]}", transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=7.4, weight="bold", color=INK, bbox=dict(fc="white", ec="none", pad=0.8), zorder=6)
    ax.set_ylim(y + 0.6, 0.7)
    ax.grid(True, axis="x", color=GRID, lw=0.5, zorder=0); ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("RMSE / better two-seed ensemble")
    if standalone:
        ax.legend(handles=handles(), loc="lower left", bbox_to_anchor=(-0.22, 1.0), ncol=2, columnspacing=0.8, handletextpad=0.1, labelspacing=0.3, fontsize=6.8)
VAR = [("dual", "Dual\nnormalization", DUAL, True), ("abl_no_guard", "Without\nguard", GRY, False), ("abl_pooled", "Pooled\nweight", GRY, False),
       ("abl_select", "Selection", GRY, False), ("abl_equal", "Equal\nweights", GRY, False)]
rng = np.random.default_rng(5)
def drawB(ax, standalone):
    ax.grid(True, axis="y", color=GRID, lw=0.5, zorder=0); ax.set_axisbelow(True)
    for i, (k, lab, c, filled) in enumerate(VAR):
        y = np.array([r["r"] for r in D["f6b"][k]])
        x = i + rng.uniform(-0.18, 0.18, len(y))
        if filled: ax.scatter(x, y, s=12, marker="o", facecolor=c, edgecolor="white", linewidth=0.3, zorder=3)
        else: ax.scatter(x, y, s=12, marker="o", facecolor="white", edgecolor=c, linewidth=0.7, zorder=3)
        gm = float(np.exp(np.log(y).mean()))
        ax.plot([i - 0.28, i + 0.28], [gm, gm], color=INK, lw=1.2, zorder=4)
        ax.text(i, 1.035, f"{gm:.3f}", transform=ax.get_xaxis_transform(), clip_on=False, ha="center", va="bottom", fontsize=7.2,
                color=INK, weight="bold" if k == "dual" else "normal")
    ax.axhline(1, color=INK2, lw=0.7, ls=(0, (3, 2)), zorder=2)
    ax.set_yscale("log"); ax.set_ylim(0.87, 1.36)
    ax.yaxis.set_major_locator(FixedLocator([0.9, 1, 1.1, 1.2, 1.3])); ax.yaxis.set_major_formatter(FuncFormatter(fmt))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_xticks(range(len(VAR))); ax.set_xticklabels([v[1] for v in VAR], fontsize=6.9)
    ax.set_xlim(-0.5, len(VAR) - 0.5); ax.tick_params(axis="x", length=0)
    ax.set_ylabel("RMSE / better single normalization")
def leg(fig, W, H):
    fig.legend(handles=handles(), loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=3, columnspacing=1.2, handletextpad=0.2)
panels("fig_6", [drawA, drawB], pw=[8.6, 7.0], ph=8.4, margins=[(1.6, 0.2, 0.95, 0.75), (1.3, 0.1, 0.95, 0.75)], legend=leg, legend_h=0.45, solo_top=[0.55, 0])
