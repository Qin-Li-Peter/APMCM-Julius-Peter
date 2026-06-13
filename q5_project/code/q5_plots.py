# -*- coding: utf-8 -*-
"""问题五 · 绘图。fig1 局部灵敏度热图 / fig2 蒙特卡洛分布 / fig3 Sobol(β,γ)堆叠条"""
import os, warnings
import numpy as np
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs"); FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"figure.dpi": 120, "font.size": 10})
d = np.load(os.path.join(OUT, "q5_arrays.npz"))
Fs, base, loc, sobST = d["Fs"], d["base"], d["loc"], d["sobST"]
TGT = ["R*", "dP*", "Theta*"]; PN = ["beta", "gamma", "Nr"]; CONT = ["beta", "gamma"]

fig, ax = plt.subplots(figsize=(5.6, 4))
im = ax.imshow(np.abs(loc), cmap="OrRd", aspect="auto")
ax.set_xticks(range(3)); ax.set_xticklabels(TGT); ax.set_yticks(range(3)); ax.set_yticklabels(PN)
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"{loc[i, j]:+.2f}", ha="center", va="center", fontsize=10)
fig.colorbar(im, ax=ax, label="|normalized sensitivity|")
ax.set_title("Local sensitivity  S=(dY/dx)(x/Y)")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_sensitivity_heatmap.svg")); plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(11, 3.4)); cols = ["#185FA5", "#A32D2D", "#0F6E56"]
for j, (ax, t) in enumerate(zip(axes, TGT)):
    ax.hist(Fs[:, j], bins=50, color=cols[j], alpha=.8)
    ax.axvline(base[j], color="k", ls="--", lw=1.2, label="baseline")
    ax.set_xlabel(t); ax.set_ylabel("count"); ax.legend(fontsize=8); ax.grid(alpha=.2)
fig.suptitle("Monte-Carlo distribution under machining tolerance (beta,gamma +-5%)", y=1.02)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_montecarlo.svg"), bbox_inches="tight"); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 4))
norm = sobST / sobST.sum(1, keepdims=True); bottom = np.zeros(3); colors = ["#534AB7", "#1D9E75"]
for k in range(2):
    ax.bar(TGT, norm[:, k], bottom=bottom, color=colors[k], label=CONT[k]); bottom += norm[:, k]
ax.set_ylabel("Sobol total-effect share (beta,gamma)"); ax.set_ylim(0, 1)
ax.set_title("Which continuous parameter drives each metric's variation")
ax.legend(title="parameter", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig3_sobol.svg")); plt.close(fig)
print("[saved to figures/] fig1_sensitivity_heatmap.svg | fig2_montecarlo.svg | fig3_sobol.svg")
