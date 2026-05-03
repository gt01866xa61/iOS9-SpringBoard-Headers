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


def validate() -> None:
    """啟動時 fail-fast，避免 Stage 3 那種 trader.MIN/MAX 與 config 不一致悄悄
    跑到 23:55 才炸的情境。

    trader 的常數懶 import：trader.py 模組載入時會 import 本模組的
    DAILY_CAP_USDT，反向 import 必須延後到本函式被呼叫時（此時兩邊都已就緒）。
    """
    from trader import (
        MAX_SINGLE_BUY_USDT,
        MIN_SINGLE_BUY_USDT,
        SYMBOL_WHITELIST,
    )

    errors: list[str] = []

    if not (MIN_SINGLE_BUY_USDT <= DCA_AMOUNT_USDT <= MAX_SINGLE_BUY_USDT):
        errors.append(
            f"DCA_AMOUNT_USDT {DCA_AMOUNT_USDT} not in "
            f"[{MIN_SINGLE_BUY_USDT}, {MAX_SINGLE_BUY_USDT}] "
            f"(trader.MIN_SINGLE_BUY_USDT, trader.MAX_SINGLE_BUY_USDT)"
        )

    if DCA_AMOUNT_USDT > DAILY_CAP_USDT:
        errors.append(
            f"DCA_AMOUNT_USDT {DCA_AMOUNT_USDT} > DAILY_CAP_USDT {DAILY_CAP_USDT} "
            f"(single buy would always trip daily cap)"
        )

    bad_symbols = [s for s in SYMBOLS_ROTATION if s not in SYMBOL_WHITELIST]
    if bad_symbols:
        errors.append(
            f"SYMBOLS_ROTATION contains symbol(s) not in trader.SYMBOL_WHITELIST: "
            f"{bad_symbols} (allowed: {sorted(SYMBOL_WHITELIST)})"
        )

    if HEARTBEAT_HOURS <= 0:
        errors.append(f"HEARTBEAT_HOURS must be > 0, got {HEARTBEAT_HOURS}")

    if MAX_CONSECUTIVE_FAILURES <= 0:
        errors.append(
            f"MAX_CONSECUTIVE_FAILURES must be > 0, got {MAX_CONSECUTIVE_FAILURES}"
        )

    if errors:
        raise RuntimeError(
            "config.validate() failed:\n  - " + "\n  - ".join(errors)
        )
