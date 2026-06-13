# -*- coding: utf-8 -*-
"""
问题三 · 绘图（读取 q3_run.py 的输出 pareto_arrays.npz）
生成: fig1_pareto_3d.svg（三维前沿+膝点） / fig2_pareto_projections.svg（三张两两投影）
用法: python q3_plots.py   （需先运行 q3_run.py）
"""
import os, warnings
import numpy as np
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "..", "outputs")
FIG  = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"figure.dpi": 120, "font.size": 10})

d = np.load(os.path.join(OUT, "pareto_arrays.npz"))
Fp, ki, ip = d["Fp"], int(d["knee_idx"]), int(d["ideal_idx"])
LAB = ["R*", "dP*", "Theta*"]
TEAL, RED, AMBER = "#1D9E75", "#A32D2D", "#BA7517"

# ---- Fig 1: 三维 Pareto 前沿 + 膝点 ----
fig = plt.figure(figsize=(7.2, 6))
ax = fig.add_subplot(111, projection="3d")
ax.scatter(Fp[:, 0], Fp[:, 1], Fp[:, 2], s=8, c=TEAL, alpha=0.35, label="Pareto front")
ax.scatter(*Fp[ki], s=130, c=RED, marker="*", edgecolor="k", lw=.6, label="Knee (chosen)")
ax.scatter(*Fp[ip], s=70, c=AMBER, marker="D", edgecolor="k", lw=.5, label="Ideal-point")
ax.set_xlabel(LAB[0]); ax.set_ylabel(LAB[1]); ax.set_zlabel(LAB[2])
ax.set_title("Pareto front (grid search) with knee point")
ax.legend(loc="upper left", fontsize=8); ax.view_init(elev=22, azim=-58)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_pareto_3d.svg")); plt.close(fig)

# ---- Fig 2: 两两投影 ----
pairs = [(0, 1), (0, 2), (1, 2)]
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
for ax, (i, j) in zip(axes, pairs):
    ax.scatter(Fp[:, i], Fp[:, j], s=10, c=TEAL, alpha=0.4)
    ax.scatter(Fp[ki, i], Fp[ki, j], s=160, c=RED, marker="*",
               edgecolor="k", lw=.6, label="Knee", zorder=5)
    ax.scatter(Fp[ip, i], Fp[ip, j], s=70, c=AMBER, marker="D",
               edgecolor="k", lw=.5, label="Ideal-point", zorder=5)
    ax.set_xlabel(LAB[i]); ax.set_ylabel(LAB[j]); ax.grid(alpha=.25)
axes[0].legend(fontsize=8)
fig.suptitle("Pareto front projections", y=1.02)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_pareto_projections.svg"),
                                bbox_inches="tight"); plt.close(fig)
print("[已保存到 figures/] fig1_pareto_3d.svg | fig2_pareto_projections.svg")
