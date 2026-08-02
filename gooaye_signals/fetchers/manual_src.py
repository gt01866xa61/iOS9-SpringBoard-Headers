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
_CAPEX_DIRECTIONS = {"raise", "maintain", "slow", "cut"}
_CSP_COMPANIES = {"alphabet", "microsoft", "meta"}
_CXMT_STAGES = {"plan", "construction", "volume", "delay", "restriction"}


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


def _validate_memory_margin(data: dict) -> None:
    """記憶體毛利率：單一公司、同一 GAAP 口徑的季序列。"""
    anchor = date.fromisoformat(_iso_date(data.get("as_of"), "memory_gross_margin.as_of"))
    for index, raw in enumerate(_list(data.get("series"), "memory_gross_margin.series")):
        where = f"memory_gross_margin.series[{index}]"
        point = _mapping(raw, where)
        point_date = date.fromisoformat(_iso_date(point.get("date"), f"{where}.date"))
        if point_date > anchor:
            raise ValueError(f"{where}.date 不得晚於 as_of")
        for field in ("label", "src"):
            _text(point, field, where)
        _optional_url(point, "src_url", where)
        margin = _number_or_none(point.get("gross_margin_pct"), f"{where}.gross_margin_pct")
        if margin is None or not 0 <= margin <= 100:
            raise ValueError(f"{where}.gross_margin_pct 必須在 0..100")


def _validate_csp_capex(data: dict) -> None:
    """CSP 財報指引：每筆是公司於一場法說的明確 CapEx 方向。"""
    anchor = date.fromisoformat(_iso_date(data.get("as_of"), "csp_capex_guidance.as_of"))
    for index, raw in enumerate(_list(data.get("reports"), "csp_capex_guidance.reports")):
        where = f"csp_capex_guidance.reports[{index}]"
        point = _mapping(raw, where)
        report_date = date.fromisoformat(_iso_date(point.get("date"), f"{where}.date"))
        if report_date > anchor:
            raise ValueError(f"{where}.date 不得晚於 as_of")
        for field in ("company", "period", "guidance", "src"):
            _text(point, field, where)
        _optional_url(point, "src_url", where)
        if point.get("company") not in _CSP_COMPANIES:
            raise ValueError(f"{where}.company 必須是 alphabet / microsoft / meta")
        if point.get("direction") not in _CAPEX_DIRECTIONS:
            raise ValueError(f"{where}.direction 必須是 raise / maintain / slow / cut")


def _validate_price_gap(data: dict) -> None:
    """現貨/合約價：只收同一品項的可直接比價快照。"""
    anchor = date.fromisoformat(_iso_date(data.get("as_of"), "memory_spot_contract_gap.as_of"))
    for index, raw in enumerate(_list(data.get("series"), "memory_spot_contract_gap.series")):
        where = f"memory_spot_contract_gap.series[{index}]"
        point = _mapping(raw, where)
        point_date = date.fromisoformat(_iso_date(point.get("date"), f"{where}.date"))
        if point_date > anchor:
            raise ValueError(f"{where}.date 不得晚於 as_of")
        for field in ("item", "currency", "src"):
            _text(point, field, where)
        _optional_url(point, "src_url", where)
        for field in ("spot", "contract"):
            value = _number_or_none(point.get(field), f"{where}.{field}")
            if value is None or value <= 0:
                raise ValueError(f"{where}.{field} 必須是正數")
        for field in ("spot_as_of", "contract_as_of"):
            quoted_on = date.fromisoformat(_iso_date(point.get(field), f"{where}.{field}"))
            if quoted_on > anchor:
                raise ValueError(f"{where}.{field} 不得晚於 as_of")


def _validate_cxmt_ramp(data: dict) -> None:
    """CXMT 擴產：計畫、施工與量產事件要分開，不能把計畫當成量產。"""
    anchor = date.fromisoformat(_iso_date(data.get("as_of"), "cxmt_ramp.as_of"))
    for index, raw in enumerate(_list(data.get("milestones"), "cxmt_ramp.milestones")):
        where = f"cxmt_ramp.milestones[{index}]"
        point = _mapping(raw, where)
        event_date = date.fromisoformat(_iso_date(point.get("date"), f"{where}.date"))
        if event_date > anchor:
            raise ValueError(f"{where}.date 不得晚於 as_of")
        for field in ("what", "src"):
            _text(point, field, where)
        _optional_url(point, "src_url", where)
        if point.get("stage") not in _CXMT_STAGES:
            raise ValueError(f"{where}.stage 非法")
        target_year = point.get("target_year")
        if target_year is not None and (isinstance(target_year, bool)
                                        or not isinstance(target_year, int)
                                        or not 2000 <= target_year <= 2100):
            raise ValueError(f"{where}.target_year 必須是 2000..2100 的整數或 null")
        target_wspm = _number_or_none(point.get("target_wspm_min"), f"{where}.target_wspm_min")
        if target_wspm is not None and target_wspm < 0:
            raise ValueError(f"{where}.target_wspm_min 不可為負數")


_VALIDATORS = {
    "hpe_dell_ai_orders": _validate_orders,
    "onprem_events": _validate_events,
    "menlo_opensource": _validate_menlo,
    "memory_gross_margin": _validate_memory_margin,
    "csp_capex_guidance": _validate_csp_capex,
    "memory_spot_contract_gap": _validate_price_gap,
    "cxmt_ramp": _validate_cxmt_ramp,
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
