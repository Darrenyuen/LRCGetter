@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo 首次运行，正在创建独立 Python 环境……
    call "%~dp0install.bat"
    if errorlevel 1 goto run_failed
)

".venv\Scripts\python.exe" -c "import bs4, lxml, pyqqmusicdes, requests" >nul 2>nul
if errorlevel 1 (
    echo 检测到依赖不完整，正在重新安装……
    ".venv\Scripts\python.exe" -m pip install -e .
    if errorlevel 1 goto run_failed
)

".venv\Scripts\python.exe" -m qrcd.cli
set "QRCD_EXIT=%errorlevel%"
echo.
if not "%QRCD_EXIT%"=="0" echo 程序退出，状态码：%QRCD_EXIT%
echo 按任意键关闭窗口……
pause >nul
exit /b %QRCD_EXIT%

:run_failed
echo.
echo 启动失败，请保留本窗口中的错误信息。
echo 按任意键关闭窗口……
pause >nul
exit /b 1
