# -*- coding: utf-8 -*-
"""
问题三 · 绘图（清晰版，读取 q3_run.py 的输出）
==================================================
为什么这么画：N_r 是离散档(2/4/6/8/10)，三维散点会碎成"悬空面条"难以解读。
故改为：
  fig1  三张两两投影，按 N_r 上色(每个排数档一条权衡曲线) + 膝点/理想点
  fig2  头牌图：R*–ΔP* 主权衡，颜色=第三指标 Θ*(色条) + 膝点/理想点
用法: python q3_plots.py
"""
import os, warnings
import numpy as np
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "..", "outputs")
FIG  = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"figure.dpi": 120, "font.size": 10})

d = np.load(os.path.join(OUT, "pareto_arrays.npz"))
Xp, Fp, ki, ip = d["Xp"], d["Fp"], int(d["knee_idx"]), int(d["ideal_idx"])
Nr = Xp[:, 2]
LAB = ["R*", "dP*", "Theta*"]
RED, AMBER = "#A32D2D", "#BA7517"
NR_COLORS = {2: "#85B7EB", 4: "#1D9E75", 6: "#BA7517", 8: "#D4537E", 10: "#534AB7"}

def mark_knee(ax, i, j):
    ax.scatter(Fp[ki, i], Fp[ki, j], s=240, c=RED, marker="*",
               edgecolor="k", lw=.7, zorder=6, label="Knee (chosen)")
    ax.scatter(Fp[ip, i], Fp[ip, j], s=80, c=AMBER, marker="D",
               edgecolor="k", lw=.5, zorder=6, label="Ideal-point")

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

# ---- Fig 2: 头牌 R*–dP* 权衡, 颜色=Theta* ----
fig, ax = plt.subplots(figsize=(7.2, 5))
sc = ax.scatter(Fp[:, 0], Fp[:, 1], c=Fp[:, 2], s=26, cmap="viridis_r",
                alpha=.85, edgecolor="none")
cb = fig.colorbar(sc, ax=ax); cb.set_label("Theta*  (temperature non-uniformity)")
mark_knee(ax, 0, 1)
ax.set_xlabel("R*  (thermal resistance)")
ax.set_ylabel("dP*  (pressure drop)")
ax.set_title("Pareto front: R* vs dP* trade-off (color = Theta*)")
ax.legend(loc="upper right", fontsize=9); ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_tradeoff_R_dP.svg")); plt.close(fig)

print("[saved to figures/] fig1_pareto_byNr.svg | fig2_tradeoff_R_dP.svg")
