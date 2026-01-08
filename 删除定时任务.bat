@echo off
chcp 65001 >nul 2>&1
title 巴南图书馆自动抢座系统 - 删除定时任务
color 0c

echo ======================================================
echo      巴南图书馆自动抢座系统 - 删除定时任务
echo ======================================================
echo.

set "TASK_NAME=BNLibrary_SeatReservation"

:: 检查任务是否存在
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 未找到定时任务"%TASK_NAME%"
    echo [提示] 任务可能已被删除或从未创建
    pause
    exit /b 0
)

echo [警告] 即将删除定时任务：%TASK_NAME%
echo.
set /p confirm="确认删除？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo [取消] 操作已取消
    pause
    exit /b 0
)

:: 删除任务
schtasks /delete /tn "%TASK_NAME%" /f

if %errorlevel% equ 0 (
    echo.
    echo ======================================================
    echo            ✅ 定时任务已成功删除！
    echo ======================================================
    echo.
) else (
    echo.
    echo ======================================================
    echo            ❌ 删除失败！
    echo ======================================================
    echo.
    echo [错误] 可能需要管理员权限
    echo [提示] 请右键此脚本，选择"以管理员身份运行"
    echo.
)

pause

