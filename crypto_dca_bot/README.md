# Crypto Smart DCA Bot

A 24/7 crypto DCA + holdings-monitor bot.
Exchange: **Binance** (via `ccxt`). Notifications: **Telegram Bot**.

## Phase progress

| Phase | Scope | Status |
| ----- | ----- | ------ |
| 1 | Logger + Telegram notifier bootstrap | Implemented — awaiting user validation |
| 2 | `exchange_api.py` — ccxt price + balance | Pending |
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

## Security

- `.env` is gitignored; never commit real API keys.
- Only `.env.example` (placeholder values) lives in git.
- The notifier reads credentials at init time from `os.environ`.

## Layout

```
crypto_dca_bot/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── logger.py          # rotating file + stdout logger
├── notifier.py        # TelegramNotifier
└── test_phase1.py     # validation script
```
