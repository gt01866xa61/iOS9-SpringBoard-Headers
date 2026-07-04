"""Phase 1 驗證：契約 + registry 完整性。

跑法（在 gooaye_signals/ 目錄下）：
    python tests/test_phase1_specs.py

驗證：registry 探索無誤、id==檔名且唯一、interpretations 四鍵齊、每 binding.source
存在於 SOURCE_REGISTRY、cluster 合法、widget/cadence 合法、episode_date 格式正確、
master_light 真值表、時間戳為台北 +08:00。
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime

# 讓 core / registry / signals / fetchers 可以被 import（把 gooaye_signals/ 放進 path）
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import config
from core.clusters import CLUSTER_IDS, master_light
from core.spec import (
    CADENCE_NAMES,
    REQUIRED_LIGHTS,
    SignalSpec,
    WIDGET_NAMES,
)
from fetchers import SOURCE_REGISTRY
from registry import discover

EXPECTED_IDS = {"yageo_rev_yoy", "mlcc_basket_ma", "ai_breadth"}


def _check_specs() -> None:
    specs = discover()
    ids = [s.id for s in specs]

    assert len(ids) == len(set(ids)), f"signal id 重複：{ids}"
    assert EXPECTED_IDS.issubset(set(ids)), f"缺少種子訊號，實得 {ids}"

    for s in specs:
        assert isinstance(s, SignalSpec), f"{s} 不是 SignalSpec"
        # id == 檔名 由 registry 保證；這裡再驗其他契約
        assert s.name, f"{s.id} 缺 name"
        assert s.cluster in CLUSTER_IDS, f"{s.id} cluster '{s.cluster}' 不存在"
        assert s.widget in WIDGET_NAMES, f"{s.id} widget '{s.widget}' 非法"
        assert s.cadence in CADENCE_NAMES, f"{s.id} cadence '{s.cadence}' 非法"
        assert s.bindings, f"{s.id} 至少要有一個 binding"
        for b in s.bindings:
            assert b.source in SOURCE_REGISTRY, f"{s.id} binding source '{b.source}' 未註冊"
            assert b.key, f"{s.id} binding 缺 key"
        for lt in REQUIRED_LIGHTS:
            assert lt in s.interpretations, f"{s.id} interpretations 缺 '{lt}'"
            assert s.interpretations[lt], f"{s.id} interpretations['{lt}'] 為空"
        # 三個必答問題：①追什麼 ②怎麼看，＋擴充順序
        assert s.track, f"{s.id} 缺 track（追什麼）"
        assert s.shape, f"{s.id} 缺 shape（怎麼看）"
        assert isinstance(s.order, int), f"{s.id} order 需為 int"
        # episode_date 需可解析（"?" 只允許在 episode_ref）
        datetime.strptime(s.episode_date, "%Y-%m-%d")

    print(f"  ✓ registry 探索 {len(specs)} 個訊號，契約全數通過")


def _check_master_light() -> None:
    def card(light: str, in_master: bool = True) -> dict:
        return {"light": light, "in_master": in_master}

    # >=2 紅 → 紅
    lt, _, votes = master_light([card("red"), card("red"), card("green")])
    assert lt == "red", (lt, votes)
    # 1 紅 → 黃
    lt, _, _ = master_light([card("red"), card("green"), card("green")])
    assert lt == "yellow", lt
    # 1 黃 → 黃
    lt, _, _ = master_light([card("yellow"), card("green")])
    assert lt == "yellow", lt
    # 全綠 → 綠
    lt, _, _ = master_light([card("green"), card("green")])
    assert lt == "green", lt
    # 空 → gray
    lt, _, _ = master_light([])
    assert lt == "gray", lt
    # 只有 gray → gray
    lt, _, _ = master_light([card("gray"), card("gray")])
    assert lt == "gray", lt
    # 非 in_master 的紅不計入（→ 綠）
    lt, _, _ = master_light([card("red", in_master=False), card("green")])
    assert lt == "green", lt

    print("  ✓ master_light 真值表通過")


def _check_timezone() -> None:
    stamp = datetime.now(config.TAIPEI_TZ).isoformat(timespec="seconds")
    assert stamp.endswith("+08:00"), f"時間戳非台北時區：{stamp}"
    print(f"  ✓ 時間戳為台北時區：{stamp}")


def main() -> int:
    print("Phase 1 驗證中…")
    _check_specs()
    _check_master_light()
    _check_timezone()
    print("Phase 1 驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
