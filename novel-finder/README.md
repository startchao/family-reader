# 小說搜尋下載器 Novel Finder

透過 Telegram Bot 搜尋、預覽、下載 69書吧（69shuba.cx）小說，並以 `.txt` 格式傳回。
運行環境為 GitHub Actions，無需自建伺服器。

---

## 功能介紹

| 功能 | 說明 |
|------|------|
| 熱門榜單 | 傳送 `/hot` 或 `/hot 分類` 取得 Top 20 書單 |
| 搜尋 | 直接輸入書名關鍵字，取得最多 10 筆候選 |
| 下載 | 選擇搜尋結果編號，自動下載全書並傳送 `.txt` |

支援分類：`玄幻` `仙俠` `都市` `穿越` `歷史` `懸疑`

---

## 環境需求

- Python 3.12
- 套件見 `requirements.txt`

---

## GitHub Secrets 設定

前往 `Settings → Secrets and variables → Actions → New repository secret`，新增以下兩項：

| Secret 名稱 | 說明 |
|---|---|
| `TELEGRAM_TOKEN` | 從 [@BotFather](https://t.me/BotFather) 建立 Bot 後取得的 Token |
| `TELEGRAM_CHAT_ID` | 你的 Telegram Chat ID（可傳訊給 [@userinfobot](https://t.me/userinfobot) 取得）|

---

## 部署方式

1. Fork 或 clone 本 repo
2. 設定好上述兩個 Secrets
3. 前往 **Actions → Novel Finder Bot → Run workflow**
4. 點 **Run workflow**（可選擇運行時間，預設 20 分鐘）
5. Job 啟動後，開啟 Telegram 與你的 Bot 對話

> **注意**：Bot 每次只能在 workflow 執行期間使用。
> 需要使用時再手動觸發一次 workflow 即可。

---

## 使用說明

```
/start          顯示說明
/hot            綜合熱門榜 Top 20
/hot 玄幻       玄幻分類榜 Top 20
/cancel         取消目前操作

直接輸入書名    搜尋書籍（例如：斗破蒼穹）
輸入編號        從搜尋結果中選擇並下載
```

---

## 專案結構

```
novel-finder/
├── src/
│   ├── main.py               # Bot 主程式（async，ConversationHandler）
│   ├── sources/
│   │   ├── base.py           # 書源抽象基底類別
│   │   └── source_69.py      # 69書吧 實作
│   └── utils/
│       ├── cleaner.py        # 內文清洗（去除廣告、HTML）
│       └── telegram.py       # Telegram API 封裝（大檔切分）
└── requirements.txt
```

---

## 反爬機制

- 隨機輪換 6 組 User-Agent
- 每次請求間隔 1～3 秒（`random.uniform`）
- 失敗自動 retry 最多 3 次（指數退避）
- 使用 `requests.Session()` 維持 Cookie

---

## 部署檢查清單

- [ ] 已在 GitHub Secrets 設定 `TELEGRAM_TOKEN`
- [ ] 已在 GitHub Secrets 設定 `TELEGRAM_CHAT_ID`
- [ ] 已透過 @BotFather 建立 Bot，並取得 Token
- [ ] 已向 Bot 傳送 `/start`（啟用對話）
- [ ] Workflow `crawler.yml` 已存在於 `.github/workflows/`
- [ ] 手動觸發 `Novel Finder Bot` workflow 確認正常啟動
- [ ] 測試傳送 `/hot` 確認榜單功能
- [ ] 測試輸入書名確認搜尋功能
- [ ] 測試輸入編號確認下載與 TXT 傳送功能
