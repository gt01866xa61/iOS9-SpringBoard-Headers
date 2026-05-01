# Crypto Smart DCA Bot

A 24/7 crypto DCA + holdings-monitor bot.
Exchange: **Binance** (via `ccxt`). Notifications: **Telegram Bot**.

## Phase progress

| Phase | Scope | Status |
| ----- | ----- | ------ |
| 1 | Logger + Telegram notifier bootstrap | ✅ Done |
| 2 | `exchange_api.py` — ccxt price + balance (read-only) | ✅ Done |
| 3 | `trader.py` — market buy with multi-layer safety + daily cap | ✅ Implemented — awaiting user validation |
| 4 | `main.py` — schedule loop + high-water alerts | Pending |

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
5. `[7/11]` should print `PASS wrong IP whitelist: raised AuthenticationError`.
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

Expected: **10 passed, 0 failed, 1 skipped (total 11)**. The skip is
`[7/11]` (semi-manual wrong-IP, same as Phase 2). New Phase 3 cases all
fail-fast at local safety checks **without hitting Binance**:

- `[8/11]` Symbol off whitelist → `ValueError`
- `[9/11]` Below min notional → `ValueError`
- `[10/11]` Above max single buy → `ValueError`
- `[11/11]` Daily cap exceeded → `ValueError`, state file untouched + cleaned

Telegram receives **no messages** during chaos. The state file does not
remain after chaos exits (cleaned up by `[11/11]`'s `finally`).

### Phase 3 safety knobs (in `trader.py`)

| Constant | Default | Meaning |
|---|---|---|
| `SYMBOL_WHITELIST` | `{BTC/USDT, ETH/USDT}` | Only these symbols can be bought |
| `DAILY_CAP_USDT` | `50.0` | Hard ceiling on total USDT spent per Asia/Taipei calendar day |
| `MAX_SINGLE_BUY_USDT` | `25.0` | Hard ceiling on a single order |
| `MIN_SINGLE_BUY_USDT` | `10.0` | Strategy floor; final min = `max(this, Binance min notional)` |
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
├── logger.py          # rotating file + stdout logger (Asia/Taipei TZ)
├── notifier.py        # TelegramNotifier (token-redacted, lazy factory)
├── exchange_api.py    # BinanceExchange (ccxt; price + balance, read-only)
├── trader.py          # BinanceTrader (market buy + safety + daily cap)
├── state/             # runtime daily-cap counter (gitignored content)
│   └── .gitkeep
├── test_phase1.py     # Phase 1 validation
├── test_phase2.py     # Phase 2 validation
├── test_phase3.py     # Phase 3 validation (real $11 BTC buy)
└── chaos_test.py      # 11 failure-injection tests (1 semi-manual)
```
