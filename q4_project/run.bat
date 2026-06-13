@echo off
chcp 65001 >nul
REM ===== 问题四 . 一键运行 (Windows): 权重敏感性 + 鲁棒设计 =====
setlocal
cd /d "%~dp0"
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY ( echo [错误] 未找到 Python, 请装 Python3 并勾 Add to PATH & pause & exit /b 1 )
echo 使用解释器: %PY%
set "DATA=%~1"
if "%DATA%"=="" set "DATA=data_attachment2.xlsx"
echo.
echo ^>^>^> [1/3] 检查/安装依赖 ...
%PY% -c "import numpy,pandas,sklearn,matplotlib,openpyxl" 2>nul
if errorlevel 1 ( echo     安装依赖... & %PY% -m pip install -q numpy pandas scikit-learn matplotlib openpyxl )
echo.
echo ^>^>^> [2/3] 权重扫描 + 鲁棒设计 ...
%PY% code\q4_run.py "%DATA%"
if errorlevel 1 ( echo [错误] 运行失败 & pause & exit /b 1 )
echo.
echo ^>^>^> [3/3] 生成图表 ...
%PY% code\q4_plots.py
if errorlevel 1 ( echo [错误] 绘图失败 & pause & exit /b 1 )
echo.
echo ^>^>^> 完成. 产物:
echo     outputs\q4_result.json        鲁棒设计 + 各场景最优 + win-share前5
echo     outputs\q4_arrays.npz         绘图数组
echo     figures\fig1_weight_simplex.svg  权重单纯形最优归属(三角图)
echo     figures\fig2_param_drift.svg     参数随偏好漂移
echo.
pause
endlocal
