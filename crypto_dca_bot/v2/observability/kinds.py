"""Event kind catalog(防拼錯 + schema 文件)。

集中常數,程式碼鼓勵但不強制使用(sink.log() 仍接任意 kind,給未來
新增類型留空間)。
"""

REGISTERED = "registered"
IS_READY = "is_ready"
SKIPPED_STALE = "skipped_stale"
ON_STALE_HOOK_ERROR = "on_stale_hook_error"
STRATEGY_CRASHED = "strategy_crashed"
ALERT = "alert"
PIPELINE = "pipeline"
ORDER_REJECTED = "order_rejected"
FILL = "fill"

ALL_KNOWN_KINDS = frozenset(
    {
        REGISTERED,
        IS_READY,
        SKIPPED_STALE,
        ON_STALE_HOOK_ERROR,
        STRATEGY_CRASHED,
        ALERT,
        PIPELINE,
        ORDER_REJECTED,
        FILL,
    }
)
