#!/usr/bin/env bash
# 问题三 · 一键运行 (macOS / Linux)。用法: bash run.sh [数据xlsx路径]
set -e
cd "$(dirname "$0")"
DATA="${1:-./data_attachment2.xlsx}"
PY="${PYTHON:-python3}"
echo ">>> [1/3] 检查/安装依赖 ..."
$PY -c "import numpy,pandas,sklearn,matplotlib,openpyxl" 2>/dev/null || \
    pip install -q numpy pandas scikit-learn matplotlib openpyxl
echo ">>> [2/3] 网格穷举 + 膝点优化 ..."
$PY code/q3_run.py "$DATA"
echo ">>> [3/3] 生成图表 ..."
$PY code/q3_plots.py
echo ">>> 完成。见 outputs/ 与 figures/"
