# 问题二 · 代理模型四模型对照（统一留一法）

## 一键运行
```bash
bash run.sh
# 或指定数据路径:
bash run.sh /path/to/附件2.xlsx
```

## 目录结构
```
q2_project/
├── run.sh                  一键脚本(装依赖→跑模型→出图)
├── data_attachment2.xlsx   附件2数据(84组样本)
├── code/
│   ├── q2_run.py           四模型 × 三指标，统一留一法，导出结果与最终GP
│   └── q2_plots.py         读结果出三张图
├── outputs/                运行后生成
│   ├── results.json        训练R2/LOO_Q2/RMSE/MAE + RF重要度 + 弹性网系数
│   ├── final_gp_surrogates.pkl  最终GP代理(供问题三/五)
│   ├── loo_predictions.npz 全部留一预测值
│   └── data_clean.csv
└── figures/                运行后生成(三张svg)
```

## 四个模型
| 模型 | 特征 | 定位 |
|---|---|---|
| PhysElasticNet | 物理特征(1/γ,1/γ²,φ_mix,φ_block,Nr,β²,βNr,1+γ) | 可解释主力，验证问题一机理符号 |
| GP_Kriging | 原始(β,γ,Nr) | 精度主力，光滑可导、给方差，供问题三/五 |
| QuadRSM | 二次多项式 | 经典DOE基线 |
| RandomForest | 原始(β,γ,Nr) | 对照 + 特征重要度旁证 |

## 验证：统一留一法(LOO)
对每个(模型,指标)留一交叉验证，报告 LOO_Q2 = 1 − PRESS/TSS、RMSE、MAE。
三指标各自独立建模、各选各的最优。

## 调用最终代理(问题三/五)
```python
import pickle, numpy as np
gp = pickle.load(open("outputs/final_gp_surrogates.pkl","rb"))
# 预测 (beta, gamma, Nr) = (0.2, 4.0, 4)
X = np.array([[0.2, 4.0, 4]])
print(gp["R*"].predict(X), gp["dP*"].predict(X), gp["Theta*"].predict(X))
# 注意: 仅在设计域内插有效  beta∈[0,0.3] gamma∈[3,4.5] Nr∈[0,10]
```
