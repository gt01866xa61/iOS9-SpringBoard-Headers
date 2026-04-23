@echo off
chcp 65001 >nul
title PDF 浮水印 - 環境安裝

echo.
echo  ====================================
echo   PDF 浮水印工具 - 一鍵環境安裝
echo  ====================================
echo.

:: 確認 Python 是否已安裝
where python >nul 2>&1
if errorlevel 1 (
    echo  [!] 找不到 Python！
    echo.
    echo  請先：
    echo    1. 前往 https://www.python.org/downloads/
    echo    2. 安裝時勾選「Add Python to PATH」
    echo    3. 裝好後重新雙擊此檔案
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK] %%v
echo.
echo  正在檢查套件（已是最新版本會自動略過）...
echo.

python -m pip install "PyMuPDF>=1.23.0" "Pillow>=10.0.0" "tkinterdnd2>=0.3.0"

if errorlevel 1 (
    echo.
    echo  [!] 安裝過程出錯，請確認網路連線後重試
    pause
    exit /b 1
)

echo.
echo  ====================================
echo   完成！環境已就緒
echo  ====================================
echo.
echo  使用方式：將 PDF 拖曳到 pdf_watermark.pyw 上
echo.
pause
