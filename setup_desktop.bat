@echo off
chcp 65001 >nul
title 建立桌面捷徑

echo.
echo  ============================================
echo   PDF 浮水印工具 - 建立桌面捷徑
echo  ============================================
echo.

set "THIS_DIR=%~dp0"

:: 確認安裝程式存在
if not exist "%THIS_DIR%install.bat" (
    echo  [!] 找不到 install.bat
    echo      請確認此腳本與 install.bat 放在同一資料夾
    echo.
    pause
    exit /b 1
)

:: 使用 PowerShell 建立 .lnk 捷徑
:: 透過環境變數 THIS_DIR 傳遞路徑，避免中文或空白路徑造成問題
powershell -ExecutionPolicy Bypass -NoProfile -Command ^
 "$dir = $env:THIS_DIR;" ^
 "$desk = [Environment]::GetFolderPath('Desktop');" ^
 "$ws = New-Object -ComObject WScript.Shell;" ^
 "$sc = $ws.CreateShortcut($desk + '\PDF浮水印-安裝環境.lnk');" ^
 "$sc.TargetPath  = $dir + 'install.bat';" ^
 "$sc.WorkingDirectory = $dir;" ^
 "$sc.Description = 'PDF浮水印工具 - 一鍵安裝/更新套件環境';" ^
 "$sc.Save();" ^
 "Write-Host '  [OK] 捷徑：PDF浮水印-安裝環境';" ^
 "$sc2 = $ws.CreateShortcut($desk + '\PDF浮水印工具.lnk');" ^
 "$sc2.TargetPath  = $dir + 'pdf_watermark.pyw';" ^
 "$sc2.WorkingDirectory = $dir;" ^
 "$sc2.Description = '將 PDF 拖曳到此圖示即可套用浮水印';" ^
 "$sc2.Save();" ^
 "Write-Host '  [OK] 捷徑：PDF浮水印工具'"

if errorlevel 1 (
    echo.
    echo  [!] 建立失敗
    echo      請在此檔案上按右鍵 ^> 以系統管理員身份執行
    echo.
    pause
    exit /b 1
)

echo.
echo  ============================================
echo   桌面捷徑建立完成！
echo  ============================================
echo.
echo   【PDF浮水印-安裝環境】
echo     雙擊 → 智能檢查並安裝/更新所需套件
echo.
echo   【PDF浮水印工具】
echo     拖曳 PDF 到此圖示 → 自動套用浮水印
echo.
pause
