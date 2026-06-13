# -*- coding: utf-8 -*-
"""
问题四 · 指标权重变化的影响 + 鲁棒设计
==================================================================
【做什么】第四问扰动的是"偏好(权重 w)"，不是参数。
  1) 在权重单纯形(w_R+w_dP+w_sigma=1, 均≥0)上密集采样；
  2) 每组权重下，用"归一化加权和"在 Pareto 前沿上选最优方案；
  3) 看最优 (β,γ,N_r) 随权重如何漂移；
  4) 给出"对偏好变化最不敏感"的鲁棒设计——判据见下。

【鲁棒判据】对每个曾被选为最优的候选解，统计它在整个权重单纯形上"被选为最优
  的权重面积占比(win-share)"。占比最大的解 = 在最宽的偏好范围内都最优 =
  对偏好变化最不敏感的鲁棒解。同时报告各典型场景(重R/重dP/重σ)的最优解作对照。

【为什么这样】膝点(问题三)是单点客观折中；第四问把偏好放开，检验最优解的稳健性。
  归一化用 min-max 把三指标拉到[0,1]同地位，否则范围大的 dP* 会主导加权和。

用法: python q4_run.py [数据xlsx]
"""
import sys, os, json, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from surrogate import (load_data, train_surrogates, predict_all,
                       build_grid, is_pareto, TARGETS)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data_attachment2.xlsx")
OUT  = os.path.join(HERE, "..", "outputs")
os.makedirs(OUT, exist_ok=True)


def simplex_weights(step=0.02):
    """生成权重单纯形上的网格点 (w1+w2+w3=1, 均≥0)。step=0.02 → 约1326组。"""
    ks = int(round(1 / step))
    W = []
    for a in range(ks + 1):
        for b in range(ks + 1 - a):
            c = ks - a - b
            W.append([a / ks, b / ks, c / ks])
    return np.array(W)


def run():
    print("=" * 64); print("问题四 · 权重敏感性 + 鲁棒设计"); print("=" * 64)
    df = load_data(DATA); print(f"样本数 n = {len(df)}；训练 GP ...", flush=True)
    models = train_surrogates(df)

    # Pareto 前沿（候选方案集）
    grid = build_grid(121)
    F = predict_all(models, grid)
    mask = is_pareto(F)
    Xp, Fp = grid[mask], F[mask]
    print(f"Pareto 前沿候选解数 = {len(Xp):,}", flush=True)

    # 归一化（min-max 到 [0,1]）
    lo, hi = Fp.min(0), Fp.max(0)
    Fn = (Fp - lo) / np.where(hi - lo == 0, 1, hi - lo)

    # 权重扫描：每组权重选加权和最小的 Pareto 解
    W = simplex_weights(0.02)
    scores = Fn @ W.T                      # (n_pareto, n_weight)
    best_idx = scores.argmin(0)            # 每组权重的最优解索引
    print(f"权重组合数 = {len(W):,}", flush=True)

    # 鲁棒判据：win-share（被选为最优的权重占比）
    uniq, counts = np.unique(best_idx, return_counts=True)
    win = dict(zip(uniq, counts / len(W)))
    robust_i = max(win, key=win.get)
    rob_x, rob_f = Xp[robust_i], Fp[robust_i]

    # 典型场景（重某一指标）的最优解
    scenarios = {
        "均衡 (1/3,1/3,1/3)": [1/3, 1/3, 1/3],
        "重热阻 R (0.6,0.2,0.2)": [0.6, 0.2, 0.2],
        "重压降 dP (0.2,0.6,0.2)": [0.2, 0.6, 0.2],
        "重均匀 sigma (0.2,0.2,0.6)": [0.2, 0.2, 0.6],
    }
    scen_out = {}
    for name, w in scenarios.items():
        i = (Fn @ np.array(w)).argmin()
        scen_out[name] = {"beta": float(Xp[i, 0]), "gamma": float(Xp[i, 1]),
                          "Nr": int(Xp[i, 2]), "R*": float(Fp[i, 0]),
                          "dP*": float(Fp[i, 1]), "Theta*": float(Fp[i, 2])}

    # 输出
    print("\n" + "=" * 64); print("鲁棒设计（对偏好变化最不敏感）"); print("=" * 64)
    print(f"  β = {rob_x[0]:.4f}  γ = {rob_x[1]:.4f}  N_r = {int(rob_x[2])}")
    print(f"  性能: R*={rob_f[0]:.4f}  ΔP*={rob_f[1]:.4f}  σ_T*={rob_f[2]:.4f}")
    print(f"  win-share = {win[robust_i]*100:.1f}%  (在 {win[robust_i]*100:.1f}% 的权重组合下都是最优)")
    print("\n各典型场景最优方案:")
    for name, s in scen_out.items():
        print(f"  {name:<26} β={s['beta']:.3f} γ={s['gamma']:.3f} N_r={s['Nr']}"
              f"  (R*={s['R*']:.4f} ΔP*={s['dP*']:.4f} σ*={s['Theta*']:.4f})")

    # 前 5 名 win-share
    top = sorted(win.items(), key=lambda kv: -kv[1])[:5]
    print("\nwin-share 前 5 名候选解:")
    for i, sh in top:
        print(f"  β={Xp[i,0]:.3f} γ={Xp[i,1]:.3f} N_r={int(Xp[i,2])}  win={sh*100:.1f}%")

    # 保存（含每组权重的最优解，供绘漂移轨迹/单纯形热图）
    np.savez(os.path.join(OUT, "q4_arrays.npz"),
             Xp=Xp, Fp=Fp, W=W, best_idx=best_idx, robust_i=robust_i)
    json.dump({
        "robust_design": {"beta": float(rob_x[0]), "gamma": float(rob_x[1]),
                          "Nr": int(rob_x[2]), "R*": float(rob_f[0]),
                          "dP*": float(rob_f[1]), "Theta*": float(rob_f[2]),
                          "win_share": float(win[robust_i])},
        "scenarios": scen_out,
        "top5_winshare": [{"beta": float(Xp[i, 0]), "gamma": float(Xp[i, 1]),
                           "Nr": int(Xp[i, 2]), "win_share": float(sh)} for i, sh in top],
        "n_weights": int(len(W)), "n_pareto": int(len(Xp)),
    }, open(os.path.join(OUT, "q4_result.json"), "w"), ensure_ascii=False, indent=2)
    print(f"\n[已保存] outputs/q4_result.json | q4_arrays.npz")


if __name__ == "__main__":
    run()
