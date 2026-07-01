"""資料源註冊表：source 名稱 -> fetcher 函式。

fetcher 介面（live 模式）：fn(params: Mapping[str, object]) -> object
demo 模式由 DayCache 攔截、改讀 demo/fixtures，不會呼叫這些 fetcher。

價格類全部走 yf_close（yfinance 支援 .TW/.TWO/.KS/US/期貨），FinMind 只負責月營收。
真正的抓取實作用 lazy import（呼叫時才 import yfinance/FinMind），所以 demo/測試環境
不需安裝那些套件也能跑。
"""
from __future__ import annotations

from typing import Callable, Mapping

from fetchers.finmind import fetch_revenue
from fetchers.yfinance_src import fetch_close


def _stub(name: str) -> Callable[[Mapping[str, object]], object]:
    def _f(params: Mapping[str, object]) -> object:
        raise NotImplementedError(f"fetcher '{name}' 尚未接上")

    return _f


# source 名稱 -> fetcher
SOURCE_REGISTRY: dict[str, Callable[[Mapping[str, object]], object]] = {
    "finmind_revenue": fetch_revenue,   # TW 月營收（回傳已換算 YoY）
    "yf_close": fetch_close,            # TW/美/韓股 + 金屬收盤序列
    "fred": _stub("fred"),              # 選配：總經序列（未接）
}
