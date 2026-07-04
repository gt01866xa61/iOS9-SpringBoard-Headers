"""建置進入點：探索所有 signal → 批次抓資料(去重) → 逐 signal 純 compute(互相隔離)
→ 算每個 cluster 主燈與總燈 → atomic 寫出 data/signals.json（有 web/ 也寫一份給前端）。

時鐘鎖死 Asia/Taipei fixed UTC+8。任一 signal 或來源失敗只讓那張卡走 last-good + stale
或 gray，絕不讓整版 blank；本輪若完全產不出可用 JSON → 保留上一版 committed 檔案。
GitHub Actions cron 跑這支；本機 `GOOAYE_DEMO=1 python build.py` 可離線跑。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import config
from core.clusters import CLUSTERS, master_light
from core.spec import LIGHT_SEVERITY, SignalResult, SignalSpec
from fetchers import SOURCE_REGISTRY
from fetchers.cache import DayCache
from logger import get_logger
from registry import discover

log = get_logger()


def _widget_data(res: SignalResult) -> dict:
    """把 SignalResult 攤平成前端 widget 讀的 widget_data。"""
    wd: dict = {}
    if res.series:
        wd["series"] = list(res.series)
    if res.labels:
        wd["labels"] = list(res.labels)
    if res.rows:
        wd["rows"] = list(res.rows)
    if res.extra:
        wd.update(dict(res.extra))  # extra 的鍵（percent/bands/columns/highlight_index/caption…）攤到頂層
    return wd


def _run_one(spec: SignalSpec, cache: DayCache) -> dict:
    """單一 signal：per-source 抓取隔離 + per-signal compute 隔離 + last-good-stale。"""
    now = datetime.now(config.TAIPEI_TZ).isoformat(timespec="seconds")
    base = {
        "id": spec.id, "name": spec.name, "widget": spec.widget,
        "tags": list(spec.tags), "in_master": spec.in_master, "unit": spec.unit,
        "cadence": spec.cadence, "episode_ref": spec.episode_ref,
        "episode_date": spec.episode_date, "updated_at": now,
        # 三個必答問題（①追什麼 ②怎麼看 ③各燈含義）＋擴充順序——spec 層 metadata，永遠新鮮
        "track": spec.track, "shape": spec.shape, "order": spec.order,
        "interpretations": dict(spec.interpretations),
    }

    inputs: dict = {}
    err: str | None = None
    source_failed = False
    for b in spec.bindings:
        try:
            inputs[b.key] = cache.get_or_fetch(b.source, b.params, SOURCE_REGISTRY[b.source])
        except Exception as exc:  # noqa: BLE001 — per-source 隔離
            source_failed = True
            err = str(exc)
            log.warning("source %s 失敗（%s）：%s", b.source, spec.id, exc)

    try:
        res = spec.compute(inputs) if not source_failed else SignalResult(light="gray")
    except Exception as exc:  # noqa: BLE001 — per-signal 隔離
        res = SignalResult(light="gray")
        err = str(exc)
        log.exception("signal %s compute 失敗", spec.id)

    prev = cache.last_good(spec.id)
    if res.light == "gray" and prev is not None:
        # 來源/運算掛掉但有上一版成功結果 → 沿用舊圖 + stale，而非空灰卡
        card = dict(base)
        card["updated_at"] = prev.get("updated_at", now)  # 顯示資料其實有多舊
        card.update({
            "ok": False, "stale": True, "error": err,
            "light": prev["light"], "value_label": prev.get("value_label", ""),
            "interpretation": prev.get("interpretation", ""),
            "widget_data": prev.get("widget_data", {}), "detail": prev.get("detail", {}),
        })
        return card

    card = dict(base)
    card.update({
        "ok": err is None, "stale": False, "error": err,
        "light": res.light, "value_label": res.value_label,
        "interpretation": spec.interpretations.get(res.light, ""),
        "widget_data": _widget_data(res), "detail": dict(res.detail),
    })
    if res.light != "gray":
        cache.save_last_good(spec.id, card)  # 存這輪成功結果供未來 fallback
    return card


def _atomic_write(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)  # 原子替換，前端不會讀到半截檔


# === 燈號歷史：反轉觀測的主角是「變化」，每天記一格供前端畫燈帶 + 偵測變燈 ===
_COLORED = {"green", "yellow", "red"}


def _history_write_enabled() -> bool:
    """demo 模式不落地歷史檔（避免本機測試污染 CI 維護的真實燈史）；測試可用環境變數強制開。"""
    return (not config.DEMO_MODE) or os.environ.get("GOOAYE_FORCE_HISTORY") == "1"


def _load_history() -> dict:
    try:
        h = json.loads(config.HISTORY_JSON.read_text(encoding="utf-8"))
        if isinstance(h, dict):
            h.setdefault("signals", {})
            h.setdefault("master", [])
            return h
    except (OSError, json.JSONDecodeError):
        pass
    return {"signals": {}, "master": []}


def _upsert(entries: list, today: str, light: str) -> None:
    """同日覆蓋、跨日追加，並裁掉超過保留天數的舊紀錄。"""
    if entries and entries[-1][0] == today:
        entries[-1][1] = light
    else:
        entries.append([today, light])
    del entries[:-config.HISTORY_KEEP_DAYS]


def _prev_light(entries: list, today: str) -> str | None:
    """回傳「今天以前」最近一筆的燈色（同日多輪更新不算變化）。"""
    for d, l in reversed(entries):
        if d != today:
            return l
    return None


def _apply_history(cards: list[dict], top: str, now) -> tuple[list[dict], str | None]:
    """把燈史掛到每張卡（history/prev_light/changed），回傳 (changes, master_prev)。"""
    hist = _load_history()
    today = now.strftime("%Y-%m-%d")
    changes: list[dict] = []

    for card in cards:
        entries = hist["signals"].setdefault(card["id"], [])
        prev = _prev_light(entries, today)
        card["prev_light"] = prev
        card["changed"] = bool(prev and prev != card["light"]
                               and prev in _COLORED and card["light"] in _COLORED)
        if card["changed"]:
            changes.append({"id": card["id"], "name": card["name"],
                            "from": prev, "to": card["light"]})
        _upsert(entries, today, card["light"])
        card["history"] = entries[-config.HISTORY_SHOW_DAYS:]

    master_prev = _prev_light(hist["master"], today)
    if (master_prev and master_prev != top
            and master_prev in _COLORED and top in _COLORED):
        changes.insert(0, {"id": "_master", "name": "總燈號",
                           "from": master_prev, "to": top})
    _upsert(hist["master"], today, top)

    if _history_write_enabled():
        _atomic_write(config.HISTORY_JSON, hist)
    return changes, master_prev


def build_payload() -> tuple[dict, list[dict]]:
    """跑完整條 pipeline，回傳 (payload, cards)。"""
    now = datetime.now(config.TAIPEI_TZ)
    specs = discover()
    cache = DayCache(config.CACHE_DIR, demo=config.DEMO_MODE,
                     fixtures_dir=config.DEMO_FIXTURES_DIR)

    # run-plan：把重疊的 (source, params) 去重，共用資料只抓一次
    seen: set[tuple] = set()
    plan: list[tuple] = []
    for s in specs:
        for b in s.bindings:
            k = (b.source, json.dumps(b.params, sort_keys=True, default=str))
            if k not in seen:
                seen.add(k)
                plan.append((b.source, b.params))
    cache.prefetch(plan, SOURCE_REGISTRY)

    cluster_of = {s.id: s.cluster for s in specs}
    cards = [_run_one(s, cache) for s in specs]

    by_cluster: dict[str, list[dict]] = {}
    for c in cards:
        by_cluster.setdefault(cluster_of[c["id"]], []).append(c)

    clusters_out: list[dict] = []
    top = "gray"
    for cspec in sorted(CLUSTERS, key=lambda c: c.order):
        group = by_cluster.get(cspec.id, [])
        group.sort(key=lambda c: c.get("order", 999))  # 擴充順序（先加的在前），非檔名字母序
        ml, reason, votes = master_light(group)
        if LIGHT_SEVERITY[ml] > LIGHT_SEVERITY[top]:
            top = ml
        clusters_out.append({
            "id": cspec.id, "name": cspec.name, "order": cspec.order,
            "master": {"light": ml, "label": cspec.master_label[ml],
                       "reason": reason, "votes": votes},
            "signals": [c for c in group if c["in_master"]],
            "supporting": [c for c in group if not c["in_master"]],
        })

    top_reason = next((c["master"]["reason"] for c in clusters_out
                       if c["master"]["light"] == top), "")
    errors = [{"signal_id": c["id"], "message": c["error"], "at": c["updated_at"]}
              for c in cards if c.get("error")]

    # 燈號歷史 + 變化偵測（cards 與 clusters_out 共用同一批 dict，掛上去前端就看得到）
    changes, master_prev = _apply_history(cards, top, now)

    payload = {
        "schema_version": config.SCHEMA_VERSION,
        "generated_at": now.isoformat(timespec="seconds"),
        "generated_at_label": now.strftime("%Y/%m/%d %H:%M (台北)"),
        "tz": "Asia/Taipei (UTC+8)",
        "next_update_hint": config.NEXT_UPDATE_HINT,
        "master_light": top,
        "master_prev": master_prev,
        "master_reason": top_reason,
        "changes": changes,
        "clusters": clusters_out,
        "errors": errors,
    }
    return payload, cards


def main() -> int:
    payload, cards = build_payload()

    # 整輪保底：完全沒有任何 ok 卡且已有舊檔 → 不覆蓋，保留上一版
    if not any(c["ok"] for c in cards) and config.SIGNALS_JSON.exists():
        log.error("本輪無任何可用資料，保留上一版 signals.json")
        return 0

    _atomic_write(config.SIGNALS_JSON, payload)
    if config.WEB_DIR.exists():
        _atomic_write(config.WEB_DATA_JSON, payload)  # 給前端 same-origin 讀

    log.info("signals.json 已寫出：%d clusters, %d errors, master=%s",
             len(payload["clusters"]), len(payload["errors"]), payload["master_light"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
