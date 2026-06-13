# -*- coding: utf-8 -*-
"""
问题五 · 参数扰动的敏感性与稳定性
==================================================================
【做什么】第五问扰动"结构参数"(加工误差/工况波动)，针对确定方案看三指标抖多少。

【关键物理判断 —— 为什么连续扰动只作用于 β、γ，N_r 单独离散处理】
  加工误差作用在"连续几何量"上：针肋直径→β、各层高度→γ。而 N_r 是单个歧管单元内
  的针肋排数，是制造时定死的整数(你只会做 4 排或 6 排，不会做出 3.7 排)。因此：
   - 蒙特卡洛 & Sobol：只对 β、γ 施加连续加工公差，N_r 固定；
   - N_r 另做"少一排/多一排"的离散稳健性检查，单独报告。
  这样局部灵敏度、蒙特卡洛、Sobol 三者口径一致(都针对连续公差)，结论不再自相矛盾。

【三件分析】
  1) 局部灵敏度 S=(∂Y/∂x)(x/Y)：在最优点对各参数的归一化斜率(N_r 用离散差分，仅参考)；
  2) 蒙特卡洛：β,γ 各 ±5%(1σ) 高斯扰动，得三指标分布(均值/标准差/CV/95分位/最坏)；
  3) Sobol(β,γ)：方差分解，定量给出 β、γ 对各指标波动的贡献占比；
  4) N_r 离散检查：N_r±2 对三指标的影响。

用法: python q5_run.py [数据xlsx] [beta gamma Nr]
"""
import sys, os, json, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from surrogate import load_data, train_surrogates, predict_all, TARGETS

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data_attachment2.xlsx")
OUT  = os.path.join(HERE, "..", "outputs"); os.makedirs(OUT, exist_ok=True)

X0 = np.array([0.22, 4.5, 4.0])              # 默认评估问题三/四的鲁棒解
if len(sys.argv) >= 5:
    X0 = np.array([float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])])

PN = ["beta", "gamma", "Nr"]
REL_SIGMA = {"beta": 0.05, "gamma": 0.05}    # 连续加工公差 1σ = ±5%
N_MC = 20000
CONT = ["beta", "gamma"]                      # 仅这两个施加连续扰动


def local_sensitivity(models, x0):
    base = predict_all(models, x0[None, :])[0]
    out = {}
    for k, name in enumerate(PN):
        h = 2.0 if name == "Nr" else max(abs(x0[k]) * 1e-3, 1e-4)  # N_r 用±2离散差分
        xp, xm = x0.copy(), x0.copy(); xp[k] += h; xm[k] -= h
        xp[2] = np.clip(xp[2], 0, 10); xm[2] = np.clip(xm[2], 0, 10)
        dY = (predict_all(models, xp[None, :])[0] - predict_all(models, xm[None, :])[0]) / (2 * h)
        out[name] = {TARGETS[j]: {"dYdx": float(dY[j]),
                     "S_norm": float(dY[j] * x0[k] / base[j]) if base[j] else 0.0}
                     for j in range(3)}
    return base, out


def monte_carlo(models, x0):
    rng = np.random.default_rng(0)
    b = np.clip(x0[0] * (1 + rng.normal(0, REL_SIGMA["beta"], N_MC)), 0, 0.30)
    g = np.clip(x0[1] * (1 + rng.normal(0, REL_SIGMA["gamma"], N_MC)), 3.0, 4.5)
    nr = np.full(N_MC, x0[2])                 # N_r 固定
    Fs = predict_all(models, np.column_stack([b, g, nr]))
    stats = {t: {"mean": float(Fs[:, j].mean()), "std": float(Fs[:, j].std()),
                 "cv_%": float(100 * Fs[:, j].std() / Fs[:, j].mean()),
                 "p95": float(np.percentile(Fs[:, j], 95)),
                 "worst(max)": float(Fs[:, j].max()),
                 "range": float(np.ptp(Fs[:, j]))} for j, t in enumerate(TARGETS)}
    return Fs, stats


