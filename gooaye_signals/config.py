"""全域設定。單一真相來源，改參數只動這裡。時鐘鎖死 Asia/Taipei fixed UTC+8。

故意不暴露時區設定常數——平台鎖死 Asia/Taipei：所有日期／時間邏輯統一用 TAIPEI_TZ
(fixed UTC+8，不依賴 IANA tzdata)，沿用 crypto_dca_bot 的 Windows-tzdata 教訓。
"""
from __future__ import annotations

import os
from datetime import timedelta, timezone
from pathlib import Path

# === 時區（固定 UTC+8）===
TAIPEI_TZ = timezone(timedelta(hours=8), name="Asia/Taipei")

# === Schema 版本（前端會 guard，破壞性變更才 +1）===
SCHEMA_VERSION = 1

# === 路徑 ===
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
SIGNALS_JSON = DATA_DIR / "signals.json"
HISTORY_JSON = DATA_DIR / "history.json"   # 燈號歷史（CI 每日 commit 回 repo 持久化）
WEB_DIR = BASE_DIR / "web"
WEB_DATA_JSON = WEB_DIR / "data" / "signals.json"
DEMO_FIXTURES_DIR = BASE_DIR / "demo" / "fixtures"

# === 模式切換 ===
# GOOAYE_DEMO=1 → 離線讀 demo/fixtures，不打任何網路 API（本機開發／測試／產內嵌 fallback）
DEMO_MODE: bool = os.environ.get("GOOAYE_DEMO") == "1"

# === 前端顯示文案 ===
NEXT_UPDATE_HINT = "平日約每 30 分更新一次，假日每日補跑"

# === 陳舊判定：updated_at 超過該訊號 cadence 的幾倍即視為 stale ===
STALE_CADENCE_MULTIPLIER = 2

# === 燈號歷史 ===
HISTORY_KEEP_DAYS = 45    # 檔案保留天數上限
HISTORY_SHOW_DAYS = 30    # 前端燈帶顯示天數

# === 各 cadence 對應的「新鮮秒數」上限（× STALE_CADENCE_MULTIPLIER 才算舊）===
CADENCE_SECONDS: dict[str, int] = {
    "trading_day": 24 * 3600,
    "daily": 24 * 3600,
    "monthly": 31 * 24 * 3600,
    "manual": 365 * 24 * 3600,
}
