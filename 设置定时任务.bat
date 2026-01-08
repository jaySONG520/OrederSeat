@echo off
chcp 65001 >nul 2>&1
title 巴南图书馆自动抢座系统 - 定时任务设置
color 0b

echo ======================================================
echo      巴南图书馆自动抢座系统 - 定时任务设置工具
echo ======================================================
echo.

:: 获取当前脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "BAT_FILE=%SCRIPT_DIR%一键开启抢座.bat"
set "TASK_NAME=BNLibrary_SeatReservation"

echo [提示] 将创建每天 21:55 自动运行的定时任务
echo [提示] 任务名称：%TASK_NAME%
echo [提示] 执行文件：%BAT_FILE%
echo.

:: 检查批处理文件是否存在
if not exist "%BAT_FILE%" (
    echo [错误] 未找到 一键开启抢座.bat 文件！
    echo [提示] 请确保此脚本与 一键开启抢座.bat 在同一目录
    pause
    exit /b 1
)

:: 检查是否已存在同名任务
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [提示] 检测到已存在的定时任务，正在删除旧任务...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
    if %errorlevel% neq 0 (
        echo [警告] 删除旧任务失败，可能需要管理员权限
    ) else (
        echo [成功] 已删除旧任务
    )
    echo.
)

:: 创建新的定时任务
echo [状态] 正在创建定时任务...
echo.

:: 使用 schtasks 创建每天 21:55 运行的任务
:: 注意：使用英文任务名避免编码问题，路径需要正确转义
schtasks /create /tn "%TASK_NAME%" /tr "\"%BAT_FILE%\"" /sc daily /st 21:55 /f

if %errorlevel% equ 0 (
    echo.
    echo ======================================================
    echo            ✅ 定时任务创建成功！
    echo ======================================================
    echo.
    echo [任务信息]
    echo   任务名称：%TASK_NAME%
    echo   执行时间：每天 21:55
    echo   执行文件：%BAT_FILE%
    echo.
    echo [提示] 脚本会在 21:55 启动，然后等待到 21:59:59.850 自动抢座
    echo [提示] 你可以通过以下方式管理定时任务：
    echo   1. 打开"任务计划程序"（taskschd.msc）
    echo   2. 查找任务"%TASK_NAME%"
    echo   3. 可以手动运行、禁用或删除任务
    echo.
    echo [命令] 查看任务：schtasks /query /tn "%TASK_NAME%"
    echo [命令] 删除任务：schtasks /delete /tn "%TASK_NAME%" /f
    echo [命令] 立即运行：schtasks /run /tn "%TASK_NAME%"
    echo.
) else (
    echo.
    echo ======================================================
    echo            ❌ 定时任务创建失败！
    echo ======================================================
    echo.
    echo [错误] 可能需要管理员权限
    echo [提示] 请右键此脚本，选择"以管理员身份运行"
    echo.
)

pause

