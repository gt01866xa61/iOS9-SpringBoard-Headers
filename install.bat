@echo off
chcp 65001 >nul
title PDF 浮水印工具 - 環境安裝

echo.
echo  正在確認 Python 是否已安裝...
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo  ============================================
    echo  [!] 找不到 Python，請先完成以下步驟：
    echo  ============================================
    echo.
    echo   1. 前往 https://www.python.org/downloads/
    echo   2. 下載 Python 3.10 以上版本
    echo   3. 安裝時「必須」勾選 Add Python to PATH
    echo   4. 安裝完畢後，重新雙擊 install.bat
    echo.
    pause
    exit /b 1
)

python "%~dp0install.py"
