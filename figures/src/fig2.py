from jstyle import *
from matplotlib.patches import FancyBboxPatch, Rectangle
setup()
W, H = 160, 86
fig = plt.figure(figsize=(W/10*CM, H/10*CM))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
steps = ["1", "2", "2b", "3", "4", "5", "6", "7"]
dates = ["11 Nov", "13 Nov", "14 Nov", "15 Nov", "16 Nov", "17 Nov", "17 Nov", "17 Nov"]
NS = len(steps)
dsets = ["Siemens", "ECG200", "Motors", "Hydraulic rig", "C-MAPSS", "MetroPT-3"]
x0, cw = 31, 16.0
xc = [x0 + cw*(i+0.5) for i in range(NS)]
yrow = [58.5 - 6.3*i for i in range(6)]
DEV, TEST, CONF, REUSE = "dev", "test", "conf", "reuse"
use = {0: {0: DEV, 1: DEV}, 1: {0: DEV, 1: DEV}, 2: {0: DEV, 1: DEV}, 3: {2: TEST, 3: TEST},
       4: {0: DEV, 1: DEV, 2: DEV, 3: DEV}, 5: {4: CONF, 5: CONF}, 6: {4: REUSE, 5: REUSE}, 7: {4: REUSE, 5: REUSE}}
sty = {DEV: dict(fc="#d9d9d9", ec="#d9d9d9", lw=0.6, hatch=None),
       TEST: dict(fc="white", ec=INK2, lw=1.0, hatch="////"),
       CONF: dict(fc="#5c5c5c", ec="#5c5c5c", lw=0.6, hatch=None),
       REUSE: dict(fc="white", ec="#5c5c5c", lw=1.2, hatch=None)}
plt.rcParams["hatch.linewidth"] = 0.5
plt.rcParams["hatch.color"] = "#9a9a9a"
# method bands
def band(i0, i1, text, ec, lw=0.8):
    xa, xb = x0 + cw*i0 + 1.0, x0 + cw*(i1+1) - 1.0
    ax.add_patch(FancyBboxPatch((xa, 77), xb - xa, 7.5, boxstyle="round,pad=0,rounding_size=1.4", fc="white", ec=ec, lw=lw))
    ax.text((xa+xb)/2, 80.75, text, ha="center", va="center", fontsize=7.4, weight="bold", color=INK)
band(0, 0, "Ablation", NEUT)
band(1, 3, "Reliability-weighted shrinkage", NEUT)
band(4, 7, "Dual normalization", DUAL, 1.2)
ax.text(2, 80.75, "Method tested", ha="left", va="center", fontsize=7.4, color=INK2)
# headers
for i in range(NS):
    ax.text(xc[i], 71.6, f"Step {steps[i]}", ha="center", va="center", fontsize=7.6, weight="bold", color=INK)
    ax.text(xc[i], 67.6, dates[i], ha="center", va="center", fontsize=6.8, color=MUTED)
ax.text(2, 69.6, "Plan written", ha="left", va="center", fontsize=7.4, color=INK2)
ax.plot([2, x0 + NS*cw], [63.8, 63.8], color=GRID, lw=0.6)
# rows
for j, d in enumerate(dsets):
    ax.text(2, yrow[j], d, ha="left", va="center", fontsize=7.6, color=INK)
    ax.plot([x0, x0 + NS*cw], [yrow[j], yrow[j]], color=GRID, lw=0.5, zorder=0)
for i in range(NS):
    for j, role in use[i].items():
        st = sty[role]
        ax.add_patch(FancyBboxPatch((xc[i] - cw/2 + 2.2, yrow[j] - 2.3), cw - 4.4, 4.6,
                                    boxstyle="round,pad=0,rounding_size=1.0", fc=st["fc"], ec=st["ec"], lw=st["lw"],
                                    hatch=st["hatch"], zorder=2))
# group brackets for dataset roles (Table 1 order)
ax.plot([2, x0 + NS*cw], [23.6, 23.6], color=GRID, lw=0.6)
outc = [("architecture", "not claimed"), ("not met", "10 of 38"), ("met", "35 of 38"), ("not met", "9 of 24"),
        ("method", "frozen"), ("H1–H3", "supported"), ("H4 not met,", "H5 supported"), ("R1–R3", "supported")]
for i, (a, b) in enumerate(outc):
    col = INK
    ax.text(xc[i], 19.6, a, ha="center", va="center", fontsize=7.0, color=col)
    ax.text(xc[i], 15.8, b, ha="center", va="center", fontsize=7.0, color=col)
ax.text(2, 17.7, "Outcome", ha="left", va="center", fontsize=7.4, color=INK2)
# legend (placed by measured text width)
items = [(DEV, "development data"), (TEST, "independent test, new data"), (CONF, "confirmation, new data"), (REUSE, "Step 5 test data reused")]
fig.canvas.draw(); rend = fig.canvas.get_renderer(); inv = ax.transData.inverted()
xx, ly = 2.0, 7.0
for role, lab in items:
    st = sty[role]
    ax.add_patch(FancyBboxPatch((xx, ly - 1.6), 6, 3.2, boxstyle="round,pad=0,rounding_size=0.8", fc=st["fc"], ec=st["ec"], lw=st["lw"], hatch=st["hatch"]))
    t = ax.text(xx + 7.6, ly, lab, ha="left", va="center", fontsize=6.8, color=INK2)
    bb = t.get_window_extent(rend); (x_a, _), (x_b, _) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
    xx = x_b + 4.5
assert xx < W + 2, xx
save(fig, "fig_2")
