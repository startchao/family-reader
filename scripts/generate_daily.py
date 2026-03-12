#!/usr/bin/env python3
"""
Family Daily Reader — Daily Article Generator
優化版：自動建立資料夾、動態路徑修正、移除寫死的 API Key。
"""

import os
import json
import urllib.request
import urllib.error
import datetime
import re
import sys

# ── 1. 路徑與環境變數優化 ───────────────────────────────────────────────────
# 取得腳本所在的絕對路徑，並定位到上一層的 docs 資料夾
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs")

# 從 GitHub Secrets 讀取 Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
TODAY = datetime.date.today().isoformat()

# ── 2. 成員設定 (內容維持您的邏輯，僅優化 Prompt 結構) ──────────────────────────
MEMBERS = [
    {
        "id": "tony",
        "name": "Tony",
        "icon": "📰",
        "color": "#c0392b",
        "badge": "B2–C1 · FLPT",
        "storage_key": "daily_tony",
        "prompt": f"You are an expert FLPT tutor. Generate a B2-C1 level English article for a Taiwanese military officer. Topic: Geopolitics or Military. Output in Traditional Chinese. Date: {TODAY}. Format: ===TITLE===, ===ARTICLE===, ===TRANSLATION===, ===VOCAB===, ===QUIZ==="
    },
    {
        "id": "angel",
        "name": "Angel",
        "icon": "🌸",
        "color": "#7d3c98",
        "badge": "B2–C1",
        "storage_key": "daily_angel",
        "prompt": f"You are an English teacher. Generate a B2-C1 level article about Lifestyle/Culture. Date: {TODAY}. Format: ===TITLE===, ===ARTICLE===, ===TRANSLATION===, ===VOCAB===, ===QUIZ==="
    },
    {
        "id": "jill",
        "name": "Jill",
        "icon": "📖",
        "color": "#16a085",
        "badge": "B2 · 國高中",
        "storage_key": "daily_jill",
        "prompt": f"You are an English teacher. Generate a B2 level article about Tech/Environment for high schoolers. Date: {TODAY}. Format: ===TITLE===, ===ARTICLE===, ===TRANSLATION===, ===VOCAB===, ===QUIZ==="
    },
    {
        "id": "guan",
        "name": "Guan",
        "icon": "🚀",
        "color": "#2980b9",
        "badge": "A2–B1 · 國小-國中",
        "storage_key": "daily_guan",
        "prompt": f"You are a fun English teacher. Generate an A2-B1 level article about Animals/Sports for kids. Date: {TODAY}. Format: ===TITLE===, ===ARTICLE===, ===TRANSLATION===, ===VOCAB===, ===QUIZ==="
    }
]

# ── 3. API 與 解析邏輯 (略，維持原有高效解析) ──────────────────────────────────
def call_gemini(prompt):
    if not GEMINI_API_KEY:
        raise ValueError("請先在 GitHub Secrets 設定 GEMINI_API_KEY")
    payload = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.85}
    }).encode("utf-8")
    req = urllib.request.Request(f"{GEMINI_URL}?key={GEMINI_API_KEY}", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))["candidates"][0]["content"]["parts"][0]["text"]

def parse_response(raw):
    def extract(tag):
        m = re.search(rf"==={tag}===(.*?)(?====\w+===|$)", raw, re.DOTALL)
        return m.group(1).strip() if m else ""
    # 這裡保留原本的字典解析邏輯... (省略部分重複代碼)
    return {"title": extract("TITLE"), "article": extract("ARTICLE"), "translation": extract("TRANSLATION"), 
            "vocab": [], "quiz": []} # 範例簡化，請保留原有的完整解析

# ── 4. 主程式：增加資料夾保護與路徑輸出 ─────────────────────────────────────────
def main():
    # 強制檢查並建立 docs 資料夾
    if not os.path.exists(OUTPUT_DIR):
        print(f"📁 建立資料夾: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = {}
    for member in MEMBERS:
        print(f"🚀 正在生成 {member['name']} 的文章...")
        try:
            raw = call_gemini(member["prompt"])
            data = parse_response(raw)
            
            # 此處調用原本的 generate_member_html 邏輯
            # ...
            
            # 寫入檔案
            filename = f"{member['id']}_{TODAY}.html"
            out_path = os.path.join(OUTPUT_DIR, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("... (HTML 內容) ...") # 使用原有的 HTML 模板

            print(f"✅ 已存檔至: {out_path}")
            results[member["id"]] = True
        except Exception as e:
            print(f"❌ {member['name']} 失敗: {e}")
            results[member["id"]] = False

if __name__ == "__main__":
    main()
