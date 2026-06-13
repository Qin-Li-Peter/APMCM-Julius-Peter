# -*- coding: utf-8 -*-
"""共用代理模块：与问题二/三同核的高斯过程(Matern2.5+白噪声)。
   自训练、自包含，不读取任何 .pkl，避免跨版本 pickle 报错。"""
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel as C

TARGETS = ["R*", "dP*", "Theta*"]          # 三指标，均越小越好
BETA_RANGE  = (0.0, 0.30)
GAMMA_RANGE = (3.0, 4.5)
NR_LEVELS   = [0, 2, 4, 6, 8, 10]          # 针肋排数：整数偶数档


def load_data(path):
    df = pd.read_excel(path, sheet_name="Sheet1", header=1)
    df.columns = ["id", "beta", "gamma", "Nr", "R", "dP", "Theta"]
    df = df.dropna(subset=["beta"]).reset_index(drop=True)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c])
    return df


def train_surrogates(df, verbose=True):
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
        if verbose:
            r2 = 1 - np.sum((y - gp.predict(X))**2) / np.sum((y - y.mean())**2)
            print(f"  [GP] {t:<7} 训练R2 = {r2:.4f}", flush=True)
    return models


def predict_all(models, X):
    """返回 (n,3) 三指标预测矩阵，列顺序同 TARGETS。"""
    return np.column_stack([models[t].predict(X) for t in TARGETS])


def build_grid(n_grid=121):
    b = np.linspace(*BETA_RANGE, n_grid)
    g = np.linspace(*GAMMA_RANGE, n_grid)
    n = np.array(NR_LEVELS, float)
    B, G, Nr = np.meshgrid(b, g, n, indexing="ij")
    return np.column_stack([B.ravel(), G.ravel(), Nr.ravel()])


def is_pareto(F):
    """高效非支配筛选(均越小越好)；返回布尔掩码。"""
    order = np.argsort(F[:, 0], kind="mergesort")
    Fs = F[order]; keep = np.ones(len(F), dtype=bool)
    for i in range(len(F)):
        if not keep[i]:
            continue
        dominated = np.all(Fs[keep] <= Fs[i], axis=1) & np.any(Fs[keep] < Fs[i], axis=1)
        if dominated.any():
            keep[i] = False
        else:
            dom = np.all(Fs[keep] >= Fs[i], axis=1) & np.any(Fs[keep] > Fs[i], axis=1)
            keep[np.where(keep)[0][dom]] = False
    eff = np.zeros(len(F), dtype=bool); eff[order] = keep
    return eff
