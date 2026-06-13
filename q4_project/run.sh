#!/usr/bin/env bash
# 问题四 · 一键运行 (macOS/Linux): 权重敏感性 + 鲁棒设计。用法: bash run.sh [数据xlsx]
set -e
cd "$(dirname "$0")"
DATA="${1:-./data_attachment2.xlsx}"; PY="${PYTHON:-python3}"
echo ">>> [1/3] 依赖 ..."; $PY -c "import numpy,pandas,sklearn,matplotlib,openpyxl" 2>/dev/null || pip install -q numpy pandas scikit-learn matplotlib openpyxl
echo ">>> [2/3] 权重扫描 + 鲁棒设计 ..."; $PY code/q4_run.py "$DATA"
echo ">>> [3/3] 绘图 ..."; $PY code/q4_plots.py
echo ">>> 完成。见 outputs/ 与 figures/"
