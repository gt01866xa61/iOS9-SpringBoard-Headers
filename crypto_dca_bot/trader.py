"""BinanceTrader: spot market buy with multi-layer safety nets (Phase 3).

Inherits BinanceExchange (Phase 2) for ccxt client, _call error wrapper,
and notify plumbing. Adds order placement, symbol whitelist, single-buy
+ daily cap, persistent daily state.

Pre-API safety order (steps 1-6 raise ValueError before hitting Binance):
  1. symbol in SYMBOL_WHITELIST
  2. quote_amount in [effective_min, MAX_SINGLE_BUY_USDT]
  3. load daily_state.json
  4. cross-day reset (Asia/Taipei)
  5. daily cap check
  6. USDT balance >= quote_amount * BALANCE_SAFETY_MULTIPLIER
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional, TypeVar

import ccxt

from exchange_api import BinanceExchange
from notifier import get_notifier

SYMBOL_WHITELIST: frozenset[str] = frozenset({"BTC/USDT", "ETH/USDT"})
try:
    from config import DAILY_CAP_USDT
except ImportError as exc:
    raise RuntimeError(
        f"trader.py failed to import DAILY_CAP_USDT from config.py: {exc}. "
        f"Refusing to start with stale 50.0 fallback — a syntax error in "
        f"config.py would otherwise silently use Phase 3's 50 USDT cap."
    ) from exc
MAX_SINGLE_BUY_USDT: float = 25.0
MIN_SINGLE_BUY_USDT: float = 5.0
BALANCE_SAFETY_MULTIPLIER: float = 1.01
STATE_FILE: Path = Path(__file__).resolve().parent / "state" / "daily_state.json"

# Fixed UTC+8 (matches logger._TAIPEI). Asia/Taipei has no DST since 1979,
# so a fixed offset is functionally identical to ZoneInfo("Asia/Taipei")
# without requiring the tzdata package on Windows (Python 3.9+ on Windows
# ships zoneinfo but no IANA database).
TAIPEI_TZ = timezone(timedelta(hours=8), name="Asia/Taipei")

_RATE_LIMIT_RETRY_SLEEP_S = 2.0

T = TypeVar("T")


class BinanceTrader(BinanceExchange):
    """Spot market buy with multi-layer safety nets."""

    def place_market_buy(
        self,
        symbol: str,
        quote_amount_usdt: float,
    ) -> Optional[dict]:
        """Place a market buy spending `quote_amount_usdt` USDT on `symbol`.

        Returns the ccxt order dict on success, None on safety-check failure
        (after step 7) or exchange error. Re-raises AuthenticationError /
        PermissionDenied. Raises ValueError for any pre-API safety violation.
        """
        # [1] symbol whitelist
        if symbol not in SYMBOL_WHITELIST:
            raise ValueError(
                f"symbol not in whitelist: {symbol!r} "
                f"(allowed: {sorted(SYMBOL_WHITELIST)})"
            )

        # [2] amount range (with dynamic min notional)
        effective_min = max(MIN_SINGLE_BUY_USDT, self._get_min_notional(symbol))
        if not (effective_min <= quote_amount_usdt <= MAX_SINGLE_BUY_USDT):
            raise ValueError(
                f"quote_amount {quote_amount_usdt:.2f} not in "
                f"[{effective_min:.2f}, {MAX_SINGLE_BUY_USDT:.2f}]"
            )

        # [3-5] daily cap (raises ValueError if exceeded)
        state = self._check_daily_cap(quote_amount_usdt)

        # [6] USDT balance + safety buffer
        free = self.get_balance("USDT")
        required = quote_amount_usdt * BALANCE_SAFETY_MULTIPLIER
        if free is None:
            raise ValueError("balance fetch returned None; aborting buy")
        if free < required:
            raise ValueError(
                f"insufficient USDT: free={free:.4f}, required={required:.4f} "
                f"(quote_amount * {BALANCE_SAFETY_MULTIPLIER})"
            )

        # [7] pre-trade audit (Telegram failure does not abort — see plan)
        self._log.info("Pre-trade: %.4f USDT on %s", quote_amount_usdt, symbol)
        try:
            sent = get_notifier().send(
                f"📤 準備下單 {quote_amount_usdt:.2f} USDT 買 {symbol}",
                level="INFO",
            )
            if not sent:
                self._log.warning(
                    "pre-trade Telegram returned False; continuing to place order"
                )
        except Exception as exc:  # noqa: BLE001
            self._log.warning("pre-trade Telegram raised; continuing: %s", exc)

        # [8] place market order via raw quoteOrderQty
        label = f"place_market_buy {symbol} {quote_amount_usdt:.4f} USDT"
        order = self._call(
            label,
            lambda: self._client.create_order(
                symbol=symbol,
                type="market",
                side="buy",
                amount=None,
                params={"quoteOrderQty": quote_amount_usdt},
            ),
        )
        if order is None:
            return None

        # [9-10] parse + atomically commit state with actual cost
        actual_cost = self._extract_actual_cost(order, quote_amount_usdt)
        self._commit_daily_state(state, actual_cost)

        # [11] post-trade notify
        filled = float(order.get("filled") or 0)
        average = order.get("average")
        avg_str = f"{float(average):,.2f}" if average else "?"
        base = symbol.split("/")[0]
        self._log.info(
            "Order filled: cost=%.4f USDT, filled=%s %s, avg=%s, id=%s",
            actual_cost, filled, base, avg_str, order.get("id"),
        )
        try:
            get_notifier().send(
                f"✅ 成交 {actual_cost:.4f} USDT → {filled:.8f} {base} @ {avg_str}",
                level="INFO",
            )
        except Exception as exc:  # noqa: BLE001
            self._log.warning("post-trade Telegram raised: %s", exc)

        return order

    def _get_min_notional(self, symbol: str) -> float:
        """Read MIN_NOTIONAL filter from Binance market info, fallback 5.0.

        ccxt's `client.market(symbol)` is a local lookup that requires
        markets to be loaded — `load_markets()` does NOT happen automatically
        here (only `fetch_ticker` / `fetch_balance` etc. trigger it
        internally). Route the load through `self._call` so AuthenticationError
        / PermissionDenied propagate fail-loud while transient errors
        (NetworkError / ExchangeError) fall back to 5.0 via the markets-
        still-empty path.

        Narrow data-shape catch: KeyError / TypeError / AttributeError /
        ValueError. ccxt errors at `market()` are unexpected once markets
        are loaded; if they occur, propagate.
        """
        if not self._client.markets:
            self._call("load_markets", lambda: self._client.load_markets())
        if not self._client.markets:
            self._log.warning(
                "markets not loaded for %s; fallback to 5.0", symbol,
            )
            return 5.0
        try:
            market = self._client.market(symbol)
            min_cost = market.get("limits", {}).get("cost", {}).get("min")
            return float(min_cost) if min_cost else 5.0
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            self._log.warning(
                "min_notional lookup degraded for %s, fallback to 5.0: %s",
                symbol, exc,
            )
            return 5.0

    def _today_taipei(self) -> str:
        return datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")

    def _load_daily_state(self) -> dict:
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {"date": self._today_taipei(), "spent_usdt": 0.0}

    def _check_daily_cap(self, quote_amount: float) -> dict:
        """Read-only check; returns today's state for later commit.
        Raises ValueError without writing the file — failed orders should
        not consume today's quota.
        """
        state = self._load_daily_state()
        today = self._today_taipei()
        if state.get("date") != today:
            state = {"date": today, "spent_usdt": 0.0}
        spent = float(state.get("spent_usdt") or 0.0)
        state["spent_usdt"] = spent
        if spent + quote_amount > DAILY_CAP_USDT:
            raise ValueError(
                f"daily cap exceeded: today spent {spent:.2f}, "
                f"cap {DAILY_CAP_USDT:.2f}, this order {quote_amount:.2f}"
            )
        return state

    def _commit_daily_state(self, state: dict, actual_cost: float) -> None:
        """Atomic write: tmp file + os.replace. Crash-safe — partial writes
        cannot corrupt the existing state file."""
        state["spent_usdt"] = round(float(state["spent_usdt"]) + actual_cost, 8)
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        tmp.replace(STATE_FILE)

    def _extract_actual_cost(self, order: dict, requested: float) -> float:
        """Safely extract spent USDT from a ccxt order dict.

        Binance market buy responses are inconsistent — `cost` may be None/0
        for instant fills. Falls back to summing trades, then to requested.
        Without this guard, `_commit_daily_state` would crash on `None +`,
        leaving the order placed but the daily counter unupdated.
        """
        cost = order.get("cost")
        if cost is not None and float(cost) > 0:
            return float(cost)
        fills = order.get("trades") or order.get("fills") or []
        if fills:
            total = 0.0
            for f in fills:
                f_cost = f.get("cost")
                if f_cost is not None and float(f_cost) > 0:
                    total += float(f_cost)
                    continue
                price = float(f.get("price") or 0)
                amount = float(f.get("amount") or f.get("qty") or 0)
                total += price * amount
            if total > 0:
                return total
        self._log.warning(
            "order cost missing/zero, fallback to requested %.4f USDT (id=%s)",
            requested, order.get("id"),
        )
        return requested

    def _call(self, label: str, fn: Callable[[], T]) -> Optional[T]:
        """Trader error matrix: prepend InsufficientFunds + InvalidOrder
        ahead of the general ExchangeError catch. All other classes match
        BinanceExchange._call exactly so retry/raise/notify behavior stays
        consistent for read-only paths inherited via super().get_balance() etc.
        """
        try:
            return fn()
        except ccxt.AuthenticationError as exc:
            self._log.error("%s: AuthenticationError: %s", label, exc)
            self._notify(f"❌ Auth 失敗 ({label}): API key 錯誤")
            raise
        except ccxt.PermissionDenied as exc:
            self._log.error("%s: PermissionDenied: %s", label, exc)
            self._notify(
                f"❌ 權限被拒 ({label}) — 檢查 IP 白名單或 API key 權限設定"
            )
            raise
        except ccxt.RateLimitExceeded:
            self._log.warning(
                "%s: RateLimitExceeded, sleep %.1fs and retry once",
                label, _RATE_LIMIT_RETRY_SLEEP_S,
            )
            time.sleep(_RATE_LIMIT_RETRY_SLEEP_S)
            try:
                return fn()
            except ccxt.ExchangeError as exc:
                self._log.error("%s: still failed after retry: %s", label, exc)
                self._notify(f"❌ {label} 限流後仍失敗")
                return None
        except ccxt.InsufficientFunds as exc:
            self._log.error("%s: InsufficientFunds: %s", label, exc)
            self._notify(f"❌ 餘額不足 ({label}): {exc}")
            return None
        except ccxt.InvalidOrder as exc:
            self._log.error("%s: InvalidOrder: %s", label, exc)
            self._notify(f"❌ 下單規則違規 ({label}): {exc}")
            return None
        except ccxt.BadSymbol as exc:
            self._log.error("%s: BadSymbol: %s", label, exc)
            return None
        except ccxt.NetworkError as exc:
            self._log.error("%s: NetworkError: %s", label, exc)
            self._notify(f"⚠️ 網路錯誤 ({label}): {exc}")
            return None
        except ccxt.ExchangeError as exc:
            self._log.error("%s: ExchangeError: %s", label, exc)
            self._notify(f"❌ 交易所錯誤 ({label}): {exc}")
            return None
