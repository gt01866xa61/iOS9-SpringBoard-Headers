# M8:資安規格(Security / 維運安全)

> Backlog #8。V2 量化交易平台的**資安硬規格**(security spec)。
> 跟 M1–M7 不同類:M1–M7 是「**策略**能不能上線」的閘門(策略驗證);M8 是「**整個系統**能不能安全運行」的閘門(維運安全)。
> 真錢 + 對外可達的系統,**資安失守一次 = 資產直接被提走,沒有 retry**。所以 M8 跟策略賺不賺錢無關,卻同級重要。
> 全文白話。第一次出現的術語當場用人話解釋。維運名詞另見 `v2a/glossary.md`。

---

## 0. 為什麼「跟策略好壞無關」卻同級重要

白話講:再神的策略,**金鑰被偷 = 別人用你的帳戶把幣提走,你賺多少都歸零**。資安不是讓你賺更多,是讓你**不要一次見底**。

量化界把這種「跟市場漲跌無關、純粹人為/系統面出包」的風險叫 **operational risk(維運風險)** — 跟你押對押錯方向沒關係,是金鑰外洩、主機被入侵、手滑打錯網這類。M1–M7 管「市場風險」(策略會不會虧),M8 管「維運風險」(會不會被偷/被駭)。兩條腿,缺一條都站不穩。

**這段用人話總結:M8 是下限保護 — 防的是「歸零」,不是「少賺」。**

---

## 1. 現況稽核(2026-06-06 baseline)

動 M8 規格前,先把現況掃過一遍當基準線(baseline)。本次稽核結論:

| 查核項 | 現況 | 風險 |
|---|---|---|
| **Repo 是否 public** | ⚠️ **是 public**(`gt01866xa61/iOS9-SpringBoard-Headers`,`private:false`) | 中 — 策略邏輯/部署結構對全世界可見 |
| **git 歷史真金鑰殘留** | ✅ **無**。全歷史(50 commit、所有 ref、所有 blob)只找到**假值**:`chaos_test.py` 的 `0000000000:ChAoS_invalid_token_for_testing_xxxxx`(故意的測試假 token)、`bad_key_xxxxxxxx`(chaos 假金鑰) | 低 |
| **曾經 commit 過真 `.env`** | ✅ 從來沒有(任何路徑都沒有) | 低 |
| **code 寫死金鑰** | ✅ 無。`notifier.py` / `exchange_api.py` 全部 `os.environ` 讀;`notifier.py` 連例外訊息都把 token `.replace(..., "[REDACTED]")` | 低 |
| **`.gitignore` 是否擋 `.env`** | ✅ 有(`crypto_dca_bot/.gitignore` 第一行 `.env`) | 低 |
| **V1 時代 redact commit(`fcb6976`)** | ❗ **不在本 repo 歷史**(rev-parse 找不到) | **未知 — 見下** |

### 1.1 唯一需要動作的殘留風險:已退役 V1 token

`fcb6976`(記憶中「V1 做過 redact 的 commit」)**不在本 repo**。代表兩種可能,從現有歷史分不出是哪種:

1. 記憶中的「redact」其實是 `notifier.py` 那個**程式層 token 遮蔽**(把 log 裡的 token 換 `[REDACTED]`)→ 真 token 從沒進過 git → 完全乾淨。
2. 曾有**另一段歷史**(獨立 repo / 被 rebase/squash 掉的舊歷史)真 commit 過真 token,再用「改檔案」方式 redact → 那段歷史不在這裡。

**關鍵觀念:「改檔案式 redact」不會把 secret 從 git 歷史移除** — 真 token 永遠留在 redact 前那一個 commit。只要那段歷史曾 push 到 public,爬蟲幾秒內就掃走了。

**處置(已建議使用者):不要只 rotate,直接 revoke。** V1 已永久結案(2026-05-08,不重啟),這些 credential operational 價值是零,revoke 不痛不癢、又讓風險歸零:

