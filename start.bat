@echo off
echo 正在启动智能电子生命体...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.11+
    pause
    exit /b 1
)

REM 创建必要的目录
if not exist "logs" mkdir logs
if not exist "data" mkdir data

REM 启动应用
python main.py

pause