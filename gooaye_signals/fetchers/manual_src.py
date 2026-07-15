"""manual_series — 手動維護的資料序列，讀 repo 內 data/manual/<key>.json。

給「沒有公開 API、但有公開可溯源出處」的數據用：季度財報披露（如 HPE AI 訂單）、
事件簿（具名客戶背書）、半年更的調查序列（如 Menlo 開源占比）。

鐵律：檔案裡每一個數據點都必須帶 src（出處）欄位——手動不等於不可溯源，
更新方式＝使用者口述或財報公布後由 agent 補一筆、commit 附出處。
離線、零網路：這就是 repo 裡的一個 JSON。
"""
from __future__ import annotations

import json
from typing import Mapping

import config


def fetch_manual(params: Mapping[str, object]) -> object:
    key = str(params["key"])
    path = config.DATA_DIR / "manual" / f"{key}.json"
    return json.loads(path.read_text(encoding="utf-8"))