- **Telegram**:找 `@BotFather` → `/deletebot`(V1 已死,直接刪)。
- **Binance**(若 Phase 2 真開過實 key):API Management 刪掉那把 key。

**這段用人話總結:這個公開 repo 本身沒在漏東西,不用緊急滅火;但那把查不到去向的 V1 token,花兩分鐘 revoke 掉當保險。**

### 處置結果(2026-05-26 使用者完成)

- ✅ **Telegram bot 已 revoke**(整隻刪了,`@BotFather /deletebot` 完成)
- 🟰 **Binance key 不需要 revoke** — owner 事實覆蓋 audit 假設:**V1 只跑模擬,從沒真錢交易,從未開過會 leak 的 trading key**。audit 段「若 Phase 2 真開過實 key」前提不成立 → 沒有 revoke 對象
- **資安尾巴結案**。下次需要 Binance key = V2-D step 4 tiny live 真錢上場前,屆時依本檔 § 2 規格生成(read-only / trading 分離 + 禁提現 + IP whitelist + 90 天 rotate)

---

## 2. API key 規範(交易所金鑰)

交易所 API key 是「能動你的錢的鑰匙」,M8 最高優先級。六條硬規:

### 2.1 trading key 禁開提現權限
- 在交易所後台,交易 key 只勾「現貨/合約交易」,**絕不勾「提現(Withdraw)」**。
- 白話:就算這把 key 整個被偷走,攻擊者**頂多亂下單**(再用 IP whitelist 擋死),**不能把幣轉走**。提現權限是「能搬空你帳戶」的權限,bot 下單根本用不到,一律關。

### 2.2 強制 IP whitelist(綁定固定 IP)
- key 綁定你 VPS 的固定出口 IP。非白名單 IP 拿這把 key 打 API,**交易所直接拒絕**。
- 白話:key 被偷走也沒用,因為攻擊者的 IP 不在名單上。
- 注意:Binance 規則 — **未綁 IP 的 key 預設禁提現**(且閒置一段時間會失效);綁了 IP 才能談提現。對 trading key 我們本來就禁提現,綁 IP 是再加一層。

### 2.3 read-only key 與 trading key 分離
- **看盤 / 抓資料 / 對帳**用 read-only key(只有讀權限,連下單都不行)。
- **下單**才用 trading key。
- 白話:research / backtest / monitoring 這些「只是要看數字」的程式,只拿到唯讀鑰匙。下單那把更危險的鑰匙,暴露面越小越好 — 只有真正執行下單的那一支程式碰得到。

### 2.4 實盤 key 與測試 key 分離
- **testnet(測試網)key** 與 **mainnet(實盤)key** 完全分開:不同變數名(`BINANCE_API_KEY` vs `BINANCE_TESTNET_API_KEY`)、最好不同 `.env`。
- 白話:防「測試程式手滑打到實盤」。測試就該打不到真錢的環境,結構上隔開,不靠人記得切。

### 2.5 定期 rotate(輪換金鑰)
- 每 **90 天**換一次:產生新 key → 更新 `.env` → 確認 bot 跑得動 → **刪掉舊 key**。
- 疑似外洩 / 換主機 / 任何異常 → **立即 rotate**,不等週期。
- 白話:鑰匙用久了暴露機率累積,定期換新的,舊的作廢。就算哪天悄悄漏了,壽命也被砍短。

### 2.6 永不寫死進 code
- 金鑰**只進 `.env`**,`.env` **進 `.gitignore`**,code 一律 `os.environ` 讀。
- V1 已經這樣做(`exchange_api.py` / `notifier.py`),V2 **繼續沿用,不准退步**。
- 白話:鑰匙跟程式碼分家。程式碼可以公開、可以進 git,鑰匙永遠只在那台機器的 `.env` 裡,絕不上傳。

**這段用人話總結:給 bot 的鑰匙要「能下單但不能提錢、只認自家 IP、唯讀和下單分兩把、測試和實盤分兩把、定期換、永遠不寫進程式碼」。最壞情況鑰匙被偷,對方頂多亂下單還被 IP 擋死,搬不走你的幣。**

---

