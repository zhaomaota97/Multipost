@echo off
chcp 65001 >nul
cd /d %~dp0
echo ============================================
echo   视频一键发布 - 首次安装
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 没有检测到 Python，请先安装 Python 3.10+ 并勾选 Add to PATH
  echo 下载地址：https://www.python.org/downloads/
  pause
  exit /b 1
)

echo [1/3] 创建虚拟环境 venv ...
if not exist venv (
  python -m venv venv
)

echo [2/3] 安装依赖 ...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] 安装浏览器内核（Playwright Chromium）...
python -m playwright install chromium

echo.
echo ============================================
echo   安装完成！双击「启动.bat」即可使用。
echo ============================================
pause
