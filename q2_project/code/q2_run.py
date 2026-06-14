# -*- coding: utf-8 -*-
"""
问题二 · 代理模型四模型对照（统一留一法 LOO）
================================================
模型:
  1) PhysElasticNet  物理特征弹性网（承接问题一机理特征，可解释主力）
  2) GP_Kriging      高斯过程 / Kriging（光滑、可给方差，精度主力）
  3) QuadRSM         二次响应面（经典 DOE 基线）
  4) RandomForest    随机森林（对照 + 特征重要度旁证）
指标: R*（无量纲热阻）, dP*（无量纲压降）, Theta*（无量纲温度非均匀性）
验证: 对每个(模型,指标)做留一法; 报告 训练R2 / LOO_Q2 / RMSE / MAE
输出: results.json, loo_predictions.npz, final_gp_surrogates.pkl, en_coefficients.json
用法: python q2_run.py [数据xlsx路径]
"""
import sys, os, json, pickle, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.base import clone
from sklearn.linear_model import ElasticNetCV, LinearRegression
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel as C
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneOut

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data_attachment2.xlsx")
OUT  = os.path.join(HERE, "..", "outputs")
os.makedirs(OUT, exist_ok=True)

# ---------------- 读数据 ----------------
def load_data(path):
    df = pd.read_excel(path, sheet_name="Sheet1", header=1)
    df.columns = ["id", "beta", "gamma", "Nr", "R", "dP", "Theta"]
    df = df.dropna(subset=["beta"]).reset_index(drop=True)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c])
    return df

# ------------- 物理特征(承接问题一机理) -------------
PHYS_NAMES = ["1/gamma", "1/gamma^2", "phi_mix", "phi_block",
              "Nr", "beta^2", "beta*Nr", "(1+gamma)"]
def phys_features(X):
    b, g, N = X[:, 0], X[:, 1], X[:, 2]
    return np.column_stack([
        1.0 / g,                 # 歧管分配 ~ 1/gamma
        1.0 / g**2,              # 歧管动压损失 ~ 1/gamma^2
        1.0 - np.exp(-b * N),    # phi_mix 扰流强化(饱和), N=0时自动为0
        N * b**2 / (1 - b)**2,   # phi_block 针肋阻塞(局部阻力)
        N.astype(float),         # 排数(线性压降)
        b**2,                    # 针肋宽度二次
        b * N,                   # beta*Nr 交互
        1.0 + g,                 # 通道流速 ~ (1+gamma)
    ])

# ------------- 四个模型工厂 -------------
def make_models():
    en = Pipeline([
        ("sc", StandardScaler()),
        ("en", ElasticNetCV(l1_ratio=[.1, .3, .5, .7, .9, 1.0],
                            alphas=np.logspace(-4, 1, 40), cv=5, max_iter=20000)),
    ])
    kernel = (C(1.0, (1e-3, 1e3)) *
              Matern(length_scale=[1, 1, 1], length_scale_bounds=(1e-2, 1e2), nu=2.5)
              + WhiteKernel(1e-3, (1e-8, 1e-1)))
    gp = Pipeline([
        ("sc", StandardScaler()),
        ("gp", GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                        n_restarts_optimizer=4, alpha=1e-10)),
    ])
    rsm = Pipeline([
        ("poly", PolynomialFeatures(2, include_bias=False)),
        ("sc", StandardScaler()), ("lr", LinearRegression()),
    ])
    rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=2, random_state=0)
    # (estimator, 特征类型) : "phys"=物理特征, "raw"=原始(beta,gamma,Nr)
    return {"PhysElasticNet": (en, "phys"), "GP_Kriging": (gp, "raw"),
            "QuadRSM": (rsm, "raw"), "RandomForest": (rf, "raw")}

MODEL_ORDER = ["PhysElasticNet", "GP_Kriging", "QuadRSM", "RandomForest"]

