import os
import re
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.ext import CommandHandler


# ================== CONFIG ==================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MAX_LINKS = 5
TIKWM_API = "https://www.tikwm.com/api/"
# ============================================


# ========= REGEX DETEKSI LINK TIKTOK =========
TIKTOK_REGEX = r"(https?://(?:www\.)?(?:tiktok\.com|vt\.tiktok\.com)/[^\s]+)"


def extract_tiktok_links(text: str):
    links = re.findall(TIKTOK_REGEX, text)
    return links[:MAX_LINKS]


def safe_title(title: str):
    if not title or title.strip() == "":
        return "Video TikTok"
    return title[:50]


def format_caption(part: int, title: str):
    return f"**Part {part} {title}**"


def fetch_tiktok_data(url: str):
    response = requests.get(
        TIKWM_API,
        params={"url": url},
        timeout=15
    )
    response.raise_for_status()
    return response.json()


def extract_video_info(api_response: dict):
    data = api_response.get("data", {})
    video_url = data.get("play")  # no watermark
    title = data.get("title") or "Video TikTok"
    return video_url, title


# ================= HANDLER ===================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    links = extract_tiktok_links(text)

    if not links:
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"📦 Menemukan {len(links)} link. Menyiapkan batch download..."
    )

    for idx, link in enumerate(links, start=1):
        try:
            api_response = fetch_tiktok_data(link)
            video_url, raw_title = extract_video_info(api_response)

            title = safe_title(raw_title)
            caption = format_caption(idx, title)

            await context.bot.send_video(
                chat_id=chat_id,
                video=video_url,
                caption=caption,
                parse_mode="Markdown"
            )

        except Exception:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Gagal memproses Part {idx}"
            )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Selamat datang di TikTok Batch Downloader\n\n"
        "📥 Cara menggunakan:\n"
        "Kirim beberapa link TikTok dalam 1 pesan\n"
        "(Maksimal 5 link)\n\n"
        "🧾 Contoh format:\n"
        "https://vt.tiktok.com/xxxxxx\n"
        "https://www.tiktok.com/@user/video/yyyyy\n"
        "https://vt.tiktok.com/zzzzzz\n\n"
        "⚙️ Sistem otomatis:\n"
        "• Link ke-1 → Part 1\n"
        "• Link ke-2 → Part 2\n"
        "• Judul dari caption video\n"
        "• Tanpa watermark\n"
        "• Dikirim sebagai video\n\n"
        "🚀 Silakan kirim link TikTok sekarang"
    )
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN belum diset di environment variable")

# ================== MAIN =====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 TikTok Batch Downloader Bot berjalan...")
    app.run_polling()
if __name__ == "__main__":
    main()
