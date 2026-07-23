"""manual_series — 手動維護的資料序列，讀 repo 內 data/manual/<key>.json。

給「沒有公開 API、但有公開可溯源出處」的數據用：季度財報披露（如 HPE AI 訂單）、
事件簿（具名客戶背書）、半年更的調查序列（如 Menlo 開源占比）。

鐵律：檔案裡每一個數據點都必須帶 src（出處）欄位——手動不等於不可溯源，
更新方式＝使用者口述或財報公布後由 agent 補一筆、commit 附出處。
離線、零網路：這就是 repo 裡的一個 JSON。
"""
from __future__ import annotations

import json
import math
from datetime import date
from typing import Mapping

import config


_EVENT_TYPES = {"endorse", "supply", "data", "narrative"}
_EVENT_DIRS = {"+", "-", "0"}


def _mapping(value: object, where: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{where} 必須是 object")
    return value


def _list(value: object, where: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{where} 必須是 array")
    return value


def _text(point: dict, field: str, where: str) -> str:
    value = point.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}.{field} 必須是非空字串")
    return value


def _optional_url(point: dict, field: str, where: str) -> None:
    value = point.get(field)
    if value is not None and (not isinstance(value, str)
                              or not value.startswith(("https://", "http://"))):
        raise ValueError(f"{where}.{field} 必須是完整 http(s) URL")


def _iso_date(value: object, where: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{where} 必須是 YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{where} 必須是 YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{where} 必須是 YYYY-MM-DD")
    return value


def _number_or_none(value: object, where: str) -> float | int | None:
    if value is None:
        return None
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value)):
        raise ValueError(f"{where} 必須是數字或 null")
    return value


def _validate_orders(data: dict) -> None:
    _iso_date(data.get("as_of"), "hpe_dell_ai_orders.as_of")
    for company in ("hpe", "dell"):
        entries = _list(data.get(company), f"hpe_dell_ai_orders.{company}")
        for index, raw in enumerate(entries):
            where = f"hpe_dell_ai_orders.{company}[{index}]"
            point = _mapping(raw, where)
            _text(point, "q", where)
            _text(point, "src", where)
            _optional_url(point, "src_url", where)
            order = _number_or_none(point.get("orders_b"), f"{where}.orders_b")
            backlog = _number_or_none(point.get("backlog_b"), f"{where}.backlog_b")
            if order is None and backlog is None:
                raise ValueError(f"{where} 的 orders_b/backlog_b 不可同時為 null")
            if any(value is not None and value < 0 for value in (order, backlog)):
                raise ValueError(f"{where} 的 orders_b/backlog_b 不可為負數")


def _validate_events(data: dict) -> None:
    anchor = date.fromisoformat(_iso_date(data.get("as_of"), "onprem_events.as_of"))
    for index, raw in enumerate(_list(data.get("events"), "onprem_events.events")):
        where = f"onprem_events.events[{index}]"
        point = _mapping(raw, where)
        event_date = date.fromisoformat(_iso_date(point.get("date"), f"{where}.date"))
        if event_date > anchor:
            raise ValueError(f"{where}.date 不得晚於 as_of")
        for field in ("camp", "what", "src"):
            _text(point, field, where)
        _optional_url(point, "src_url", where)
        if point.get("dir") not in _EVENT_DIRS:
            raise ValueError(f"{where}.dir 必須是 + / - / 0")
        if point.get("type") not in _EVENT_TYPES:
            raise ValueError(f"{where}.type 非法")


def _validate_menlo(data: dict) -> None:
    _iso_date(data.get("as_of"), "menlo_opensource.as_of")
    for index, raw in enumerate(_list(data.get("series"), "menlo_opensource.series")):
        where = f"menlo_opensource.series[{index}]"
        point = _mapping(raw, where)
        _text(point, "label", where)
        _text(point, "src", where)
        _optional_url(point, "src_url", where)
        _optional_url(point, "total_src_url", where)
        pct = _number_or_none(point.get("pct"), f"{where}.pct")
        if pct is None or not 0 <= pct <= 100:
            raise ValueError(f"{where}.pct 必須在 0..100")
        total = _number_or_none(point.get("total_b"), f"{where}.total_b")
        if total is not None:
            if total < 0:
                raise ValueError(f"{where}.total_b 不可為負數")
            _text(point, "total_src", where)


_VALIDATORS = {
    "hpe_dell_ai_orders": _validate_orders,
    "onprem_events": _validate_events,
    "menlo_opensource": _validate_menlo,
}


def validate_manual(key: str, payload: object) -> dict:
    """嚴格驗證目前正式 manual key；新 key 必須先宣告 schema，不能裸資料上線。"""
    data = _mapping(payload, key)
    validator = _VALIDATORS.get(key)
    if validator is None:
        raise ValueError(f"manual_series 未宣告 schema：{key}")
    validator(data)
    return data


def fetch_manual(params: Mapping[str, object]) -> object:
    key = str(params["key"])
    path = config.DATA_DIR / "manual" / f"{key}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_manual(key, payload)
