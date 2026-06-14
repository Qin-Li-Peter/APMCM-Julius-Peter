@echo off
chcp 65001 >nul
REM =====================================================================
REM  问题二 . 一键运行脚本 (Windows)
REM    1) 检查/安装依赖   2) 跑四模型留一法对照   3) 出三张图
REM  用法: 双击 run.bat  或在 cmd 里执行  run.bat
REM        指定数据:  run.bat "C:\路径\附件2.xlsx"
REM =====================================================================
setlocal
cd /d "%~dp0"

REM ---- 找 Python 解释器 (优先 py 启动器, 其次 python) ----
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo [错误] 未找到 Python。请先安装 Python 3 并勾选 "Add to PATH"。
    echo        下载: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo 使用解释器: %PY%

REM ---- 数据路径 (默认当前目录下的 data_attachment2.xlsx) ----
set "DATA=%~1"
if "%DATA%"=="" set "DATA=data_attachment2.xlsx"

echo.
echo ^>^>^> [1/3] 检查/安装依赖 ...
%PY% -c "import numpy,pandas,sklearn,matplotlib,openpyxl" 2>nul
if errorlevel 1 (
    echo     缺少依赖, 正在安装 ...
    %PY% -m pip install -q numpy pandas scikit-learn matplotlib openpyxl
    if errorlevel 1 (
        echo [错误] 依赖安装失败, 请检查网络或手动运行:
        echo        %PY% -m pip install numpy pandas scikit-learn matplotlib openpyxl
        pause
        exit /b 1
    )
)

echo.
echo ^>^>^> [2/3] 运行四模型对照(统一留一法) ...
%PY% code\q2_run.py "%DATA%"
if errorlevel 1 ( echo [错误] 模型运行失败 & pause & exit /b 1 )

echo.
echo ^>^>^> [3/3] 生成图表 ...
%PY% code\q2_plots.py
if errorlevel 1 ( echo [错误] 绘图失败 & pause & exit /b 1 )

echo.
echo ^>^>^> 完成. 产物:
echo     outputs\results.json              四模型x三指标 训练R2/LOO_Q2/RMSE/MAE + 重要度 + 弹性网系数
echo     outputs\final_gp_surrogates.pkl   最终GP代理(全数据重拟合) 供问题三/五
echo     outputs\loo_predictions.npz       全部LOO预测值
echo     outputs\data_clean.csv            清洗后数据
echo     figures\fig1_model_comparison.svg 四模型 Q2 对照
echo     figures\fig2_gp_pred_vs_actual.svg GP 预测-真实散点
echo     figures\fig3_main_effects.svg     主效应折线(印证问题一机理)
echo.
pause
endlocal
