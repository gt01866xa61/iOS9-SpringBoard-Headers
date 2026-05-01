"""Binance market data + balance via ccxt (Phase 2: read-only).

Public price queries work without API keys. Balance queries need
BINANCE_API_KEY / BINANCE_API_SECRET in .env (Reading permission only,
IP-whitelisted). Phase 3 will reuse this client for order placement.
"""
from __future__ import annotations

import os
import time
from typing import Callable, Optional, TypeVar

import ccxt

from logger import get_logger
from notifier import get_notifier

_DEFAULT_TIMEOUT_MS = 10_000
_RATE_LIMIT_RETRY_SLEEP_S = 2.0

T = TypeVar("T")


class BinanceExchange:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout_ms: int = _DEFAULT_TIMEOUT_MS,
        notify_on_error: bool = True,
    ) -> None:
        self._log = get_logger("dca_bot.exchange")
        self._notify_on_error = notify_on_error

        api_key = api_key or os.environ.get("BINANCE_API_KEY") or None
        api_secret = api_secret or os.environ.get("BINANCE_API_SECRET") or None
        self._has_keys = bool(api_key and api_secret)

        self._client = ccxt.binance({
            "enableRateLimit": True,
            "timeout": timeout_ms,
            "apiKey": api_key,
            "secret": api_secret,
            "options": {
                "defaultType": "spot",
                "adjustForTimeDifference": True,
                "createMarketBuyOrderRequiresPrice": False,
            },
        })

    def get_price(self, symbol: str) -> Optional[float]:
        ticker = self._call(
            f"fetch_ticker {symbol}",
            lambda: self._client.fetch_ticker(symbol),
        )
        if ticker is None:
            return None
        last = ticker.get("last")
        if last is None:
            self._log.error("%s: ticker missing 'last' field", symbol)
            return None
        price = float(last)
        self._log.info("Price %s = %s", symbol, price)
        return price

    def get_balance(self, asset: str = "USDT") -> Optional[float]:
        if not self._has_keys:
            raise RuntimeError(
                "BINANCE_API_KEY / BINANCE_API_SECRET must be set for "
                "get_balance() (see .env.example)."
            )
        balances = self._call("fetch_balance", lambda: self._client.fetch_balance())
        if balances is None:
            return None
        free = balances.get(asset, {}).get("free", 0.0)
        free = float(free)
        self._log.info("Balance %s free = %s", asset, free)
        return free

    def _call(self, label: str, fn: Callable[[], T]) -> Optional[T]:
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
            self._log.warning("%s: RateLimitExceeded, sleep %.1fs and retry once",
                              label, _RATE_LIMIT_RETRY_SLEEP_S)
            time.sleep(_RATE_LIMIT_RETRY_SLEEP_S)
            try:
                return fn()
            except ccxt.ExchangeError as exc:
                self._log.error("%s: still failed after retry: %s", label, exc)
                self._notify(f"❌ {label} 限流後仍失敗")
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

    def _notify(self, message: str) -> None:
        if not self._notify_on_error:
            return
        try:
            get_notifier().send(message, level="ERROR")
        except Exception as exc:  # noqa: BLE001
            self._log.error("Notifier failed during error reporting: %s", exc)
