"""
base.py — 書源抽象基底類別
定義所有書源必須實作的介面，並提供共用的 HTTP 請求機制（隨機 UA、retry、sleep）。
"""
import random
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any

import requests
from requests import Session

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

# BookInfo 欄位：id, title, author, category, chapters, url
BookInfo = Dict[str, Any]
# ChapterInfo 欄位：title, url
ChapterInfo = Dict[str, str]


class NovelSource(ABC):
    """所有書源的抽象基底類別"""

    BASE_URL: str = ""
    MAX_RETRIES: int = 3

    def __init__(self):
        self.session: Session = requests.Session()

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        """
        帶有隨機 UA、sleep、retry 的 HTTP 請求。
        失敗最多重試 MAX_RETRIES 次。
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                headers = kwargs.pop("headers", {})
                headers["User-Agent"] = random.choice(USER_AGENTS)
                headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
                headers.setdefault("Accept-Language", "zh-TW,zh;q=0.9,en;q=0.8")

                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=20,
                    **kwargs,
                )
                response.raise_for_status()

                # 請求成功後 sleep 1~3 秒
                time.sleep(random.uniform(1, 3))
                return response

            except requests.RequestException as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                wait = 2 ** attempt  # 指數退避：1s, 2s, 4s
                time.sleep(wait)

        # 不應該到這裡，但為了型別安全
        raise RuntimeError(f"Failed to fetch {url} after {self.MAX_RETRIES} retries")

    @abstractmethod
    def search(self, keyword: str) -> List[BookInfo]:
        """
        搜尋書名關鍵字，回傳最多 10 筆 BookInfo。
        BookInfo 必須包含：id, title, author, chapters, url
        """

    @abstractmethod
    def get_rank(self, category: str = "") -> List[BookInfo]:
        """
        取得熱門榜單，回傳最多 20 筆 BookInfo。
        category 為空字串時回傳綜合榜。
        """

    @abstractmethod
    def get_chapters(self, book_url: str) -> List[ChapterInfo]:
        """
        解析書籍頁面，回傳章節清單。
        ChapterInfo 必須包含：title, url
        """

    @abstractmethod
    def get_content(self, chapter_url: str) -> str:
        """
        爬取單一章節內文，回傳純文字（已去除 HTML 標籤）。
        """
