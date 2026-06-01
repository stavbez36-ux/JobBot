import os
import logging
import urllib.request
import urllib.parse
import json

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_TOKEN не задан")
    exit(1)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Python", "Designer"],
        ["Frontend", "Backend"],
        ["Курьер", "Менеджер"],
    ],
    resize_keyboard=True,
)

# ── HH API (СТАБИЛЬНО) ─────────────────────────────
def search_hh(query: str, limit: int = 5):
    encoded = urllib.parse.quote(query)

    url = f"https://api.hh.ru/vacancies?text={encoded}&per_page={limit}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    try:
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read().decode("utf-8"))

        results = []

        for item in data.get("items", []):
            title = item.get("name")
            company = item.get("employer", {}).get("name", "Неизвестно")
            link = item.get("alternate_url")

            results.append(
                f"💼 {title}\n🏢 {company}\n🔗 {link}"
            )

        return results

    except Exception as e:
        logger.error(f"HH API error: {e}")
        return []


# ── Telegram handlers ─────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 JobBot 2.0 запущен!\n\nНапиши профессию:",
        reply_markup=MAIN_KEYBOARD
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто напиши:\n"
        "Python\nDesigner\nFrontend\nBackend\nКурьер"
    )


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.chat.send_action("typing")

    results = search_hh(text)

    if not results:
        await update.message.reply_text(
            "⚠️ Вакансий не найдено. Попробуй другое слово."
        )
        return

    for r in results:
        await update.message.reply_text(r)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    logger.info("✅ JobBot 2.0 запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
