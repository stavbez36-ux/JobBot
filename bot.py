import os
import logging
import feedparser
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    logger.error("❌ Нет TELEGRAM_TOKEN")
    exit(1)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["💻 Удалёнка", "📦 Подработка"],
        ["🎨 Дизайнер", "📞 Продажи"],
        ["🚗 Курьер", "💡 Другое"],
    ],
    resize_keyboard=True,
)

def search_vacancies(query: str, limit: int = 5):
    url = f"https://hh.ru/rss/vacancies?text={query}&area=1"
    feed = feedparser.parse(url)

    results = []

    for entry in feed.entries[:limit]:
        title = entry.title
        link = entry.link
        results.append(f"💼 {title}\n🔗 {link}")

    return results


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Я JobBot\n\nНапиши профессию или выбери кнопку 👇",
        reply_markup=MAIN_KEYBOARD
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Напиши что ищешь:\n"
        "• python\n"
        "• дизайнер\n"
        "• курьер\n"
        "И я найду вакансии"
    )


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.chat.send_action("typing")

    query = text.replace(" ", "+")

    vacancies = search_vacancies(query)

    if not vacancies:
        await update.message.reply_text("⚠️ Пока нет вакансий по запросу. Попробуй другое слово.")
        return

    for v in vacancies:
        await update.message.reply_text(v)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ JobBot запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
