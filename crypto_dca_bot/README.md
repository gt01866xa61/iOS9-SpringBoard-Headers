# Crypto Smart DCA Bot

A 24/7 crypto DCA + holdings-monitor bot.
Exchange: **Binance** (via `ccxt`). Notifications: **Telegram Bot**.

## Phase progress

| Phase | Scope | Status |
| ----- | ----- | ------ |
| 1 | Logger + Telegram notifier bootstrap | ✅ Done |
| 2 | `exchange_api.py` — ccxt price + balance (read-only) | ✅ Implemented — awaiting user validation |
| 3 | `trader.py` — buy with safety checks | Pending |
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
5. `[7/7]` should print `PASS wrong IP whitelist: raised AuthenticationError`.
6. **Critical**: go back to Binance API Management and **restore the
   whitelist to your real IP**. Otherwise `test_phase2.py` and the
   future production bot will keep failing with `AuthenticationError`.

> ⚠️ Don't skip step 6. Forgetting to restore the IP is the most common
> way this test breaks future runs.

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
├── test_phase1.py     # Phase 1 validation
├── test_phase2.py     # Phase 2 validation
└── chaos_test.py      # 7 failure-injection tests (1 semi-manual)
```
