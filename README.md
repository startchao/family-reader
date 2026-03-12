# Family English Reader

全家英文閱讀練習平台。每天自動生成文章，也可以隨時手動生成新文章。

## 功能
- 📅 每天早上 06:00 自動生成四位家人的英文閱讀文章
- ✍️ 隨時可以手動生成新文章（即時 AI 生成）
- 📊 閱讀進度與答題率記錄
- 📂 過去文章存檔可回顧

## 家人程度設定
| 使用者 | 程度 | 主題 |
|--------|------|------|
| Tony | B2–C1 · FLPT 導向 | 地緣政治、軍事、國際安全 |
| Angel | B2–C1 | 生活、文化、健康、旅遊（廣泛） |
| Jill | B2 · 國高中 | 時事、科技、環境、跨文化 |
| Guan | A2–B1 · 小學—國中 | 動物、自然、運動、趣味知識 |

## 專案結構
```
family-reader/
├── .github/workflows/daily.yml   # 自動排程
├── scripts/generate_daily.py     # 文章生成程式
├── docs/
│   ├── index.html                # 首頁
│   ├── tony.html                 # Tony 手動版
│   ├── angel.html                # Angel 手動版
│   ├── jill.html                 # Jill 手動版
│   ├── guan.html                 # Guan 手動版
│   └── *_YYYY-MM-DD.html         # 每日自動生成文章
└── .gitignore
```

## 設定說明
1. Settings → Secrets → 加入 `GEMINI_API_KEY`
2. Settings → Pages → Branch: main，資料夾: `/docs`
3. Actions → 手動執行一次測試
