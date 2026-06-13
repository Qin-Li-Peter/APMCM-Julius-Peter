#!/usr/bin/env bash
# 问题五 · 一键运行 (macOS/Linux)。用法: bash run.sh [数据xlsx] [beta gamma Nr]
set -e
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
ARGS="${*:-./data_attachment2.xlsx}"
echo ">>> [1/3] 依赖 ..."; $PY -c "import numpy,pandas,sklearn,matplotlib,openpyxl" 2>/dev/null || pip install -q numpy pandas scikit-learn matplotlib openpyxl
echo ">>> [2/3] 敏感性+蒙特卡洛+Sobol ..."; $PY code/q5_run.py $ARGS
echo ">>> [3/3] 绘图 ..."; $PY code/q5_plots.py
echo ">>> 完成。见 outputs/ 与 figures/"
