"""資料源註冊表：source 名稱 -> fetcher 函式。

fetcher 介面（live 模式）：fn(params: Mapping[str, object]) -> object
demo 模式由 DayCache 攔截、改讀 demo/fixtures，不會呼叫這些 fetcher。

Phase 1 先放 stub（呼叫即 raise NotImplementedError），讓 registry 完整性測試能驗證
每個 signal 宣告的 binding.source 都存在。真正的抓取實作在 Phase 3 由 finmind.py /
yfinance_src.py 覆寫進 SOURCE_REGISTRY。
"""
from __future__ import annotations

from typing import Callable, Mapping


def _stub(name: str) -> Callable[[Mapping[str, object]], object]:
    def _f(params: Mapping[str, object]) -> object:
        raise NotImplementedError(f"fetcher '{name}' 尚未接上（Phase 3 實作）")

    return _f


# source 名稱 -> fetcher。Phase 3 會把 stub 換成真的抓取函式。
# 價格類全部走 yf_close（yfinance 支援 .TW/.TWO/.KS/US/期貨），FinMind 只負責月營收。
SOURCE_REGISTRY: dict[str, Callable[[Mapping[str, object]], object]] = {
    "finmind_revenue": _stub("finmind_revenue"),  # TW 月營收（回傳已換算 YoY）
    "yf_close": _stub("yf_close"),                # TW/美/韓股 + 金屬收盤序列
    "fred": _stub("fred"),                        # 選配：總經序列
}
