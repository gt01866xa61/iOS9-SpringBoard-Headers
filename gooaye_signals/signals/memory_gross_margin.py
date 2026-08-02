"""支援面板 — 記憶體毛利率變化（財報確認器，不計主燈）。

追什麼：記憶體是高固定成本產業，價格轉弱時毛利率常比營收更早鬆動。本卡先採
        美光同一 GAAP 合併口徑作為可連續追蹤的代理，不把它誤稱成整個產業的平均。
長相　：季毛利率折線；重點是最新一季相對上一季的百分點（pp）變化，不是絕對高低。
狀態　：綠＝仍擴張；黃＝持平或首度鬆動；紅＝單季大幅下滑或連兩季鬆動。
資料　：data/manual/memory_gross_margin.json——美光季度正式新聞稿，財報後手動補點。
"""
from __future__ import annotations

from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數（毛利率的「鬆動」以 QoQ 百分點而非金額判斷）===
SOFTEN_PP = 1.0
SHARP_DROP_PP = 5.0


def _source(point: dict) -> dict:
    out = {"source": str(point.get("src") or "")}
    url = str(point.get("src_url") or "")
    if url.startswith(("https://", "http://")):
        out["source_url"] = url
    return out


def _compute(inputs: dict) -> SignalResult:
    data = inputs.get("margin") or {}
    entries = sorted(list(data.get("series") or []), key=lambda point: str(point.get("date") or ""))
    if not entries:
        return SignalResult(light="gray")

    series = [float(point["gross_margin_pct"]) for point in entries]
    labels = [str(point["label"]) for point in entries]
    latest = entries[-1]
    latest_pct = series[-1]
    caption = ("美光 GAAP 合併毛利率，僅作同口徑記憶體代理，非產業平均；"
               f"門檻：QoQ 下降 ≥{SOFTEN_PP:.0f}pp＝鬆動，"
               f"下降 ≥{SHARP_DROP_PP:.0f}pp 或連兩季鬆動＝紅。")

    if len(entries) < 2:
        return SignalResult(
            light="gray", value_label=f"{latest_pct:.1f}%（待下一季比較）",
            series=series, labels=labels, extra={"caption": caption},
            detail={"as_of": str(data.get("as_of") or ""), "points": len(entries)},
            data_as_of=str(latest.get("date") or data.get("as_of") or ""),
            sources=tuple(_source(point) for point in entries),
        )

    delta_pp = latest_pct - series[-2]
    prior_delta_pp = series[-2] - series[-3] if len(entries) >= 3 else None
    if delta_pp <= -SHARP_DROP_PP or (
            prior_delta_pp is not None and prior_delta_pp <= -SOFTEN_PP and delta_pp <= -SOFTEN_PP):
        light = "red"
    elif delta_pp <= -SOFTEN_PP:
        light = "yellow"
    elif delta_pp >= SOFTEN_PP:
        light = "green"
    else:
        light = "yellow"

    return SignalResult(
        light=light,
        value_label=f"{latest_pct:.1f}%（{delta_pp:+.1f}pp QoQ）",
        series=series, labels=labels, extra={"caption": caption},
        detail={"qoq_pp": round(delta_pp, 2), "prior_qoq_pp": prior_delta_pp,
                "as_of": str(data.get("as_of") or "")},
        data_as_of=str(latest.get("date") or data.get("as_of") or ""),
        sources=tuple(_source(point) for point in entries),
    )


SIGNAL = SignalSpec(
    id="memory_gross_margin",
    name="記憶體毛利率變化",
    cluster="semi_memory_top",
    tags=("記憶體", "毛利率", "美光", "財報"),
    widget="sparkline",
    bindings=(
        DataBinding(key="margin", source="manual_series", params={"key": "memory_gross_margin"}),
    ),
    compute=_compute,
    interpretations={
        "green": "同口徑毛利率仍在擴張，尚未出現本卡定義的鬆動。",
        "yellow": "毛利率持平或首度鬆動；高固定成本下，留意後續財報是否延續。",
        "red": "毛利率單季大幅下滑或連兩季鬆動；這是代理序列的早期轉折警示。",
        "gray": "尚不足兩個同口徑季度，先建立可比較的基準。",
    },
    cadence="manual",
    track="記憶體業高固定成本下的財報毛利率變化。先用美光 GAAP 合併口徑作為可連續追蹤的代理；它不是整個產業的平均，也不代替其他記憶體廠。",
    shape="看最新一季比上一季的 pp 變化：續升＝綠；下降至少 1pp＝黃；單季降至少 5pp、或連兩季各降至少 1pp＝紅。重點是「開始鬆動」，不是毛利率絕對值高不高。",
    order=7,
    in_master=False,
    unit="%",
)
