"""Phase 4 集中設定。驗證 → production 切換只改本檔。

故意不暴露 DCA_TIMEZONE 常數——bot 鎖死 Asia/Taipei：
- schedule 套件用本機 OS 時鐘排程（主機系統時區必須是 Asia/Taipei）
- date 邏輯統一用 trader.TAIPEI_TZ（fixed UTC+8，不依賴 IANA tzdata）
"""
from __future__ import annotations

from pathlib import Path

# === 模式切換 ===
DRY_RUN: bool = False  # True = 不打 API、不寫 daily_state，只 log + Telegram

# === DCA 參數 ===
DCA_AMOUNT_USDT: float = 5.5
SYMBOLS_ROTATION: tuple[str, ...] = ("ETH/USDT", "BTC/USDT")  # day % 2: 偶=ETH, 奇=BTC (plan D3)
DCA_TIME: str = "12:00"  # 24hr，本機時區（必須 Asia/Taipei）；驗證階段改 "23:55"

# === 安全網（覆蓋 trader.py 預設） ===
DAILY_CAP_USDT: float = 12.0  # 比 Phase 3 的 50 緊縮，符合驗證預算

# === Phase 4 新機制 ===
HEARTBEAT_HOURS: int = 6
MAX_CONSECUTIVE_FAILURES: int = 5
HIGH_WATER_MARK_USDT: float = 100.0  # 持倉總估值達此推播

# === 路徑 ===
DATA_DIR: Path = Path(__file__).resolve().parent / "data"
PRICES_DB: Path = DATA_DIR / "prices.sqlite"
RUNTIME_STATE: Path = DATA_DIR / "runtime_state.json"
