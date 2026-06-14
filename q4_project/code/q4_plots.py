# -*- coding: utf-8 -*-
"""
问题四 · 绘图（读取 q4_run.py 输出）
  fig1  权重单纯形上的"最优解归属"图(三角坐标)：每组权重落点上色=被选中的方案
  fig2  最优 (β,γ,N_r) 随权重的漂移：三个参数各一张，色=对应主导权重
用法: python q4_plots.py
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

d = np.load(os.path.join(OUT, "q4_arrays.npz"))
Xp, Fp, W, best_idx, robust_i = (d["Xp"], d["Fp"], d["W"],
                                 d["best_idx"], int(d["robust_i"]))

# 把权重单纯形投到二维三角坐标
def to_tri(W):
    # 顶点: R*=(0,0), dP*=(1,0), sigma*=(0.5, sqrt3/2)
    x = W[:, 1] + 0.5 * W[:, 2]
    y = (np.sqrt(3) / 2) * W[:, 2]
    return x, y

# ---- Fig 1: 单纯形最优解归属 ----
fig, ax = plt.subplots(figsize=(6.6, 6))
x, y = to_tri(W)
uniq = np.unique(best_idx)
cmap = plt.cm.tab20(np.linspace(0, 1, len(uniq)))
cmap_d = {u: cmap[k] for k, u in enumerate(uniq)}
cols = np.array([cmap_d[b] for b in best_idx])
ax.scatter(x, y, c=cols, s=18)
# 标出鲁棒解所占区域的中心 & 三个顶点标签
rx, ry = to_tri(W[best_idx == robust_i])
ax.scatter(rx.mean(), ry.mean(), s=260, marker="*", c="red",
           edgecolors="none", zorder=5,
           label=f"Robust (β={Xp[robust_i,0]:.2f},γ={Xp[robust_i,1]:.1f},Nr={int(Xp[robust_i,2])})")
for (vx, vy), t in zip([(0, 0), (1, 0), (0.5, np.sqrt(3)/2)],
                       ["w(R*)=1", "w(dP*)=1", "w(σ*)=1"]):
    ax.annotate(t, (vx, vy), ha="center",
                va="top" if vy == 0 else "bottom", fontsize=10,
                xytext=(0, -8 if vy == 0 else 8), textcoords="offset points")
ax.plot([0, 1, 0.5, 0], [0, 0, np.sqrt(3)/2, 0], "k-", lw=.6)
ax.legend(loc="upper right", fontsize=8); ax.axis("off"); ax.set_aspect("equal")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_weight_simplex.svg"),
                                bbox_inches="tight"); plt.close(fig)

# ---- Fig 2: 参数随"主导权重"漂移 ----
# 用每组权重里最大的那个分量代表偏好倾向，看选出的参数怎么变
dom = W.argmax(1)  # 0=R 1=dP 2=sigma 主导
labels = ["w(R*) dominant", "w(dP*) dominant", "w(σ*) dominant"]
P = Xp[best_idx]   # 每组权重选出的参数
fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
names = [r"$\beta$", r"$\gamma$", r"$N_r$"]
robust_x = Xp[robust_i]
robust_dom = sorted(set(dom[best_idx == robust_i].tolist()))
for k, ax in enumerate(axes):
    for dv, c in zip([0, 1, 2], ["#185FA5", "#A32D2D", "#0F6E56"]):
        vals = P[dom == dv, k]
        ax.scatter(np.full(vals.shape, dv) + np.random.uniform(-.15, .15, vals.shape),
                   vals, s=10, c=c, alpha=.4)
    ax.scatter(robust_dom, [robust_x[k]] * len(robust_dom),
               s=150, marker="*", c="red", edgecolors="none", zorder=5)
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["R", "dP", "σ"], fontsize=9)
    ax.set_xlabel("dominant weight"); ax.set_ylabel(names[k]); ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_param_drift.svg"),
                                bbox_inches="tight"); plt.close(fig)
print("[saved to figures/] fig1_weight_simplex.svg | fig2_param_drift.svg")
