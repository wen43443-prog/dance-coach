@echo off
chcp 65001 >nul
title 舞帧 - 本地服务器
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python serve.py
) else (
  where py >nul 2>nul
  if %errorlevel%==0 (
    py serve.py
  ) else (
    echo 未找到 Python，请先安装 Python，或直接双击 index.html 在电脑上使用。
  )
)
pause
