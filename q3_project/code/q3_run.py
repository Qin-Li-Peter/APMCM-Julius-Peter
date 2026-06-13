# -*- coding: utf-8 -*-
"""
问题三 · 多目标优化：网格穷举求 Pareto 前沿 + 膝点法选综合最优
==================================================================
【为什么这么做 —— 设计依据】
1. 为什么用"网格穷举"而不是 NSGA-II 等启发式算法？
   决策变量只有 3 个、范围又小(β∈[0,0.3], γ∈[3,4.5], N_r∈{0,2,4,6,8,10})，
   且 GP 代理预测极快。启发式算法是为"穷举算不动的高维问题"准备的；本题
   穷举完全算得动，故直接在密网格上算出三指标再筛非支配解 —— 精确、可复现、
   不依赖随机种子、无"是否收敛"之忧。

2. 为什么 N_r 只取整数偶数档(0,2,4,6,8,10)？
   针肋排数是物理上的整数量，连续化插值得到的"3.7 排"不可制造。取附件 2
   的真实档位，结论可直接落地。

3. 为什么第三问自己重训 GP，而不读问题二存的 .pkl？
   pickle 的 sklearn 模型跨版本/跨机器易报错。自训练让本脚本完全自包含，
   且与问题二用同一核(Matern2.5 + 白噪声)、同一数据，结果一致。

4. 为什么膝点用"到极值解平面的最大距离"，而不是"理想-最差连线"？
   2 目标时两者一致；3 目标时，严谨的几何膝点是 Pareto 前沿上离"三个极值解
   (各自最小化一个指标的解)所张平面"最远、且偏向理想点一侧的解 —— 它就是
   "再多降一个指标就要付出不成比例代价"的转折点。

5. 为什么选膝点前必须 min-max 归一化？
   三指标范围悬殊(R*≈0.72–0.77 很窄, ΔP*≈0.077–0.20 较宽)。不归一化，范围
   大的压降会主导距离度量，使膝点失真。归一化到[0,1]后三者等地位。

6. 为什么膝点法适合第三问？
   它不需要人为指定权重 —— 给的是"几何上最均衡的客观折中点"。这正好与第四问
   "权重变化的影响"形成对照：第三问给不依赖权重的基准，第四问再扫权重看漂移。

用法: python q3_run.py [数据xlsx路径]
"""
import sys, os, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel as C

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data_attachment2.xlsx")
OUT  = os.path.join(HERE, "..", "outputs")
os.makedirs(OUT, exist_ok=True)

# 设计域(与附件2取值范围一致；优化只在域内插值，外推不可信)
BETA_RANGE  = (0.0, 0.30)
GAMMA_RANGE = (3.0, 4.5)
NR_LEVELS   = [0, 2, 4, 6, 8, 10]   # 整数偶数档
N_GRID      = 121                   # β、γ 各 121 档 → 121×121×6 ≈ 8.8 万点

TARGETS = ["R*", "dP*", "Theta*"]   # 三个都"越小越好"


def load_data(path):
    df = pd.read_excel(path, sheet_name="Sheet1", header=1)
    df.columns = ["id", "beta", "gamma", "Nr", "R", "dP", "Theta"]
    df = df.dropna(subset=["beta"]).reset_index(drop=True)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c])
    return df


def train_surrogates(df):
    """与问题二同核的高斯过程：Matern(nu=2.5)*常数 + 白噪声，标准化输入。"""
    X = df[["beta", "gamma", "Nr"]].values
    ys = {"R*": df["R"].values, "dP*": df["dP"].values, "Theta*": df["Theta"].values}
    models = {}
    for t, y in ys.items():
        kernel = (C(1.0, (1e-3, 1e3)) * Matern([1, 1, 1], (1e-2, 1e2), nu=2.5)
                  + WhiteKernel(1e-3, (1e-8, 1e-1)))
        gp = Pipeline([("sc", StandardScaler()),
                       ("gp", GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                                       n_restarts_optimizer=6, alpha=1e-10))])
        models[t] = gp.fit(X, y)
        print(f"  [GP] {t:<7} 训练R2 = "
              f"{1 - np.sum((y - gp.predict(X))**2)/np.sum((y - y.mean())**2):.4f}", flush=True)
    return models


def build_grid():
    b = np.linspace(*BETA_RANGE, N_GRID)
    g = np.linspace(*GAMMA_RANGE, N_GRID)
    n = np.array(NR_LEVELS, float)
    B, G, Nr = np.meshgrid(b, g, n, indexing="ij")
    return np.column_stack([B.ravel(), G.ravel(), Nr.ravel()])


def is_pareto(F):
    """高效非支配筛选(目标均为越小越好)。
    逐点扫描并不断剔除被支配者；Pareto 集通常很小，culling 很快。
    返回布尔掩码：True 表示该点是 Pareto 最优(非被支配)。"""
    n = F.shape[0]
    eff = np.ones(n, dtype=bool)
    order = np.argsort(F[:, 0], kind="mergesort")   # 按第一目标排序加速
    F = F[order]
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        if not keep[i]:
            continue
        # 任何"各目标都<=当前点 且 至少一个<当前点"的其它点都支配它
        dominated = np.all(F[keep] <= F[i], axis=1) & np.any(F[keep] < F[i], axis=1)
        if dominated.any():
            keep[i] = False
        else:
            # 当前点 i 支配掉后面那些被它支配的点
            dom_by_i = np.all(F[keep] >= F[i], axis=1) & np.any(F[keep] > F[i], axis=1)
            idx = np.where(keep)[0][dom_by_i]
            keep[idx] = False
    eff[order] = keep
    return eff


