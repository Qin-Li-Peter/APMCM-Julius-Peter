@echo off
chcp 65001 >nul
REM ===== 问题五 . 一键运行 (Windows): 参数扰动敏感性与稳定性 =====
REM 默认评估鲁棒解(0.22,4.5,4); 自定义: run.bat data.xlsx 0.21 4.5 6
setlocal
cd /d "%~dp0"
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY ( echo [错误] 未找到 Python, 请装 Python3 并勾 Add to PATH & pause & exit /b 1 )
echo 使用解释器: %PY%
set "ARGS=%*"
if "%ARGS%"=="" set "ARGS=data_attachment2.xlsx"
echo.
echo ^>^>^> [1/3] 检查/安装依赖 ...
%PY% -c "import numpy,pandas,sklearn,matplotlib,openpyxl" 2>nul
if errorlevel 1 ( echo     安装依赖... & %PY% -m pip install -q numpy pandas scikit-learn matplotlib openpyxl )
echo.
echo ^>^>^> [2/3] 敏感性 + 蒙特卡洛 + Sobol ...
%PY% code\q5_run.py %ARGS%
if errorlevel 1 ( echo [错误] 运行失败 & pause & exit /b 1 )
echo.
echo ^>^>^> [3/3] 生成图表 ...
%PY% code\q5_plots.py
if errorlevel 1 ( echo [错误] 绘图失败 & pause & exit /b 1 )
echo.
echo ^>^>^> 完成. 产物:
echo     outputs\q5_result.json        局部灵敏度/蒙特卡洛/Sobol/N_r离散检查
echo     outputs\q5_arrays.npz         绘图数组
echo     figures\fig1_sensitivity_heatmap.svg  局部灵敏度热图
echo     figures\fig2_montecarlo.svg           蒙特卡洛分布
echo     figures\fig3_sobol.svg                Sobol(β,γ)贡献占比
echo.
pause
endlocal
