# -*- coding: utf-8 -*-
"""
问题三 · 绘图（清晰版，读取 q3_run.py 的输出）
==================================================
为什么这么画：N_r 是离散档(2/4/6/8/10)，直接看三维散点容易出现分层。
故采用：
  fig1  三张两两投影，按 N_r 上色(每个排数档一条权衡曲线) + 膝点/理想点
  fig2  三维 Pareto 前沿，坐标轴=三目标，按 N_r 上色 + 红星/红三角标出两个关键点
用法: python q3_plots.py
"""
import os, warnings
import numpy as np
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  register 3D projection

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "..", "outputs")
FIG  = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"figure.dpi": 120, "font.size": 10})

d = np.load(os.path.join(OUT, "pareto_arrays.npz"))
Xp, Fp, ki, ip = d["Xp"], d["Fp"], int(d["knee_idx"]), int(d["ideal_idx"])
Nr = Xp[:, 2]
LAB = ["R*", "dP*", "Theta*"]
RED = "#C92A2A"
NR_COLORS = {2: "#85B7EB", 4: "#1D9E75", 6: "#BA7517", 8: "#D4537E", 10: "#534AB7"}

def mark_knee(ax, i, j):
    ax.scatter(Fp[ki, i], Fp[ki, j], s=240, c=RED, marker="*",
               edgecolor="k", lw=.7, zorder=6, label="Knee (chosen)")
    ax.scatter(Fp[ip, i], Fp[ip, j], s=100, c=RED, marker="^",
               edgecolor="k", lw=.6, zorder=6, label="Ideal-point ref.")

# ---- Fig 1: 三投影，按 N_r 上色 ----
pairs = [(0, 1), (0, 2), (1, 2)]
fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.8))
for ax, (i, j) in zip(axes, pairs):
    for nv in sorted(NR_COLORS):
        m = Nr == nv
        if m.any():
            ax.scatter(Fp[m, i], Fp[m, j], s=12, c=NR_COLORS[nv],
                       alpha=.65, label=f"N_r={int(nv)}")
    mark_knee(ax, i, j)
    ax.set_xlabel(LAB[i]); ax.set_ylabel(LAB[j]); ax.grid(alpha=.25)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=7, fontsize=8,
           bbox_to_anchor=(0.5, 1.08), frameon=False)
fig.suptitle("Pareto front projections — colored by pin-fin rows N_r", y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(os.path.join(FIG, "fig1_pareto_byNr.svg"), bbox_inches="tight"); plt.close(fig)

# ---- Fig 2: 三维 Pareto 前沿, 按 N_r 上色 ----
fig = plt.figure(figsize=(8.6, 6.0))
ax = fig.add_subplot(111, projection="3d")
for nv in sorted(NR_COLORS):
    m = Nr == nv
    if m.any():
        ax.scatter(Fp[m, 0], Fp[m, 1], Fp[m, 2],
                   s=18, c=NR_COLORS[nv], alpha=.58,
                   depthshade=False, edgecolor="none", label=f"N_r={int(nv)}")

ax.scatter(Fp[ki, 0], Fp[ki, 1], Fp[ki, 2],
           s=360, c=RED, marker="*", edgecolor="k", lw=.8,
           depthshade=False, label="Knee (chosen)", zorder=10)
ax.scatter(Fp[ip, 0], Fp[ip, 1], Fp[ip, 2],
           s=170, c=RED, marker="^", edgecolor="k", lw=.8,
           depthshade=False, label="Ideal-point ref.", zorder=10)

ax.set_xlabel("R*  (thermal resistance)", labelpad=8)
ax.set_ylabel("dP*  (pressure drop)", labelpad=8)
ax.set_zlabel("Theta*  (temperature non-uniformity)", labelpad=8)
ax.view_init(elev=28, azim=45)
ax.grid(alpha=.25)
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig2_tradeoff_R_dP.svg"), bbox_inches="tight")
plt.close(fig)

print("[saved to figures/] fig1_pareto_byNr.svg | fig2_tradeoff_R_dP.svg")
