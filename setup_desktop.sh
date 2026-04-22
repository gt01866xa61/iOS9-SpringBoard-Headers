#!/bin/bash
# 一鍵在桌面建立「PDF 浮水印」捷徑
set -e

PYTHON=$(which python3)
SCRIPT=$(realpath "$(dirname "$0")/pdf_watermark.py")
DESKTOP_DIR="$HOME/Desktop"

if [ ! -f "$SCRIPT" ]; then
    echo "找不到 pdf_watermark.py，請確認此腳本和 pdf_watermark.py 在同一個資料夾。"
    exit 1
fi

mkdir -p "$DESKTOP_DIR"

DESKTOP_FILE="$DESKTOP_DIR/PDF浮水印.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=PDF 浮水印
Comment=將 PDF 拖曳到此圖示即可套用浮水印
Exec=$PYTHON $SCRIPT %F
Icon=application-pdf
Terminal=false
MimeType=application/pdf;
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"

# 在 GNOME 桌面環境下需要標記為信任，否則圖示不會執行
gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true

echo ""
echo "✓ 已安裝完成：$DESKTOP_FILE"
echo ""
echo "使用方式："
echo "  1. 在桌面找到「PDF 浮水印」圖示"
echo "  2. 直接把 PDF 檔案拖曳到那個圖示上"
echo "  3. 會自動跳出浮水印設定對話框"
echo "  4. 設定完成後按「套用浮水印」"