## 3. 帳戶安全

金鑰守得再好,**帳戶後台被登入 = 對方自己生一把新 key**,前面全白做。所以帳戶這層是地基。

### 3.1 全面 2FA(雙因素驗證)
- **交易所、email、GitHub、VPS 供應商後台** — 全部開 **2FA**(two-factor authentication:登入要「密碼 + 第二道驗證」兩關)。
- 白話:光知道密碼進不來,還要過第二關(手機上的動態碼 / 插一把實體鑰匙)。

### 3.2 第二道驗證的優先序:硬體金鑰 / passkey 優先
- 優先序:**硬體金鑰(FIDO2 security key,如 YubiKey)/ passkey** > **TOTP authenticator app**(Google Authenticator / Authy 那種每 30 秒換的 6 碼) > ❌ **絕不用 SMS 簡訊 OTP**。
- 為什麼禁簡訊:**SIM swap(換卡攻擊)** — 攻擊者社工電信商把你的門號補發到他的 SIM,簡訊驗證碼就送到他手機。簡訊 2FA 等於沒有。
- 白話:第二道關卡,「插一把實體鑰匙」最穩(對方沒拿到那把實體鑰匙就是進不來),「手機 app 動態碼」次之,「簡訊」最弱、形同虛設,不要用。

### 3.3 email 是命門
- 幾乎所有帳戶的「忘記密碼 / reset」都走 email。**email 被攻破 = 全盤皆輸**(對方可以連鎖重設你所有帳戶)。
- 規範:email 帳戶用**最強的 2FA(硬體金鑰)**,且這個 email 不拿來到處註冊雜服務。
- 白話:email 是「重設所有鎖的萬能鑰匙」,所以它自己要鎖得最死。

### 3.4 password manager(密碼管理器)
- 用 **Bitwarden / 1Password** 這類工具,每個服務一組**獨立、隨機、高強度**密碼,**絕不重複用**。
- 白話:人腦記不住幾十組亂碼密碼,所以大家才重複用同一組 — 但只要一個小網站被脫庫,你所有帳戶都暴露。密碼管理器幫你記,你只記一組主密碼,每個服務的密碼都不一樣。

**這段用人話總結:帳戶後台是地基 — 全開雙重驗證、第二道用實體鑰匙(別用簡訊)、email 鎖最死、密碼用管理器每站一組不重複。守住後台,對方就算想自己生新鑰匙也進不去。**

---

## 4. Host(VPS / 主機)安全

bot 跑在一台對外的雲主機(VPS)上。主機被入侵 = `.env` 裡的鑰匙、運行中的程式全暴露。

### 4.1 只開必要 port(連接埠)
- 預設**拒絕所有 inbound(對內連線)**,只放行真正需要的 — 通常**只有 SSH 一個**(且建議改非標準 port,降低被掃描的噪音)。
- 交易 bot 是 **outbound-only**(主動連出去打交易所 API),**不需要對外開任何服務 port**。
- 白話:主機對外的門開越少越好。bot 只需要「出門」的能力,不需要「讓外面進來」的門,所以對外幾乎全關,只留一扇你自己管理用的 SSH。

### 4.2 SSH 禁密碼、只用金鑰
- `/etc/ssh/sshd_config`:`PasswordAuthentication no`、`PubkeyAuthentication yes`、`PermitRootLogin prohibit-password`(或 `no`)。
- 白話:SSH 登入只認「金鑰檔」,不認密碼。密碼登入會被全網機器人 24 小時暴力猜,金鑰登入幾乎不可能被猜中。順手禁掉 root 直接登入,逼用一般帳戶再提權。

### 4.3 UFW 防火牆
- 啟用 UFW(Uncomplicated Firewall,Ubuntu 內建的簡易防火牆):
  ```
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow <你的 SSH port>
  ufw enable
  ```
- 白話:再加一道「對內全擋、對外放行、只開 SSH」的牆,跟 4.1 互相補強(就算某個服務不小心開了 port,防火牆這層還擋著)。

