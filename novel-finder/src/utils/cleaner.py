"""
cleaner.py — 小說內文清洗工具
clean_text(raw_html) → str
"""
import re

from bs4 import BeautifulSoup

# 需要移除的廣告關鍵字模式（整行移除）
_AD_PATTERNS = [
    r"本章未完[，,。].*",
    r"請記住本站.*",
    r"筆趣閣.*",
    r"請收藏.*",
    r"手機版閱讀.*",
    r"最新章節.*",
    r"全文閱讀.*",
    r".*加入書架.*",
    r".*推薦票.*",
    r".*點擊下一頁.*",
    r".*下一章.*",
    r".*上一章.*",
    r".*返回書頁.*",
    r".*本書最新.*",
    r".*閱讀記錄.*",
    r".*更多精彩.*",
    r".*www\.\S+\.com.*",
    r".*www\.\S+\.cx.*",
    r".*69shuba.*",
    r".*69書吧.*",
    r"一秒記住.*",
    r"天才一秒.*",
    r".*為您提供.*",
    r".*飄天文學.*",
    r".*頂點小說.*",
]

_AD_RE = re.compile("|".join(_AD_PATTERNS), re.IGNORECASE)


def clean_text(raw_html: str) -> str:
    """
    將原始 HTML 清洗為乾淨的純文字。
    步驟：
    1. 用 BeautifulSoup 去除所有 HTML 標籤
    2. 移除廣告關鍵字行
    3. 壓縮超過 2 個連續空行為單一空行
    4. 去除行首尾空白
    """
    # 先把 <br> / <p> 轉成換行，避免文字黏在一起
    raw_html = re.sub(r"<br\s*/?>", "\n", raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r"</p>", "\n", raw_html, flags=re.IGNORECASE)

    soup = BeautifulSoup(raw_html, "lxml")

    # 移除 script / style 節點
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # 逐行處理
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            lines.append("")
            continue
        # 跳過廣告行
        if _AD_RE.search(line):
            continue
        lines.append(line)

    # 壓縮連續空行（超過 2 行 → 1 行）
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))

    return result.strip()


def remove_duplicate_title(content: str, chapter_title: str) -> str:
    """
    移除章節內文開頭重複出現的章節標題。
    """
    if not chapter_title:
        return content
    # 移除開頭出現的標題（允許前後有空白或標點）
    escaped = re.escape(chapter_title.strip())
    pattern = rf"^\s*{escaped}\s*\n?"
    return re.sub(pattern, "", content, count=1)
