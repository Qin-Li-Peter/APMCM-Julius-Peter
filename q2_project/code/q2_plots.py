# -*- coding: utf-8 -*-
"""
问题二 · 绘图脚本（读取 q2_run.py 的输出）
生成: fig1_model_comparison.svg / fig2_gp_pred_vs_actual.svg / fig3_main_effects.svg
用法: python q2_plots.py   （需先运行 q2_run.py）
"""
import os, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "..", "outputs")
FIG  = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({"figure.dpi": 120, "font.size": 10, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.axisbelow": True})
COL = {"PhysElasticNet": "#534AB7", "GP_Kriging": "#0F6E56",
       "QuadRSM": "#BA7517", "RandomForest": "#888780"}
MLAB = {"PhysElasticNet": "Phys ElasticNet", "GP_Kriging": "GP (Kriging)",
        "QuadRSM": "Quad RSM", "RandomForest": "Random Forest"}
MODELS = ["PhysElasticNet", "GP_Kriging", "QuadRSM", "RandomForest"]

res = json.load(open(os.path.join(OUT, "results.json")))["results"]
npz = np.load(os.path.join(OUT, "loo_predictions.npz"))
df  = pd.read_csv(os.path.join(OUT, "data_clean.csv"))
TN  = ["R*", "dP*", "Theta*"]

# ---- Fig 1: LOO Q2 对照柱状图 ----
fig, ax = plt.subplots(figsize=(7.2, 3.8))
x = np.arange(len(TN)); w = 0.2
for i, m in enumerate(MODELS):
    ax.bar(x + (i - 1.5) * w, [res[t][m]["Q2_LOO"] for t in TN], w,
           label=MLAB[m], color=COL[m])
ax.set_xticks(x); ax.set_xticklabels(TN); ax.set_ylim(0.4, 1.02)
ax.set_ylabel("LOO  $Q^2$"); ax.set_title("Four-model comparison (leave-one-out)")
ax.axhline(0.9, ls="--", c="#A32D2D", lw=.8)
ax.legend(ncol=2, fontsize=8, loc="lower center")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_model_comparison.svg")); plt.close(fig)

# ---- Fig 2: GP 预测-真实散点 (3 panel) ----
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6))
for ax, t in zip(axes, TN):
    y = npz[f"{t}__actual"]; yh = npz[f"{t}__GP_Kriging"]
    lo, hi = min(y.min(), yh.min()), max(y.max(), yh.max()); pad = (hi - lo) * .05
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], "--", c="#888780", lw=1)
    ax.scatter(y, yh, s=22, c="#0F6E56", alpha=.75, edgecolor="white", lw=.4)
    ax.set_xlabel(f"actual {t}"); ax.set_ylabel(f"predicted {t}")
    ax.set_title(f"GP   $Q^2$={res[t]['GP_Kriging']['Q2_LOO']:.4f}")
fig.suptitle("GP (Kriging) leave-one-out: predicted vs actual", y=1.02)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_gp_pred_vs_actual.svg"),
                                bbox_inches="tight"); plt.close(fig)

# ---- Fig 3: 主效应折线 (3 指标 × 3 变量) ----
fig, axes = plt.subplots(3, 3, figsize=(10.5, 8.5))
varcols = ["beta", "gamma", "Nr"]; vlab = [r"$\beta$", r"$\gamma$", r"$N_r$"]
tcol = {"R*": "R", "dP*": "dP", "Theta*": "Theta"}
tc = {"R*": "#185FA5", "dP*": "#A32D2D", "Theta*": "#0F6E56"}
for i, t in enumerate(TN):
    for j, v in enumerate(varcols):
        ax = axes[i, j]; g = df.groupby(v)[tcol[t]].mean()
        ax.plot(g.index, g.values, "-o", c=tc[t], ms=5)
        ax.set_xlabel(vlab[j])
        if j == 0: ax.set_ylabel(f"mean {t}")
fig.suptitle("Main effects (group means) — corroborates Q1 mechanism", y=1.0)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig3_main_effects.svg"),
                                bbox_inches="tight"); plt.close(fig)

print("[已保存到 figures/] fig1_model_comparison.svg | "
      "fig2_gp_pred_vs_actual.svg | fig3_main_effects.svg")