### 4.4 log 不記完整 secret
- 任何 log / 錯誤訊息 / 告警,**都不能輸出完整金鑰、完整 token、完整 API secret**。最多印末 4 碼供辨識(`...a1b2`)。
- 呼應 V1 `notifier.py` 已實作的 `str(exc).replace(self._token, "[REDACTED]")` — **V2 沿用且擴大到所有 secret**。
- 白話:log 檔本身也可能外洩(被看到、被收集、被貼到聊天室求救)。所以連 log 裡都不准出現完整鑰匙,印出來的永遠是遮罩過的。

### 4.5 production 不跑 notebook
- production(正式運行)主機**不跑 Jupyter notebook**。
- 為什麼:notebook 常開 `0.0.0.0` 監聽埠(對外暴露)、token 可被繞過、能執行任意 code — 等於在你的交易主機上開一個「網頁版任意指令執行」後門。
- 規範:research / backtest 在**本機或隔離環境**跑;production 主機**只跑 bot 本體**,不裝互動式 shell 服務。
- 白話:跑真錢的那台機器,只做一件事(跑 bot),不要在上面開「可以隨便執行程式」的網頁工具。研究、回測在別的地方做。

### 4.6 補強(industry baseline)
- **自動安全更新**:`unattended-upgrades`(系統漏洞自動補)。
- **fail2ban**:偵測 SSH 反覆失敗登入自動封 IP(擋暴力破解)。
- **非 root 跑 bot**:用專用低權限帳戶跑 bot,不要用 root。萬一 bot 被打穿,攻擊者拿到的也只是低權限。

**這段用人話總結:跑真錢的主機 = 對外只留一扇 SSH 且只認金鑰、加防火牆、log 不露完整鑰匙、絕不在上面跑 Jupyter、用低權限帳戶跑 bot。把主機當保險箱顧,不是當工作桌用。**

---

## 5. Repo(程式碼倉庫)安全

### 5.1 設 private
- 交易 bot 的程式碼 repo **設 private(私有)**。
- 即使沒寫死金鑰,public repo 仍會暴露:**策略邏輯**(別人抄 / 反制)、**部署結構**、**依賴套件版本**(讓攻擊者對照已知漏洞)。
- ⚠️ **現況決策點**:本 repo(`iOS9-SpringBoard-Headers`)是 **public**,且混了 iOS headers 的開源內容跟 bot code。兩條路擇一:
  1. 把 `crypto_dca_bot/` **搬去獨立 private repo**(乾淨,推薦 — bot 跟 iOS headers 本來就無關);
  2. 整個 repo **轉 private**(快,但 iOS headers 一起變私有)。
- 白話:放真錢策略的程式碼不該開給全世界看。最好把 bot 抽出來放一個自己的私有倉庫。

### 5.2 pre-commit hook 掃 secret(detect-secrets)
- 裝 **pre-commit hook**(commit 前自動跑的檢查):每次 commit 前自動掃 staged(即將提交)的內容,**偵測到疑似金鑰就擋下 commit**。
- 工具:**detect-secrets**(Yelp 出的 secret 掃描器)。裝法:
  ```
  pip install detect-secrets pre-commit
  detect-secrets scan > .secrets.baseline      # 建立基準線(現有已知非真 secret 標記掉)
  # .pre-commit-config.yaml 掛上 detect-secrets hook
  pre-commit install                           # 把 hook 裝進 git
  ```
- 白話:這是「**進不去**」的防線 — 在金鑰被 commit 進去之前就攔下來,根本不讓它進 git。比事後再掃乾淨省事一百倍。

### 5.3 git 歷史掃過一遍
- 用 **detect-secrets / gitleaks / trufflehog** 掃**全歷史**(不只當前檔案,連舊 commit 都掃)。
- 本次(2026-06-06)已用 git 全 blob scan 掃過,結論:**無真洩漏**(見 § 1)。
- 規範:**定期重掃**(每季 / 每次大改後)。
- 白話:已經回頭把整段歷史翻過一遍確認乾淨,以後固定再翻,別讓漏的東西躺在舊紀錄裡沒人發現。

