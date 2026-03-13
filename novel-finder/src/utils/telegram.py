"""
telegram.py — Telegram API 封裝工具
提供 send_message 與 send_file，統一處理錯誤與大檔案切分。
"""
import asyncio
import os
import time
from pathlib import Path
from typing import Optional

from telegram import Bot
from telegram.error import TelegramError

MAX_FILE_BYTES = 45 * 1024 * 1024  # 45 MB（Telegram 上限 50MB，保留緩衝）
MAX_MESSAGE_LEN = 4096


async def send_message(bot: Bot, chat_id: str, text: str) -> None:
    """
    發送文字訊息。若文字超過 4096 字元自動切分。
    包含 retry 機制（最多 3 次）。
    """
    for chunk in _split_text(text, MAX_MESSAGE_LEN):
        await _retry(bot.send_message, chat_id=chat_id, text=chunk)


async def send_file(
    bot: Bot,
    chat_id: str,
    filepath: str,
    caption: str = "",
) -> None:
    """
    發送 .txt 檔案。若超過 45MB 自動切分多個 Part 傳送。
    """
    path = Path(filepath)
    size = path.stat().st_size

    if size <= MAX_FILE_BYTES:
        with open(filepath, "rb") as f:
            await _retry(
                bot.send_document,
                chat_id=chat_id,
                document=f,
                filename=path.name,
                caption=caption,
            )
    else:
        parts = _split_file(path)
        total = len(parts)
        for idx, (part_path, part_bytes) in enumerate(parts, start=1):
            part_caption = f"{caption} (第 {idx}/{total} 部分)"
            with open(part_path, "rb") as f:
                await _retry(
                    bot.send_document,
                    chat_id=chat_id,
                    document=f,
                    filename=f"{path.stem}_part{idx}.txt",
                    caption=part_caption,
                )
            # 清理暫存分割檔
            os.unlink(part_path)


# ------------------------------------------------------------------
# 內部工具
# ------------------------------------------------------------------

def _split_text(text: str, max_len: int):
    """將長文字切成不超過 max_len 的段落"""
    while text:
        yield text[:max_len]
        text = text[max_len:]


def _split_file(path: Path):
    """
    將大檔案切分為多個不超過 MAX_FILE_BYTES 的部分。
    回傳 [(tmp_path, bytes_written), ...]
    """
    content = path.read_bytes()
    parts = []
    idx = 0
    while idx < len(content):
        chunk = content[idx: idx + MAX_FILE_BYTES]
        tmp_path = str(path.parent / f"_tmp_part_{len(parts)}.txt")
        with open(tmp_path, "wb") as f:
            f.write(chunk)
        parts.append((tmp_path, len(chunk)))
        idx += MAX_FILE_BYTES
    return parts


async def _retry(coro_fn, retries: int = 3, **kwargs):
    """帶指數退避的 async retry"""
    for attempt in range(retries):
        try:
            return await coro_fn(**kwargs)
        except TelegramError as e:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
