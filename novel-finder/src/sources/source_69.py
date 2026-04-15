"""
source_69.py — 69書吧（69shuba.cx）書源實作
繼承 NovelSource，實作搜尋、榜單、章節列表、章節內容四個介面。
"""
import urllib.parse
from typing import List

from bs4 import BeautifulSoup

from .base import NovelSource, BookInfo, ChapterInfo
from ..utils.cleaner import clean_text

BASE = "https://www.69shuba.cx"

CATEGORY_MAP = {
    "玄幻": "1",
    "仙俠": "2",
    "都市": "3",
    "穿越": "4",
    "歷史": "5",
    "懸疑": "6",
}

# 各分類榜單 URL（綜合榜用首頁熱門區）
RANK_URLS = {
    "":    f"{BASE}/top/allvisit/",
    "玄幻": f"{BASE}/top/allvisit/1/",
    "仙俠": f"{BASE}/top/allvisit/2/",
    "都市": f"{BASE}/top/allvisit/3/",
    "穿越": f"{BASE}/top/allvisit/4/",
    "歷史": f"{BASE}/top/allvisit/5/",
    "懸疑": f"{BASE}/top/allvisit/6/",
}


class Source69(NovelSource):
    """69書吧書源"""

    BASE_URL = BASE

    # ------------------------------------------------------------------
    # 搜尋
    # ------------------------------------------------------------------
    def search(self, keyword: str) -> List[BookInfo]:
        url = f"{BASE}/search.aspx"
        try:
            resp = self._make_request(
                url,
                method="POST",
                data={"searchkey": keyword, "searchtype": "articlename"},
            )
        except Exception:
            # 也嘗試 GET 方式
            encoded = urllib.parse.quote(keyword)
            resp = self._make_request(f"{BASE}/search/{encoded}/")

        soup = BeautifulSoup(resp.text, "lxml")
        results: List[BookInfo] = []

        # 搜尋結果通常在 ul.newlist 或 div.searchlist
        items = soup.select("ul.newlist li") or soup.select("div.searchlist .bookbox")

        for idx, item in enumerate(items[:10], start=1):
            title_tag = item.select_one("h3 a") or item.select_one(".bookname a")
            author_tag = item.select_one(".author") or item.select_one("p.author")
            chapter_tag = item.select_one(".update a") or item.select_one(".readed a")

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            if href and not href.startswith("http"):
                href = BASE + href

            author = ""
            if author_tag:
                author = author_tag.get_text(strip=True).replace("作者：", "").replace("作者:", "").strip()

            latest = ""
            if chapter_tag:
                latest = chapter_tag.get_text(strip=True)

            results.append({
                "id": idx,
                "title": title,
                "author": author,
                "latest_chapter": latest,
                "url": href,
            })

        return results

    # ------------------------------------------------------------------
    # 榜單
    # ------------------------------------------------------------------
    def get_rank(self, category: str = "") -> List[BookInfo]:
        rank_url = RANK_URLS.get(category, RANK_URLS[""])
        resp = self._make_request(rank_url)
        soup = BeautifulSoup(resp.text, "lxml")
        results: List[BookInfo] = []

        # 榜單通常是 ol.rank-list 或 ul.toplist
        items = (
            soup.select("ol.rank-list li")
            or soup.select("ul.toplist li")
            or soup.select("div.topbooks .bookbox")
        )

        for idx, item in enumerate(items[:20], start=1):
            title_tag = item.select_one("a.name") or item.select_one("h3 a") or item.select_one("a")
            author_tag = item.select_one(".author") or item.select_one("p.author")

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            if href and not href.startswith("http"):
                href = BASE + href

            author = ""
            if author_tag:
                author = author_tag.get_text(strip=True).replace("作者：", "").replace("作者:", "").strip()

            results.append({
                "id": idx,
                "title": title,
                "author": author,
                "url": href,
            })

        return results

    # ------------------------------------------------------------------
    # 章節列表
    # ------------------------------------------------------------------
    def get_chapters(self, book_url: str) -> List[ChapterInfo]:
        resp = self._make_request(book_url)
        soup = BeautifulSoup(resp.text, "lxml")
        chapters: List[ChapterInfo] = []

        # 69書吧的章節列表通常在 #chapterlist 或 .chapters 區塊
        chapter_list = (
            soup.select("#chapterlist a")
            or soup.select(".chapters a")
            or soup.select("ul.chapter-list a")
            or soup.select(".catalog a")
        )

        # 若找不到，嘗試去 /catalog/ 頁面
        if not chapter_list:
            # 取書籍 ID，組合目錄 URL
            catalog_url = book_url.rstrip("/") + "/catalog/"
            try:
                resp2 = self._make_request(catalog_url)
                soup2 = BeautifulSoup(resp2.text, "lxml")
                chapter_list = soup2.select("a")
            except Exception:
                pass

        for a in chapter_list:
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if not href or not title:
                continue
            if href and not href.startswith("http"):
                href = BASE + href
            # 過濾非章節連結（通常章節 URL 含 /txt/ 或數字）
            if "/txt/" not in href and not any(c.isdigit() for c in href.split("/")[-1]):
                continue
            chapters.append({"title": title, "url": href})

        return chapters

    # ------------------------------------------------------------------
    # 章節內文
    # ------------------------------------------------------------------
    def get_content(self, chapter_url: str) -> str:
        resp = self._make_request(chapter_url)
        soup = BeautifulSoup(resp.text, "lxml")

        # 內文容器
        content_div = (
            soup.select_one("#content")
            or soup.select_one(".content")
            or soup.select_one("#chaptercontent")
            or soup.select_one("div.txt")
        )

        if not content_div:
            return ""

        raw_html = str(content_div)
        return clean_text(raw_html)