### 5.4 GitHub secret scanning + push protection
- repo 設好後(private + GitHub Advanced Security,或 public 直接有),開 **secret scanning** + **push protection**:有人 push 含金鑰的 commit,**GitHub 直接擋住 push**。
- 白話:GitHub 自己也幫你站一班崗 — 真有人手滑要推鑰匙上去,平台層再攔一次。

**這段用人話總結:bot 程式碼搬去私有倉庫、裝「commit 前自動擋鑰匙」的 hook、整段歷史掃過確認乾淨、再開 GitHub 平台層的攔截。三道防線:進 git 前擋(hook)、平台層擋(push protection)、事後稽核(掃歷史)。**

---

## 6. M8 驗收清單(checklist)

上線(V2-D 真錢)前逐項打勾,任何一項未過 = 不上真錢。

### API key
- [ ] trading key 已關提現權限
- [ ] trading key 已綁 IP whitelist(VPS 出口 IP)
- [ ] read-only key 與 trading key 分離,monitoring/research 只用 read-only
- [ ] testnet key 與 mainnet key 分離(不同變數名 / `.env`)
- [ ] 已排定 90 天 rotate 機制 + 異常立即 rotate 流程
- [ ] 金鑰只在 `.env`,`.env` 在 `.gitignore`,code 全 `os.environ` 讀(沿用 V1)

### 帳戶
- [ ] 交易所 / email / GitHub / VPS 後台全開 2FA
- [ ] 第二道用硬體金鑰或 passkey;**無任何帳戶用 SMS OTP**
- [ ] email 用最強 2FA(硬體金鑰),不拿來註冊雜服務
- [ ] 全服務改用 password manager,每站獨立隨機密碼

### Host(VPS)
- [ ] 對外只開 SSH(其餘 port 全關),bot 確認 outbound-only
- [ ] SSH `PasswordAuthentication no` + 只用金鑰 + 禁 root 密碼登入
- [ ] UFW 啟用(deny incoming / allow outgoing / allow SSH)
- [ ] 所有 log/告警 secret 遮罩(沿用並擴大 V1 `[REDACTED]`)
- [ ] production 主機無 Jupyter / 無互動式對外服務
- [ ] unattended-upgrades + fail2ban + 非 root 帳戶跑 bot

### Repo
- [ ] bot code 搬獨立 private repo(或整 repo 轉 private)
- [ ] detect-secrets pre-commit hook 已裝
- [ ] git 全歷史掃過確認無真洩漏(2026-06-06 已做一次)
- [ ] GitHub secret scanning + push protection 已開

### 殘留處置(2026-05-26 已收尾)
- [x] V1 Telegram bot 已 revoke(整隻刪了,`@BotFather /deletebot` 完成)
- [N/A] V1 Binance key — 從未開過真錢 trading key(V1 只跑模擬),無 revoke 對象

---

## 7. 全文白話總結

用最日常的話講,M8 就四句:

1. **給機器人的鑰匙**:能下單、不能提錢、只認自家網路、定期換、永遠不寫進程式碼。被偷也搬不走你的幣。
2. **你的帳戶後台**:全開雙重驗證、第二關用實體鑰匙(別用簡訊)、email 鎖最死、密碼每站不一樣。別讓人從後台自己配新鑰匙。
3. **跑真錢的主機**:當保險箱顧 — 對外只留一扇上鎖的門(SSH 金鑰)、加防火牆、log 不露鑰匙、不在上面跑網頁版程式工具。
4. **程式碼倉庫**:放私有、裝「commit 前自動擋鑰匙」的關卡、整段歷史掃乾淨。

跟 M1–M7 的關係:M1–M7 防「策略虧錢」,M8 防「資產被偷 / 系統被駭」。前者是少賺,後者是歸零。**真錢上線前,M8 跟 M1–M7 一樣是硬閘門,不是建議。**

---

*建立:2026-06-06。門檻數字(rotate 週期等)為初版,V2-D 上線前 review 校準。*