def run():
    df = load_data(DATA)
    print(f"样本数 n = {len(df)}")
    X_raw = df[["beta", "gamma", "Nr"]].values
    F_phys = phys_features(X_raw)
    targets = {"R*": df["R"].values, "dP*": df["dP"].values, "Theta*": df["Theta"].values}
    getX = lambda kind: F_phys if kind == "phys" else X_raw

    loo = LeaveOneOut()
    results, loo_preds = {}, {}
    for tname, y in targets.items():
        results[tname], loo_preds[tname] = {}, {}
        ybar = y.mean(); tss = np.sum((y - ybar) ** 2)
        for mname, (est, kind) in make_models().items():
            X = getX(kind); yhat = np.zeros_like(y, float)
            for tr, te in loo.split(X):
                m = clone(est); m.fit(X[tr], y[tr]); yhat[te] = m.predict(X[te])
            press = np.sum((y - yhat) ** 2)
            results[tname][mname] = {
                "R2_train": float(1 - np.sum((y - clone(est).fit(getX(kind), y)
                                              .predict(getX(kind))) ** 2) / tss),
                "Q2_LOO": float(1 - press / tss),
                "RMSE": float(np.sqrt(np.mean((y - yhat) ** 2))),
                "MAE": float(np.mean(np.abs(y - yhat))),
            }
            loo_preds[tname][mname] = yhat

    # ---------- 打印对照表 ----------
    print("\n" + "=" * 74)
    print("四模型 × 三指标  统一留一法(LOO)对照")
    print("=" * 74)
    print(f'{"指标":<8}{"模型":<16}{"训练R2":>9}{"LOO_Q2":>9}{"RMSE":>10}{"MAE":>10}')
    print("-" * 74)
    best = {}
    for tname in targets:
        best[tname] = max(results[tname], key=lambda m: results[tname][m]["Q2_LOO"])
        for mname in MODEL_ORDER:
            r = results[tname][mname]
            star = "  <== 最优" if mname == best[tname] else ""
            print(f'{tname:<8}{mname:<16}{r["R2_train"]:>9.4f}{r["Q2_LOO"]:>9.4f}'
                  f'{r["RMSE"]:>10.5f}{r["MAE"]:>10.5f}{star}')
        print("-" * 74)

    # ---------- 随机森林特征重要度(旁证) ----------
    print("\n随机森林特征重要度 (beta, gamma, Nr):")
    rf_imp = {}
    for tname, y in targets.items():
        rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                   random_state=0).fit(X_raw, y)
        rf_imp[tname] = dict(zip(["beta", "gamma", "Nr"],
                                 [float(v) for v in rf.feature_importances_]))
        print(f"  {tname:<7}", {k: round(v, 3) for k, v in rf_imp[tname].items()})

    # ---------- 弹性网物理特征系数(可解释,验证问题一符号) ----------
    print("\n物理特征弹性网 标准化系数(全数据):")
    en_coef = {}
    for tname, y in targets.items():
        en = make_models()["PhysElasticNet"][0].fit(F_phys, y)
        co = en.named_steps["en"].coef_
        en_coef[tname] = {fn: float(c) for fn, c in zip(PHYS_NAMES, co)}
        print(f"  {tname}:")
        for fn, c in sorted(en_coef[tname].items(), key=lambda t: -abs(t[1])):
            if abs(c) > 1e-6:
                print(f"     {fn:<12}{c:+.4f}")

    # ---------- 重拟合最终GP(全84点)供问题三/五使用 ----------
    final = {}
    for tname, y in targets.items():
        kernel = (C(1.0, (1e-3, 1e3)) * Matern([1, 1, 1], (1e-2, 1e2), nu=2.5)
                  + WhiteKernel(1e-3, (1e-8, 1e-1)))
        final[tname] = Pipeline([
            ("sc", StandardScaler()),
            ("gp", GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                            n_restarts_optimizer=6, alpha=1e-10)),
        ]).fit(X_raw, y)

    # ---------- 保存 ----------
    json.dump({"results": results, "best_per_target": best,
               "rf_importance": rf_imp, "en_coefficients": en_coef},
              open(os.path.join(OUT, "results.json"), "w"),
              ensure_ascii=False, indent=2)
    np.savez(os.path.join(OUT, "loo_predictions.npz"),
             **{f"{t}__{m}": loo_preds[t][m] for t in loo_preds for m in loo_preds[t]},
             **{f"{t}__actual": targets[t] for t in targets})
    pickle.dump(final, open(os.path.join(OUT, "final_gp_surrogates.pkl"), "wb"))
    df.to_csv(os.path.join(OUT, "data_clean.csv"), index=False)
    print(f"\n[已保存到 outputs/] results.json | loo_predictions.npz | "
          f"final_gp_surrogates.pkl | data_clean.csv")

if __name__ == "__main__":
    run()
