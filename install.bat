@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m venv .venv
if errorlevel 1 goto install_failed
goto venv_ready

:use_python
where python >nul 2>nul
if errorlevel 1 goto no_python
python -m venv .venv
if errorlevel 1 goto install_failed

:venv_ready
if not exist ".venv\Scripts\python.exe" goto install_failed

".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 goto old_python

".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto install_failed
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 goto install_failed

echo.
echo 安装完成。以后双击 run.bat 即可启动。
echo 按任意键关闭窗口……
pause >nul
exit /b 0

:no_python
echo.
echo 未找到 Python。请先安装 Python 3.10 或更高版本，并勾选 “Add Python to PATH”。
echo 按任意键关闭窗口……
pause >nul
exit /b 1

:old_python
echo.
echo Python 版本过低。本项目需要 Python 3.10 或更高版本。
echo 按任意键关闭窗口……
pause >nul
exit /b 1

:install_failed
echo.
echo 安装失败，请保留本窗口中的错误信息。
echo 按任意键关闭窗口……
pause >nul
exit /b 1
