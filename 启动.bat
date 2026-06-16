@echo off
chcp 65001 >nul
cd /d %~dp0

if not exist venv (
  echo [提示] 还没有安装，请先双击运行「安装.bat」
  pause
  exit /b 1
)

call venv\Scripts\activate.bat
set PYTHONUTF8=1
echo 正在启动服务，稍后会自动打开浏览器……
start "" http://127.0.0.1:8800
python run.py
pause
