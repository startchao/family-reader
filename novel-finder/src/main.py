"""
main.py — Novel Finder Bot 主程式
使用 python-telegram-bot v20（全 async）。
執行方式：python novel-finder/src/main.py
環境變數：TELEGRAM_TOKEN、TELEGRAM_CHAT_ID
"""
import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# 調整 import 路徑，使 src/ 底下的模組可互相引用
sys.path.insert(0, str(Path(__file__).parent))

from sources.source_69 import Source69
from utils.cleaner import remove_duplicate_title
from utils.telegram import send_message, send_file

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 對話狀態
# ------------------------------------------------------------------
IDLE = 0
WAIT_BOOK_CHOICE = 1
DOWNLOADING = 2

# ------------------------------------------------------------------
# 支援的分類
# ------------------------------------------------------------------
VALID_CATEGORIES = {"玄幻", "仙俠", "都市", "穿越", "歷史", "懸疑"}

# ------------------------------------------------------------------
# 全域書源
# ------------------------------------------------------------------
source = Source69()


# ------------------------------------------------------------------
# /start
# ------------------------------------------------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "👋 歡迎使用小說搜尋下載器！\n\n"
        "📋 指令說明：\n"
        "• 直接輸入書名 → 搜尋\n"
        "• /hot → 綜合熱門榜 Top 20\n"
        "• /hot 玄幻 → 指定分類榜單\n"
        "  支援分類：玄幻、仙俠、都市、穿越、歷史、懸疑\n\n"
        "搜尋結果出現後，輸入對應編號即可下載 TXT。"
    )
    await update.message.reply_text(text)
    return IDLE


# ------------------------------------------------------------------
# /hot [分類]
# ------------------------------------------------------------------
async def cmd_hot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    args = context.args
    category = args[0] if args else ""

    if category and category not in VALID_CATEGORIES:
        await update.message.reply_text(
            f"❌ 不支援的分類「{category}」\n"
            f"支援：{', '.join(VALID_CATEGORIES)}"
        )
        return IDLE

    label = f"【{category}】" if category else "【綜合】"
    await update.message.reply_text(f"🔍 正在抓取 {label} 熱門榜單，請稍候…")

    try:
        books = source.get_rank(category)
    except Exception as e:
        logger.error("get_rank error: %s", e)
        await update.message.reply_text("❌ 抓取榜單失敗，請稍後再試。")
        return IDLE

    if not books:
        await update.message.reply_text("⚠️ 榜單為空，可能網站結構已更新。")
        return IDLE

    lines = [f"🔥 熱門榜單 {label} Top {len(books)}\n"]
    for b in books:
        author = f"（{b['author']}）" if b.get("author") else ""
        lines.append(f"{b['id']:2}. {b['title']}{author}")

    await send_message(
        context.bot,
        str(update.effective_chat.id),
        "\n".join(lines),
    )
    return IDLE


# ------------------------------------------------------------------
# 搜尋（一般文字輸入 → WAIT_BOOK_CHOICE）
# ------------------------------------------------------------------
async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyword = update.message.text.strip()
    await update.message.reply_text(f"🔍 正在搜尋「{keyword}」，請稍候…")

    try:
        books = source.search(keyword)
    except Exception as e:
        logger.error("search error: %s", e)
        await update.message.reply_text("❌ 搜尋失敗，請稍後再試。")
        return IDLE

    if not books:
        await update.message.reply_text("⚠️ 找不到相關書籍，請換個關鍵字試試。")
        return IDLE

    # 儲存搜尋結果到 user_data
    context.user_data["search_results"] = books

    lines = [f"📚 找到 {len(books)} 筆結果，請輸入編號選擇：\n"]
    for b in books:
        author = f" / {b['author']}" if b.get("author") else ""
        latest = f" [{b['latest_chapter']}]" if b.get("latest_chapter") else ""
        lines.append(f"{b['id']:2}. {b['title']}{author}{latest}")

    lines.append("\n輸入編號開始下載，或輸入其他書名重新搜尋。")
    await send_message(
        context.bot,
        str(update.effective_chat.id),
        "\n".join(lines),
    )
    return WAIT_BOOK_CHOICE


