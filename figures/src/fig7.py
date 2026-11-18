from jstyle import *
import json, numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
setup()
D = json.load(open('figdata.json'))
order = ["Siemens", "ECG200", "Motor", "Hydraulic", "CMAPSS", "MetroPT"]
rng = np.random.default_rng(2)
def fmt(v, _): return f"{v:g}"
W, H = 12.0, 8.0
fig = plt.figure(figsize=(W*CM, H*CM))
l, r, b, t = 1.35, 0.2, 0.75, 1.15
ax = fig.add_axes([l/W, b/H, (W-l-r)/W, (H-b-t)/H])
grid(ax)
for i, ds in enumerate(order):
    y = np.array([q["r"] for q in D["f7"] if q["ds"] == ds])
    x = i + rng.uniform(-0.22, 0.22, len(y))
    lo = y < 1
    ax.scatter(x[lo], y[lo], s=16, marker="^", facecolor=SEQ, edgecolor="white", linewidth=0.4, zorder=3)
    ax.scatter(x[~lo], y[~lo], s=16, marker="s", facecolor=GLOB, edgecolor="white", linewidth=0.4, zorder=3)
    ax.text(i, 1.03, f"{int(lo.sum())}/{len(y)}", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=7.4, color=INK, clip_on=False)
ax.axhline(1, color=INK2, lw=0.8, zorder=2)
ax.axvline(3.5, color=GRID, lw=0.8, zorder=1)
ax.set_yscale("log"); ax.set_ylim(0.02, 5)
ax.yaxis.set_major_locator(FixedLocator([0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 4])); ax.yaxis.set_major_formatter(FuncFormatter(fmt))
ax.yaxis.set_minor_formatter(NullFormatter())
ax.set_xticks(range(6)); ax.set_xticklabels([DSN[d] for d in order]); ax.set_xlim(-0.6, 5.6)
ax.tick_params(axis="x", length=0)
ax.set_ylabel("RMSE per-sequence / RMSE global")
ax.text(5.55, 3.2, "global better", ha="right", va="center", fontsize=7.2, color=INK2)
ax.text(5.55, 0.62, "per-sequence better", ha="right", va="center", fontsize=7.2, color=INK2)
ax.text(1.5, 1.10, "development data (Step 4)", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=7.2, color=MUTED)
ax.text(4.5, 1.10, "confirmation data (Step 5)", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=7.2, color=MUTED)
save(fig, "fig_7")
