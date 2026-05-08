# Crypto Smart DCA Bot

A 24/7 crypto DCA + holdings-monitor bot.
Exchange: **Binance** (via `ccxt`). Notifications: **Telegram Bot**.

## Phase progress

| Phase | Scope | Status |
| ----- | ----- | ------ |
| 1 | Logger + Telegram notifier bootstrap | ✅ Done |
| 2 | `exchange_api.py` — ccxt price + balance (read-only) | ✅ Done |
| 3 | `trader.py` — market buy with multi-layer safety + daily cap | ✅ Done |
| 4 | `main.py` — schedule loop + circuit breaker + heartbeat + dry-run | ✅ Validated |

## Phase 1 setup

```bash
cd crypto_dca_bot
cp .env.example .env
# Edit .env and fill:
#   TELEGRAM_BOT_TOKEN=<from @BotFather>
#   TELEGRAM_CHAT_ID=<your chat id>
pip install -r requirements.txt
python test_phase1.py
```

### Getting `TELEGRAM_CHAT_ID`

1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token.
2. Send any message to your new bot.
3. `curl "https://api.telegram.org/bot<TOKEN>/getUpdates"` and read the
   `result[].message.chat.id` field.

### Expected result

- Terminal prints `Phase 1 驗證通過`.
- `crypto_dca_bot/bot.log` contains INFO / WARNING / ERROR entries with
  timestamps.
- Your Telegram chat receives a message starting with `[INFO] ...` that says
  `Bot 初始化成功 ✅`.

## Phase 2 setup

### 1. Create a Binance.com API key (read-only)

User Center → API Management → Create API → name it (e.g. `dca_bot_phase2_readonly`)
→ complete 2FA → permission page.

**Tick only this**:
- ✅ **Enable Reading**

**Never tick** (defense in depth — Phase 2 needs none of these):
- ❌ Enable Spot & Margin Trading (Phase 3 only)
- ❌ Enable Futures
- ❌ Enable Withdrawals (do not enable, ever)
- ❌ Permits Universal Transfer
- ❌ Enable Internal Transfer

### 2. Bind IP whitelist (mandatory)

API key edit page → `Restrict access to trusted IPs only` → must be set.

Find your machine's outbound IP:
```powershell
# Windows PowerShell
Invoke-RestMethod ifconfig.me
```

```bash
# macOS / Linux
curl ifconfig.me
```

Multiple IPs are supported (comma-separated). Add Mac mini's IP later when
you deploy. **Without IP whitelist, a leaked key lets anyone read your
balance from anywhere in the world.**

### 3. Fill `.env`

Open `crypto_dca_bot/.env` and append (or replace placeholders):
```
BINANCE_API_KEY=<from step 1>
BINANCE_API_SECRET=<from step 1, only shown once>
```

`.env` is gitignored. The secret is only displayed once at API creation —
if you didn't copy it, recreate the key.

### 4. Run Phase 2 validation

```bash
python test_phase2.py
```

#### Expected result

- Terminal prints `Phase 2 驗證通過`.
- `crypto_dca_bot/bot.log` contains:
  - `Price BTC/USDT = ...`
  - `Price ETH/USDT = ...`
  - `Balance USDT free = ...` (and BTC, ETH)
- Telegram receives `Phase 2 行情 + 持倉快照` with current prices and balances.

#### Run chaos tests

```bash
python chaos_test.py
```

Expected: **6 passed, 0 failed, 1 skipped (total 7)**. The skipped one is
`[7/7] Wrong IP whitelist` — a semi-manual test (see below). Telegram
receives **no messages** during chaos (all tests use `notify_on_error=False`).

### Wrong-IP semi-manual test flow `[7/7]`

This verifies that an IP-whitelisted key correctly raises
`ccxt.AuthenticationError` when called from a non-whitelisted IP. It must
be done by hand because it requires temporarily breaking the whitelist.