def sobol_bg(models, x0):
    """仅 β、γ 的一阶/总效应 Sobol(范围 = ±2σ 均匀域，与MC量级匹配)。"""
    rng = np.random.default_rng(1); n = 8192
    lo = np.array([x0[0]*(1-2*REL_SIGMA["beta"]), x0[1]*(1-2*REL_SIGMA["gamma"])])
    hi = np.array([x0[0]*(1+2*REL_SIGMA["beta"]), x0[1]*(1+2*REL_SIGMA["gamma"])])
    lo = np.clip(lo, [0, 3], [0.3, 4.5]); hi = np.clip(hi, [0, 3], [0.3, 4.5])
    def expand(P2): return np.column_stack([P2[:, 0], P2[:, 1], np.full(len(P2), x0[2])])
    A = lo + (hi - lo) * rng.random((n, 2)); B = lo + (hi - lo) * rng.random((n, 2))
    fA, fB = predict_all(models, expand(A)), predict_all(models, expand(B))
    res = {t: {} for t in TARGETS}
    for k, name in enumerate(CONT):
        AB = A.copy(); AB[:, k] = B[:, k]; fAB = predict_all(models, expand(AB))
        for j, t in enumerate(TARGETS):
            varY = np.var(np.r_[fA[:, j], fB[:, j]]) + 1e-15
            S1 = np.mean(fB[:, j] * (fAB[:, j] - fA[:, j])) / varY
            ST = 0.5 * np.mean((fA[:, j] - fAB[:, j]) ** 2) / varY
            res[t][name] = {"S1": float(max(S1, 0)), "ST": float(max(ST, 0))}
    return res


def nr_discrete(models, x0):
    out = {}
    base = predict_all(models, x0[None, :])[0]
    for dn in (-2, 2):
        nv = np.clip(x0[2] + dn, 0, 10)
        f = predict_all(models, np.array([[x0[0], x0[1], nv]]))[0]
        out[f"N_r{int(nv)}"] = {TARGETS[j]: {"value": float(f[j]),
                                "delta_%": float(100 * (f[j] - base[j]) / base[j])}
                                for j in range(3)}
    return out


def run():
    print("=" * 64); print("问题五 · 参数扰动敏感性与稳定性"); print("=" * 64)
    df = load_data(DATA); print(f"样本数 n = {len(df)}；训练 GP ...", flush=True)
    models = train_surrogates(df)
    print(f"\n评估方案: β={X0[0]:.3f}  γ={X0[1]:.3f}  N_r={int(X0[2])}", flush=True)

    base, loc = local_sensitivity(models, X0)
    print(f"基准性能: R*={base[0]:.4f}  ΔP*={base[1]:.4f}  σ_T*={base[2]:.4f}")
    print("\n[局部] 归一化灵敏度 S=(∂Y/∂x)(x/Y)  (N_r 为±2离散差分, 仅参考):")
    print(f'{"参数":<8}{"对R*":>12}{"对dP*":>12}{"对σ_T*":>12}')
    for name in PN:
        print(f'{name:<8}{loc[name]["R*"]["S_norm"]:>12.3f}'
              f'{loc[name]["dP*"]["S_norm"]:>12.3f}{loc[name]["Theta*"]["S_norm"]:>12.3f}')

    _, mc = monte_carlo(models, X0)
    print(f"\n[蒙特卡洛] β,γ各±5%(1σ)高斯, N_r固定, N={N_MC}:")
    print(f'{"指标":<8}{"均值":>10}{"标准差":>10}{"CV%":>8}{"95分位":>10}{"最坏":>10}')
    for t in TARGETS:
        s = mc[t]
        print(f'{t:<8}{s["mean"]:>10.4f}{s["std"]:>10.4f}{s["cv_%"]:>8.2f}'
              f'{s["p95"]:>10.4f}{s["worst(max)"]:>10.4f}')

    sob = sobol_bg(models, X0)
    print("\n[Sobol(β,γ)] 总效应 ST (各连续参数对指标波动的贡献占比):")
    print(f'{"指标":<8}{"beta":>10}{"gamma":>10}')
    for t in TARGETS:
        print(f'{t:<8}{sob[t]["beta"]["ST"]:>10.3f}{sob[t]["gamma"]["ST"]:>10.3f}')

    nrd = nr_discrete(models, X0)
    print("\n[N_r 离散检查] 少/多 2 排相对基准的变化:")
    for k, v in nrd.items():
        print(f'  {k}: R*{v["R*"]["delta_%"]:+.2f}%  ΔP*{v["dP*"]["delta_%"]:+.2f}%  '
              f'σ_T*{v["Theta*"]["delta_%"]:+.2f}%')

    json.dump({"design_point": {"beta": float(X0[0]), "gamma": float(X0[1]), "Nr": int(X0[2])},
               "baseline": {t: float(base[j]) for j, t in enumerate(TARGETS)},
               "local_sensitivity": loc, "monte_carlo": mc, "sobol_bg": sob,
               "nr_discrete": nrd},
              open(os.path.join(OUT, "q5_result.json"), "w"), ensure_ascii=False, indent=2)
    Fs, _ = monte_carlo(models, X0)
    np.savez(os.path.join(OUT, "q5_arrays.npz"), Fs=Fs, base=base,
             loc=np.array([[loc[p][t]["S_norm"] for t in TARGETS] for p in PN]),
             sobST=np.array([[sob[t][p]["ST"] for p in CONT] for t in TARGETS]))
    print(f"\n[已保存] outputs/q5_result.json | q5_arrays.npz")


if __name__ == "__main__":
    run()
