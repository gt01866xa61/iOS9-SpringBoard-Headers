"""Cluster（主題叢集）元資料 + 主燈規則。

加一個新主題（利率總經／航運／情緒／個股…）= 在 CLUSTERS append 一個 ClusterSpec。
master 規則是純 Python 真值表，可單測，不用字串 DSL。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClusterSpec:
    id: str
    name: str                      # "半導體 / 記憶體循環見頂觀察"
    master_label: dict[str, str]   # 每個燈號的主燈標語
    order: int                     # 顯示順序（小的在前）


CLUSTERS: tuple[ClusterSpec, ...] = (
    ClusterSpec(
        id="semi_memory_top",
        name="半導體 / 記憶體循環見頂觀察",
        master_label={
            "red": "主升段尾聲警示",
            "yellow": "留意轉弱",
            "green": "循環結構健康",
            "gray": "資料不足",
        },
        order=1,
    ),
    ClusterSpec(
        id="leadframe_osat",
        name="導線架 / 封測供應鏈觀察",
        master_label={
            "red": "上游動能反轉警示",
            # 黃可能是「分歧」（一綠一黃）也可能是「同步鈍化」（兩黃），措辭要涵蓋兩者
            "yellow": "動能鈍化或分歧",
            "green": "上游缺貨動能延續",
            "gray": "資料不足",
        },
        order=2,
    ),
    ClusterSpec(
        id="onprem_hybrid",
        name="地端 / 混合雲 AI 觀察",
        master_label={
            "red": "劇本反向",
            "yellow": "未驗證，維持假設",   # 預設狀態：沒看到大量拉貨前，先假設吃力不討好
            "green": "劇本點火",
            "gray": "資料不足",
        },
        order=3,
    ),
    # 未來 cluster 直接在這裡 append 一列，例如：
    # ClusterSpec(id="rates_macro", name="利率 / 總經觀察",
    #             master_label={...}, order=4),
)

CLUSTER_IDS: frozenset[str] = frozenset(c.id for c in CLUSTERS)


def get_cluster(cluster_id: str) -> ClusterSpec:
    for c in CLUSTERS:
        if c.id == cluster_id:
            return c
    raise KeyError(f"未知 cluster: {cluster_id}")


def master_light(cards: list[dict]) -> tuple[str, str, dict]:
    """只數 in_master=True 的卡。>=2 紅→紅；任一紅/黃→黃；全綠→綠；否則 gray。

    純 Python truth table，可單測。回傳 (light, reason, votes)。
    cards 為卡片 dict 清單，每個至少有 "light" 與 "in_master"。
    """
    lit = [c["light"] for c in cards if c.get("in_master")]
    votes = {k: lit.count(k) for k in ("red", "yellow", "green", "gray")}

    # reason 用主題中性的措辭——同一張真值表服務所有 cluster，主題味由各
    # cluster 的 master_label 提供（多 cluster 後不能再寫死單一主題的語彙）
    if votes["red"] >= 2:
        light, reason = "red", f"{votes['red']} 項主燈訊號亮紅，警訊成立。"
    elif votes["red"] or votes["yellow"]:
        light, reason = "yellow", "部分主燈訊號轉弱或分歧，留意。"
    elif lit and all(x == "green" for x in lit):
        light, reason = "green", "計入主燈的訊號全綠。"
    else:
        light, reason = "gray", "主燈訊號資料不足。"

    return light, reason, votes
