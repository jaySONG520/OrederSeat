@echo off
title 巴南图书馆自动抢座系统 - 考研加油！
color 0a

echo ======================================================
echo           巴南图书馆自动抢座系统 (Windows版)
echo ======================================================
echo.

:: 1. 检查 Python 环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境，请先安装 Python 3.13。
    pause
    exit
)

:: 2. 检查依赖库 requests
python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在安装必要的 requests 库...
    pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo [状态] 环境检查通过。
echo [状态] 脚本将持续监控时间，并在 21:59:59.850 自动触发。
echo [提示] 请确保 reserve_seat.py 中的 ACCESS_TOKEN 是最新的！
echo.
echo ======================================================
echo           正在启动 Python 核心脚本...
echo ======================================================

:: 3. 运行 Python 脚本
python reserve_seat.py

echo.
echo ======================================================
echo           程序运行结束，请检查上方预约结果。
echo ======================================================
pause