> Empirical note: Binance returns error code `-2015` ("Invalid API-key, IP,
> or permissions for action") for IP whitelist violations, which `ccxt`
> maps to `AuthenticationError` (not `PermissionDenied`). Both classes are
> handled identically in `exchange_api._call` (log + notify + raise), so
> the production safety net is unaffected.

1. Go to Binance → API Management → edit your `dca_bot_phase2_readonly` key.
2. **Change the IP whitelist to a fake IP** (e.g. `1.2.3.4`). Save.
3. Wait 30 seconds for the change to propagate.
4. From the affected machine, run:
   ```bash
   python chaos_test.py --run-wrong-ip
   ```
5. `[7/15]` should print `PASS wrong IP whitelist: raised AuthenticationError`.
6. **Critical**: go back to Binance API Management and **restore the
   whitelist to your real IP**. Otherwise `test_phase2.py` and the
   future production bot will keep failing with `AuthenticationError`.

> ⚠️ Don't skip step 6. Forgetting to restore the IP is the most common
> way this test breaks future runs.

## Phase 3 setup

### 1. Upgrade your existing Binance API key (do NOT create a new one)

Edit the `dca_bot_phase2_readonly` key (User Center → API Management →
edit). Add **one** new permission on top of Reading:

- ✅ Enable Reading (keep)
- ✅ **Enable Spot & Margin Trading** (new)

**Never enable**:
- ❌ Enable Futures
- ❌ Enable Withdrawals (never, ever — this would let a leaked key drain funds)
- ❌ Permits Universal Transfer
- ❌ Enable Internal Transfer

**Keep the IP whitelist** — it is now your last line of defense against a
leaked key actually placing orders. Optionally rename the key to
`dca_bot_phase3_trade` as a visual reminder it has been upgraded. The
secret stays the same; `.env` doesn't need editing.

### 2. Fund USDT for testing

Transfer ~30-50 USDT into Spot Wallet (validation buys 11 USDT, the rest
gives the daily-cap mechanism room to breathe).

### 3. Run Phase 3 validation (real $11 BTC purchase)

```bash
python test_phase3.py
```

#### Expected result

- Terminal prints `Phase 3 驗證通過` and a fill summary line.
- Telegram receives **two** messages:
  - `📤 準備下單 11.00 USDT 買 BTC/USDT` (pre-trade audit)
  - `✅ 成交 ... USDT → ... BTC @ ...` (post-trade)
- `bot.log` contains `Pre-trade: ...` and `Order filled: ...` lines.
- `state/daily_state.json` is created with `{"date": "<today>", "spent_usdt": ~11.0}`.
- Binance backend Order History shows one FILLED market buy for BTC/USDT.

### 4. Run Phase 3 chaos tests

```bash
python chaos_test.py
```

Phase 3 chaos cases all fail-fast at local safety checks **without hitting
Binance**:

- `[8/15]` Symbol off whitelist → `ValueError`
- `[9/15]` Below min notional → `ValueError`
- `[10/15]` Above max single buy → `ValueError`
- `[11/15]` Daily cap exceeded → `ValueError`, state file untouched + cleaned

Telegram receives **no messages** for the Phase 1-3 cases. The state file
does not remain after chaos exits (cleaned up by `[11/15]`'s `finally`).
Phase 4 added 4 more cases — see the Phase 4 section for the full expected
result (14 passed, 1 skipped, total 15).

### Phase 3 safety knobs (in `trader.py`)

| Constant | Default | Meaning |
|---|---|---|
| `SYMBOL_WHITELIST` | `{BTC/USDT, ETH/USDT}` | Only these symbols can be bought |
| `DAILY_CAP_USDT` | `50.0` | Hard ceiling on total USDT spent per Asia/Taipei calendar day |
| `MAX_SINGLE_BUY_USDT` | `25.0` | Hard ceiling on a single order |
| `MIN_SINGLE_BUY_USDT` | `5.0` | Strategy floor; final min = `max(this, Binance min notional)` |
| `BALANCE_SAFETY_MULTIPLIER` | `1.01` | Required balance = quote × this (1% buffer for fees + slippage) |

The daily counter persists in `crypto_dca_bot/state/daily_state.json`,
written atomically (tmp file + `os.replace`) so a process crash mid-write
cannot corrupt it. Cross-day reset is keyed off Asia/Taipei date.

### Single-process discipline

Phase 3/4 assume **only one process touches `daily_state.json` at a time**.
There is no file lock. If you accidentally run `test_phase3.py` while a
Phase 4 cron tick is also placing an order, the daily cap can be bypassed
once — bounded loss is `MAX_SINGLE_BUY_USDT` (25 USDT) for that single
event. Phase 5 will add cross-platform locking if needed.

## Phase 4 setup

### What's new

- **`main.py`** — schedule loop with `schedule.every().day.at(...)`, signal-based
  graceful shutdown, heartbeat job
- **`circuit_breaker.py`** — N consecutive failures → `sys.exit(1)` + Telegram
  alert (default 5)
- **`heartbeat.py`** — every 6h posts a status snapshot (USDT/BTC/ETH balance,
  total value, today's spend, failure counter)
- **`high_water_mark.py`** — push notification when total holdings hit a new
  high above 100 USDT
- **`price_recorder.py`** — every successful `get_price` writes to
  `data/prices.sqlite` (V3 backtest dataset; failures are warning-only)
- **`config.py`** — single source of truth for tunables (`DCA_AMOUNT_USDT`,
  `DCA_TIME`, `DAILY_CAP_USDT`, `DRY_RUN`, etc.)

### Host timezone requirement

The bot relies on **the host system clock being Asia/Taipei (UTC+8)** because
the `schedule` library uses local time for `at("HH:MM")`. Date logic
(cross-day reset, today's symbol) uses `trader.TAIPEI_TZ` (fixed UTC+8) so
no `tzdata` package is required on Windows.

Verify the host timezone before launch:

```powershell
# Windows
Get-TimeZone
# Expected: Id : Taipei Standard Time   BaseUtcOffset : 08:00:00
```

If the host is in a different timezone, change Settings → Time & Language →
Time zone before running `main.py`.

### 1. Run the dry-run integration test

```bash
python test_phase4.py
```

Expected:

- Terminal prints `Phase 4 整合驗證通過`
- Telegram receives **2 messages**:
  - `🧪 [DRY-RUN] 模擬買 5.5 USDT BTC/USDT` (or ETH on even days)
  - `💓 Bot 存活 ...` heartbeat snapshot
- `state/daily_state.json` is **not modified** (dry-run guarantee)
- No Binance order is placed

### 2. Run Phase 4 chaos tests

```bash
python chaos_test.py
```

Expected: **14 passed, 0 failed, 1 skipped (total 15)**. The skip is `[7/15]`
(semi-manual wrong-IP). New Phase 4 cases:

- `[12/15]` DRY-RUN mode → `run_dca_cycle()` makes no API call, state file
  byte-for-byte unchanged
- `[13/15]` Circuit breaker trip → 5 consecutive `record_failure` calls →
  `SystemExit(1)` + **1 Telegram message** (`🚨 Circuit breaker TRIPPED`,
  side-effect by design)
- `[14/15]` Cross-day reset → seeded yesterday's `spent_usdt=11.5`,
  `_check_daily_cap(5.5)` returns today's date with `spent_usdt=0.0`
- `[15/15]` Graceful shutdown → direct call to `_signal_handler(SIGTERM, None)`
  sets `shutdown_event`. The OS-signal path is verified manually in Stage 3
  below (real `Ctrl+C`).

### 3. Validation roadmap (live trading)

The plan is to consume ~11 USDT for a cross-day validation, then ~16.5 USDT
over 3 days of `12:00` production runs.

#### Stage 3: cross-day validation (~14h, ~30 min active)

##### Pre-flight (run before D1 23:25 — 11 items, all must be green)

> Production host = Windows. Commands assume an active venv. Cheapest checks
> first; abort the run if any item fails — do not wave it through.

**Host environment**

1. **Repo sync**:
   ```bash
   git pull
   ```
2. **Host timezone** must be Asia/Taipei (UTC+8) — `schedule` uses local clock:
   ```powershell
   Get-TimeZone
   ```
   Expected: `Id : Taipei Standard Time`, `BaseUtcOffset : 08:00:00`.
3. **Sleep / hibernate disabled** for 23:55–00:15 cross-day window:
   ```powershell
   powercfg /a
   ```
   Set Power Plan → Sleep → "Never" on AC. A sleep mid-window kills the
   23:55 tick or the cross-day reset.
4. **`.env` keys** — `crypto_dca_bot/.env` exists with all four filled:
   `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `BINANCE_API_KEY`,
   `BINANCE_API_SECRET`.
5. **Dependency versions** (`ccxt` and `schedule` are the highest-risk):
   ```bash
   pip freeze | findstr /R "^ccxt== ^schedule=="
   ```
   Compare against the versions used in your last green chaos run; any
   mismatch → reinstall before proceeding. `requirements.txt` uses `>=`
   so silent upgrades are possible.
6. **`bot.log` headroom** < 4 MB:
   ```bash
   dir crypto_dca_bot\bot.log
   ```
   `RotatingFileHandler` rotates at 5 MB. ≥ 4 MB → archive + truncate so
   Stage 3 doesn't straddle a rotation boundary.
7. **No stale `state/daily_state.json`**:
   ```bash
   type crypto_dca_bot\state\daily_state.json
   ```
   Acceptable: file does not exist, OR `{"date": "<today>", "spent_usdt": 0.0}`.
   Anything else (yesterday's date, non-zero spend from an aborted run) →
   delete the file before starting.

**Application sanity**

8. **Telegram path**:
   ```bash
   python test_phase1.py
   ```
   Expected: terminal `Phase 1 驗證通過`, Telegram receives
   `Bot 初始化成功 ✅`.
9. **Pre-flight smoke + balance reconciliation**:
   ```bash
   python main.py --check
   ```
   Prints config + live `USDT / BTC / ETH` free balances + `Pre-flight OK`.
   Sends no `🟢 上線` Telegram and starts no schedule. **Cross-check the
   three balances against a fresh Binance App screenshot** — any
   discrepancy means wrong account / wrong key / out-of-date snapshot.

**Chaos re-verify**

10. **Wrong-IP whitelist on the Phase 3 trade-permission key** (the Phase 2
    pass was on the read-only key; the upgraded key has not been verified):
    on Binance, change the whitelist to `1.2.3.4`, wait 30 s, then:
    ```bash
    python chaos_test.py --run-wrong-ip
    ```
    Expected: `[7/15] PASS wrong IP whitelist: raised AuthenticationError`.
    **Critical**: restore the real IP whitelist immediately after —
    forgetting this kills the 23:55 tick.
11. **Dry-run graceful shutdown** end-to-end (validates `🛑 下線` Telegram
    actually fires; chaos `[15/15]` only checks the event flag, not the
    Telegram path):
    ```cmd
    set DRY_RUN=1
    python main.py
    ```
    Wait for `🟢 Bot 上線` Telegram, then **Ctrl+C**. Expected: terminal
    logs `Signal 2 received, graceful shutdown initiated`, Telegram
    receives `🛑 Bot 下線`, `state/daily_state.json` unchanged. Then
    clear the env var before the real Stage 3 launch:
    ```cmd
    set DRY_RUN=
    ```

##### Steps

1. **Day 1 23:30** — set `DCA_TIME = "23:55"` in `config.py`, then:
   ```bash
   python main.py
   ```
   You should receive `🟢 Bot 上線`.
2. **Day 1 23:55** — auto-triggers BTC 5.5 USDT buy (pre-trade + post-trade
   notifications, two messages).
3. **Day 2 00:15** — change `DCA_TIME = "00:15"` in `config.py`, **Ctrl+C**
   the bot (you should receive `🛑 Bot 下線` — this verifies the OS signal
   path), then `python main.py` again. The window from D2 ~00:00 (Ctrl+C)
   to 00:15 (next tick) is **15 minutes** — comfortable margin for edit +
   restart; cross-day reset still validates as long as the second buy
   lands on a new calendar date.
4. The 00:15 tick auto-triggers ETH 5.5 USDT buy. `state/daily_state.json`
   resets to today + accumulates from `0.0 → 5.5` (proof that cross-day
   reset works in production).
5. **Day 2 06:00** — first heartbeat fires; verify `💓 Bot 存活` arrives.
6. **Day 2 morning** — audit: `bot.log` + `state/daily_state.json` +
   `data/prices.sqlite` + Binance Order History.

##### Contingency: 單筆失敗時的決策樹

Stage 3 has 2 ticks (D1 23:55 BTC, D2 00:15 ETH). Market buys are irreversible
— "rollback" means stop + audit, never auto-replay.

**Per-tick failure mode → action**

- 🚨 `ccxt.AuthenticationError` (Binance `-2015`: bad key / IP mismatch /
  missing permission) → **HARD STOP**. Ctrl+C bot, audit Binance API key.
  Stage 3 abort + reschedule.
- 💰 `ccxt.InsufficientFunds` → **HARD STOP**. Top up Spot wallet to ≥ 12 USDT.
  If still before the next tick, restart bot; otherwise abort.
- 🌐 `ccxt.NetworkError` / timeout → **LET RIDE**. `schedule` does not retry
  mid-day; the next opportunity is the other day's tick. If that also fails,
  abort.
- ❌ Local `ValueError` (symbol whitelist / notional / cap) → **HARD STOP**.
  This is a config bug, not a market issue. Investigate `config.py` +
  `trader.py` constants before restarting.
- ❓ Unknown exception → check `bot.log`; **STOP** by default.

**Cross-day reset glitch (the thing Stage 3 actually verifies)**

- At ~D2 00:00 (before tick), `state/daily_state.json` should still be
  `{"date": <D1>, "spent_usdt": 5.5}`.
- After D2 00:15 tick, state should be `{"date": <D2>, "spent_usdt": 5.5}` —
  **not** `11.0`, **not** the D1 date.
- If state shows `spent_usdt = 11.0` or a stale date →
  `trader._check_daily_cap` is broken. **HARD STOP**. Do not proceed to
  Stage 4 until fixed.

**Notes**

- CircuitBreaker will not trip in Stage 3 (only 2 ticks; threshold is 5
  consecutive failures). Don't rely on it for safety.
- Telegram silence ≠ trade silence. Always cross-check Binance Order History.
- Manual state edits: write a tmp file then `os.replace` (mirrors
  `trader._write_state` atomicity) — never edit `daily_state.json` in place.

USDT consumed: ~11.

#### Stage 4: 3-day production trial (~16.5 USDT)

1. Set `DCA_TIME = "12:00"` in `config.py`.
2. Configure Windows Task Scheduler (see below).
3. Reboot once to verify auto-launch.
4. Let it run 3 days. Each 12:00 buys 5.5 USDT alternating BTC/ETH/BTC.

USDT consumed: ~16.5. Remaining buffer: ~10.5 of the original 38.

### 4. Windows Task Scheduler

- **Trigger**: At log on of any user
- **Action**: `python.exe D:\ios9-springboard-headers\crypto_dca_bot\main.py`
- **Settings**:
  - "If the task fails, restart every 1 minute, attempt up to 3 times"
  - "Stop the task if it runs longer than 25 hours" (daily restart clears any
    slow leak + reloads `config.py`)
- **Conditions**: untick "Start the task only if the computer is on AC power"

> Mac mini deployment uses `launchd` (plist with `KeepAlive=true` +
> `RunAtLoad=true`); not part of Phase 4.

### Phase 4 safety knobs (in `config.py`)

| Constant | Default | Meaning |
|---|---|---|
| `DRY_RUN` | `False` | If `True`, log + Telegram only — never call exchange write APIs |
| `DCA_AMOUNT_USDT` | `5.5` | USDT spent per scheduled buy |
| `SYMBOLS_ROTATION` | `("ETH/USDT", "BTC/USDT")` | `day % 2` selects today's symbol (tuple order is significant: even days → index 0 = ETH, odd days → BTC) |
| `DCA_TIME` | `"12:00"` | Local-clock time of daily buy (host must be Asia/Taipei) |
| `DAILY_CAP_USDT` | `12.0` | Overrides `trader.DAILY_CAP_USDT` (Phase 3 default 50) |
| `HEARTBEAT_HOURS` | `6` | Interval between `💓 Bot 存活` posts |
| `MAX_CONSECUTIVE_FAILURES` | `5` | Circuit breaker trip threshold |
| `HIGH_WATER_MARK_USDT` | `100.0` | Total-value threshold for `🚀 持倉新高` push |

### Notes on schedule semantics

- `schedule` does **not** make up missed jobs: if the bot is down at 12:00
  and restarts at 14:00, it does **not** retroactively fire the missed
  12:00 tick. For DCA this is the desired behavior.
- One bot process per host: there is no cross-process lock on
  `daily_state.json`. Don't run `test_phase3.py` while the Phase 4 bot is
  also running.

## Security

- `.env` is gitignored; never commit real API keys.
- Only `.env.example` (placeholder values) lives in git.
- API keys are loaded at construction time from `os.environ`.
- Tokens are redacted from log output via `notifier.py`.
- `BinanceExchange` only requests Read-permission keys for Phase 2.

## Layout

```
crypto_dca_bot/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── logger.py            # rotating file + stdout logger (Asia/Taipei TZ)
├── notifier.py          # TelegramNotifier (token-redacted, lazy factory)
├── exchange_api.py      # BinanceExchange (ccxt; price + balance + recorder hook)
├── trader.py            # BinanceTrader (market buy + safety + daily cap)
├── config.py            # Phase 4: tunables (DCA_TIME, DRY_RUN, caps, etc.)
├── main.py              # Phase 4: schedule loop + signal handler + heartbeat job
├── circuit_breaker.py   # Phase 4: N consecutive failures -> sys.exit(1)
├── heartbeat.py         # Phase 4: 6h status snapshot to Telegram
├── price_recorder.py    # Phase 4: SQLite price log (V3 backtest dataset)
├── high_water_mark.py   # Phase 4: total-value high alerts
├── state/               # daily-cap counter (gitignored content)
│   └── .gitkeep
├── data/                # Phase 4 runtime data (prices.sqlite, runtime_state.json)
│   └── .gitkeep
├── test_phase1.py       # Phase 1 validation
├── test_phase2.py       # Phase 2 validation
├── test_phase3.py       # Phase 3 validation (real $11 BTC buy)
├── test_phase4.py       # Phase 4 dry-run integration test
└── chaos_test.py        # 15 failure-injection tests (1 semi-manual)
```
