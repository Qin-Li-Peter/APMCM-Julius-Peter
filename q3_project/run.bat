@echo off
chcp 65001 >nul
REM =====================================================================
REM  问题三 . 一键运行 (Windows)
REM    网格穷举求 Pareto 前沿 + 膝点法选综合最优
REM  用法: 双击 run.bat  或  run.bat "C:\路径\附件2.xlsx"
REM =====================================================================
setlocal
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
    echo [错误] 未找到 Python。请先安装 Python 3 并勾选 "Add to PATH"。
    echo        下载: https://www.python.org/downloads/
    pause & exit /b 1
)
echo 使用解释器: %PY%

set "DATA=%~1"
if "%DATA%"=="" set "DATA=data_attachment2.xlsx"

echo.
echo ^>^>^> [1/3] 检查/安装依赖 ...
%PY% -c "import numpy,pandas,sklearn,matplotlib,openpyxl" 2>nul
if errorlevel 1 (
    echo     缺少依赖, 正在安装 ...
    %PY% -m pip install -q numpy pandas scikit-learn matplotlib openpyxl
    if errorlevel 1 ( echo [错误] 依赖安装失败 & pause & exit /b 1 )
)

echo.
echo ^>^>^> [2/3] 网格穷举 + 膝点优化 ...
%PY% code\q3_run.py "%DATA%"
if errorlevel 1 ( echo [错误] 优化运行失败 & pause & exit /b 1 )

echo.
echo ^>^>^> [3/3] 生成图表 ...
%PY% code\q3_plots.py
if errorlevel 1 ( echo [错误] 绘图失败 & pause & exit /b 1 )

echo.
echo ^>^>^> 完成. 产物:
echo     outputs\q3_result.json        综合最优方案(膝点)+理想点交叉验证+锚点
echo     outputs\pareto_front.csv      完整 Pareto 前沿(beta,gamma,Nr 及三指标)
echo     outputs\pareto_arrays.npz     绘图用数组
echo     figures\fig1_pareto_3d.svg    三维前沿+膝点
echo     figures\fig2_pareto_projections.svg  三张两两投影
echo.
pause
endlocal