# ------------------------------------------------------------------
# 選擇書籍編號 → 開始下載
# ------------------------------------------------------------------
async def handle_book_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()

    if not text.isdigit():
        # 不是數字 → 視為新的搜尋關鍵字
        return await handle_search(update, context)

    choice = int(text)
    books = context.user_data.get("search_results", [])
    book = next((b for b in books if b["id"] == choice), None)

    if not book:
        await update.message.reply_text(f"❌ 無效的編號，請輸入 1～{len(books)} 之間的數字。")
        return WAIT_BOOK_CHOICE

    await update.message.reply_text(
        f"📖 已選擇：《{book['title']}》\n⏳ 開始下載，請耐心等候（章節數多時需要較長時間）…"
    )

    try:
        await _download_and_send(update, context, book)
    except Exception as e:
        logger.error("download error: %s", e)
        await update.message.reply_text(f"❌ 下載過程發生錯誤：{e}")

    # 清除搜尋結果，回到 IDLE
    context.user_data.pop("search_results", None)
    return IDLE


# ------------------------------------------------------------------
# 下載核心邏輯
# ------------------------------------------------------------------
async def _download_and_send(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    book: Dict[str, Any],
) -> None:
    chat_id = str(update.effective_chat.id)

    # 取得章節列表
    await send_message(context.bot, chat_id, "📋 正在解析章節目錄…")
    chapters = source.get_chapters(book["url"])

    if not chapters:
        await send_message(context.bot, chat_id, "⚠️ 找不到章節資料，可能需要登入或網站已更新。")
        return

    await send_message(context.bot, chat_id, f"📝 共 {len(chapters)} 章，開始逐章下載…")

    # 逐章爬取並寫入暫存檔
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    ) as f:
        tmp_path = f.name
        title = book["title"]
        author = book.get("author", "")
        f.write(f"書名：{title}\n")
        if author:
            f.write(f"作者：{author}\n")
        f.write("\n" + "=" * 40 + "\n\n")

        for idx, chapter in enumerate(chapters, start=1):
            try:
                content = source.get_content(chapter["url"])
                content = remove_duplicate_title(content, chapter["title"])
            except Exception as e:
                logger.warning("Failed to get chapter %s: %s", chapter["title"], e)
                content = "（本章內容獲取失敗）"

            f.write(f"\n{chapter['title']}\n\n")
            f.write(content)
            f.write("\n\n")

            # 每 50 章回報一次進度
            if idx % 50 == 0:
                await send_message(
                    context.bot, chat_id, f"⏳ 已下載 {idx}/{len(chapters)} 章…"
                )

    # 傳送檔案
    safe_title = title.replace("/", "_").replace("\\", "_")
    filename = f"{safe_title}.txt"
    dest_path = str(Path(tmp_path).parent / filename)
    Path(tmp_path).rename(dest_path)

    await send_message(context.bot, chat_id, "✅ 下載完成！正在傳送檔案…")
    await send_file(
        context.bot,
        chat_id,
        dest_path,
        caption=f"《{title}》完整版",
    )

    # 清理暫存檔
    try:
        os.unlink(dest_path)
    except OSError:
        pass


# ------------------------------------------------------------------
# /cancel
# ------------------------------------------------------------------
async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("❎ 已取消。輸入書名重新搜尋，或 /hot 查看榜單。")
    return IDLE


# ------------------------------------------------------------------
# 超時自動關閉（讓 GitHub Actions job 能正常結束）
# ------------------------------------------------------------------
BOT_LIFETIME_SECONDS = int(os.environ.get("BOT_LIFETIME_SECONDS", "1200"))  # 預設 20 分鐘


async def _shutdown_timer(application: Application) -> None:
    await asyncio.sleep(BOT_LIFETIME_SECONDS)
    logger.info("Bot lifetime reached %d seconds, shutting down.", BOT_LIFETIME_SECONDS)
    await application.stop()


# ------------------------------------------------------------------
# 主程式
# ------------------------------------------------------------------
def main() -> None:
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN environment variable is not set.")
        sys.exit(1)

    application = (
        ApplicationBuilder()
        .token(token)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            CommandHandler("hot", cmd_hot),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search),
        ],
        states={
            IDLE: [
                CommandHandler("hot", cmd_hot),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search),
            ],
            WAIT_BOOK_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_book_choice),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    async def post_init(app: Application) -> None:
        asyncio.ensure_future(_shutdown_timer(app))

    application.post_init = post_init

    logger.info("Bot started. Will run for %d seconds.", BOT_LIFETIME_SECONDS)
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