def knee_point(Fp):
    """膝点：到"极值解平面"最远、且偏理想侧的 Pareto 解。
    步骤：min-max 归一化 → 取三个极值解(各最小化一目标) → 拟合平面 →
    取离平面最远(理想侧)的解。返回索引及归一化矩阵。"""
    lo, hi = Fp.min(0), Fp.max(0)
    Fn = (Fp - lo) / np.where(hi - lo == 0, 1, hi - lo)     # 归一化到[0,1]
    a = np.array([Fn[np.argmin(Fn[:, k])] for k in range(3)])  # 三个极值解
    normal = np.cross(a[1] - a[0], a[2] - a[0])
    if np.linalg.norm(normal) < 1e-12:                       # 退化兜底：用理想点法
        return int(np.argmin(np.linalg.norm(Fn, axis=1))), Fn
    normal /= np.linalg.norm(normal)
    ideal = np.zeros(3)
    side = np.sign((ideal - a[0]) @ normal)                  # 朝理想点的一侧为正
    s = ((Fn - a[0]) @ normal) * side                        # 各解到平面的有向距离
    return int(np.argmax(s)), Fn


def run():
    print("=" * 64)
    print("问题三 · 网格穷举 Pareto 前沿 + 膝点法")
    print("=" * 64)
    df = load_data(DATA); print(f"样本数 n = {len(df)}；开始训练 GP 代理 ...", flush=True)
    models = train_surrogates(df)

    print("\n构建网格并用 GP 预测三指标 ...", flush=True)
    grid = build_grid()
    F = np.column_stack([models[t].predict(grid) for t in TARGETS])  # (M,3)
    print(f"  网格点数 = {len(grid):,}", flush=True)

    print("非支配排序求 Pareto 前沿 ...", flush=True)
    mask = is_pareto(F)
    Xp, Fp = grid[mask], F[mask]
    print(f"  Pareto 前沿解数 = {mask.sum():,}", flush=True)

    ki, Fn = knee_point(Fp)
    knee_x, knee_f = Xp[ki], Fp[ki]
    # 交叉验证：理想点法(归一化后离原点最近)
    ip = int(np.argmin(np.linalg.norm(Fn, axis=1)))
    ideal_x, ideal_f = Xp[ip], Fp[ip]

    # 各指标单独最优(锚点)作参考
    anchors = {t: Xp[np.argmin(Fp[:, j])] for j, t in enumerate(TARGETS)}

    print("\n" + "=" * 64)
    print("综合最优方案（膝点法）")
    print("=" * 64)
    print(f"  β = {knee_x[0]:.4f}   γ = {knee_x[1]:.4f}   N_r = {int(knee_x[2])}")
    print(f"  预测性能:  R* = {knee_f[0]:.4f}   ΔP* = {knee_f[1]:.4f}   σ_T* = {knee_f[2]:.4f}")
    print("\n交叉验证（理想点法）:")
    print(f"  β = {ideal_x[0]:.4f}   γ = {ideal_x[1]:.4f}   N_r = {int(ideal_x[2])}")
    print(f"  预测性能:  R* = {ideal_f[0]:.4f}   ΔP* = {ideal_f[1]:.4f}   σ_T* = {ideal_f[2]:.4f}")
    print("\n各指标单独最优（锚点，作参考）:")
    for t, x in anchors.items():
        print(f"  min {t:<6}: β={x[0]:.3f} γ={x[1]:.3f} N_r={int(x[2])}")

    # 保存
    pd.DataFrame(np.column_stack([Xp, Fp]),
                 columns=["beta", "gamma", "Nr", "R*", "dP*", "Theta*"]
                 ).to_csv(os.path.join(OUT, "pareto_front.csv"), index=False)
    json.dump({
        "knee":  {"beta": float(knee_x[0]), "gamma": float(knee_x[1]), "Nr": int(knee_x[2]),
                  "R*": float(knee_f[0]), "dP*": float(knee_f[1]), "Theta*": float(knee_f[2])},
        "ideal_point": {"beta": float(ideal_x[0]), "gamma": float(ideal_x[1]), "Nr": int(ideal_x[2]),
                        "R*": float(ideal_f[0]), "dP*": float(ideal_f[1]), "Theta*": float(ideal_f[2])},
        "anchors": {t: {"beta": float(x[0]), "gamma": float(x[1]), "Nr": int(x[2])}
                    for t, x in anchors.items()},
        "n_pareto": int(mask.sum()), "n_grid": int(len(grid)),
    }, open(os.path.join(OUT, "q3_result.json"), "w"), ensure_ascii=False, indent=2)
    np.savez(os.path.join(OUT, "pareto_arrays.npz"), Xp=Xp, Fp=Fp, knee_idx=ki, ideal_idx=ip)
    print(f"\n[已保存到 outputs/] pareto_front.csv | q3_result.json | pareto_arrays.npz")
    return Xp, Fp, ki, ip


if __name__ == "__main__":
    run()
