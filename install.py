"""
PDF 浮水印工具 - 智能環境安裝程式
執行方式：雙擊 install.bat，或直接 python install.py
"""
import sys
import subprocess
import importlib.metadata

REQUIRED = [
    # (顯示名稱,  pip metadata 名稱,  最低版本 tuple,   安裝用名稱)
    ("PyMuPDF",     "pymupdf",      (1, 23, 0), "PyMuPDF"),
    ("Pillow",      "pillow",       (10, 0, 0), "Pillow"),
    ("tkinterdnd2", "tkinterdnd2",  (0,  3, 0), "tkinterdnd2"),
]

SEP = "=" * 52

def parse_version(v_str):
    try:
        return tuple(int(x) for x in str(v_str).split(".")[:3])
    except Exception:
        return (0,)

def fmt_ver(t):
    return ".".join(str(x) for x in t)

def get_installed(meta_name):
    try:
        return importlib.metadata.version(meta_name)
    except importlib.metadata.PackageNotFoundError:
        return None

def pip_install(pkg_name, spec, upgrade=False):
    cmd = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.append(spec)
    return subprocess.run(cmd, capture_output=True, text=True)

# ── 標題 ──────────────────────────────────────────
print(SEP)
print("   PDF 浮水印工具 - 智能環境檢查 & 安裝")
print(SEP)
print()

# ── Python 版本檢查 ───────────────────────────────
pv = sys.version_info
pv_str = f"{pv.major}.{pv.minor}.{pv.micro}"
if pv >= (3, 10):
    print(f"  [OK]   Python {pv_str}")
else:
    print(f"  [!]    Python {pv_str}  ← 版本過舊，需要 3.10 以上")
    print()
    print("  請至以下網址下載新版 Python：")
    print("  https://www.python.org/downloads/")
    print("  安裝時務必勾選「Add Python to PATH」")
    print()
    input("按 Enter 結束...")
    sys.exit(1)

print()
print("  套件狀態：")
print()

# ── 逐一檢查並處理套件 ───────────────────────────
all_ok = True
for pkg_name, meta_name, min_ver_t, install_name in REQUIRED:
    min_spec = f"{install_name}>={fmt_ver(min_ver_t)}"
    installed_str = get_installed(meta_name)

    if installed_str is None:
        # 從未安裝
        print(f"  [安裝中] {pkg_name:<14} 未安裝  →  安裝中...", end="", flush=True)
        r = pip_install(pkg_name, min_spec)
        if r.returncode == 0:
            new_v = get_installed(meta_name) or "?"
            print(f"  完成 ({new_v})")
        else:
            print("  失敗！")
            print(f"           錯誤：{r.stderr.strip()[:200]}")
            all_ok = False

    else:
        installed_t = parse_version(installed_str)
        if installed_t < min_ver_t:
            # 已安裝但版本過舊
            print(f"  [更新中] {pkg_name:<14} {installed_str} < {fmt_ver(min_ver_t)}  →  更新中...", end="", flush=True)
            r = pip_install(pkg_name, min_spec, upgrade=True)
            if r.returncode == 0:
                new_v = get_installed(meta_name) or "?"
                print(f"  完成 ({new_v})")
            else:
                print("  失敗！")
                all_ok = False
        else:
            # 版本 OK，略過
            print(f"  [OK]   {pkg_name:<14} {installed_str}  （版本符合，略過）")

# ── 結果摘要 ─────────────────────────────────────
print()
print(SEP)
if all_ok:
    print("  全部就緒！可以開始使用 PDF 浮水印工具")
    print(SEP)
    print()
    print("  使用方式：")
    print("    將任意 PDF 檔案拖曳到 pdf_watermark.pyw 上即可")
else:
    print("  部分套件安裝失敗，請確認網路連線後重試")
    print(SEP)

print()
input("按 Enter 關閉...")
