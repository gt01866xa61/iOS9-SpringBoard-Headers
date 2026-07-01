"""Signal 宣告用的核心型別。所有 signals/*.py 都用這裡的 frozen dataclass 宣告。

設計鐵律：compute 是純函式 (inputs -> SignalResult)，不抓網路、不看時鐘、不寫檔。
資料由 DataBinding 宣告、builder 負責抓取並批次去重後餵進來。時鐘鎖死 Asia/Taipei。

新增一個訊號 = 在 signals/ 放一個檔、export 一個 SIGNAL: SignalSpec。放進去就是註冊。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Mapping, Sequence, get_args

# === 燈號（順序即嚴重度；gray 不計入 master 投票）===
Light = Literal["green", "yellow", "red", "gray"]
LIGHT_SEVERITY: dict[str, int] = {"gray": -1, "green": 0, "yellow": 1, "red": 2}

# === Widget 型別 = 前端 dispatch key。只有「新增一種顯示」才需要動前端 ===
Widget = Literal["light_card", "bar_chart", "gauge", "sparkline", "table"]

# === 更新節奏 ===
Cadence = Literal["daily", "trading_day", "monthly", "manual"]

# 供驗證／測試使用的 runtime 清單
LIGHT_NAMES: tuple[str, ...] = get_args(Light)
WIDGET_NAMES: tuple[str, ...] = get_args(Widget)
CADENCE_NAMES: tuple[str, ...] = get_args(Cadence)
# 每個訊號的 interpretations 必須涵蓋這四個燈號
REQUIRED_LIGHTS: tuple[str, ...] = ("green", "yellow", "red", "gray")


@dataclass(frozen=True)
class DataBinding:
    """宣告一次資料抓取。key = compute inputs 的鍵；builder 依此批次抓取並去重。"""

    key: str                                   # compute 讀 inputs[key]
    source: str                                # 對應 fetchers.SOURCE_REGISTRY 的鍵
    params: Mapping[str, object] = field(default_factory=dict)  # {"stock_id": "2327"} 等


@dataclass(frozen=True)
class SignalResult:
    """compute 的輸出。widget 只讀它需要的欄位；builder 直接轉成 signals.json 的卡片。"""

    light: Light
    value_label: str = ""                      # 卡片主數字，如 "-3.1%" / "33%"
    series: Sequence[float] = ()               # bar_chart / sparkline 的數列
    labels: Sequence[str] = ()                 # 與 series 對齊的 x 軸標籤
    rows: Sequence[dict] = ()                  # table widget 的列
    extra: Mapping[str, object] = field(default_factory=dict)   # widget 專屬（highlight_index、bands…）
    detail: Mapping[str, object] = field(default_factory=dict)  # debug／佐證數字


@dataclass(frozen=True)
class SignalSpec:
    """一個訊號的完整宣告。metadata 全都是「白話自我說明」的一等公民欄位。"""

    id: str                                    # 全域唯一，必須 == 檔名
    name: str                                  # 中文顯示名（回答：追什麼訊號）
    cluster: str                               # 所屬 cluster id（見 core/clusters.py）
    tags: tuple[str, ...]                       # 分類標籤
    widget: Widget                             # 顯示型態（回答：變化的長相）
    bindings: tuple[DataBinding, ...]          # 需要哪些資料
    compute: Callable[[dict], SignalResult]    # 純函式 inputs -> SignalResult
    interpretations: Mapping[Light, str]       # 四個燈號各一句白話（回答：狀態含義）
    episode_ref: str                           # 提及來源，如 "EP512"，記不清可填 "?"
    episode_date: str                          # 對應日期 "YYYY-MM-DD"（台北）
    cadence: Cadence                           # 更新節奏
    in_master: bool = True                     # 是否計入所屬 cluster 的主燈投票
    unit: str = ""                             # 主數字單位
