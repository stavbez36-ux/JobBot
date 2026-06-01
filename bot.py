import os
import logging
import urllib.request
import urllib.parse
import feedparser

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── LOGS ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_TOKEN не задан")
    exit(1)

# ── КЛАВИАТУРА ───────────────────────────────────────
KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Python", "Designer"],
        ["Frontend", "Backend"],
        ["Курьер", "Менеджер"],
        ["Удалёнка", "Подработка"],
    ],
    resize_keyboard=True
)

# ── RSS ИСТОЧНИКИ (СТАБИЛЬНЫЕ) ──────────────────────
def build_urls(query: str):
    q = urllib.parse.quote(query)

    return [
        f"https://hh.ru/rss/vacancies?text={q}&area=1",
        f"https://www.superjob.ru/rss/vacancies.xml?keywords={q}",
    ]

# ── ПОИСК ВАКАНСИЙ ───────────────────────────────────
def search_vacancies(query: str, limit: int = 5):
    urls = build_urls(query)

    results = []

    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            data = urllib.request.urlopen(req, timeout=10).read()
            feed = feedparser.parse(data)

            for entry in feed.entries[:limit]:
                results.append(
                    f"💼 {entry.title}\n🔗 {entry.link}"
                )

        except Exception as e:
            logger.error(f"RSS error: {e}")
            logger.error(f"URL was: {url}")
    return results[:limit]

# ── HANDLERS ────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *JobBot 3.0 запущен!*\n\n"
        "Напиши профессию или выбери кнопку 👇",
        parse_mode="Markdown",
        reply_markup=KEYBOARD
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Напиши, что ищешь:\n"
        "Python\nDesigner\nFrontend\nBackend\nКурьер\nУдалёнка"
    )

async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.chat.send_action("typing")

    results = search_vacancies(text)

    if not results:
        await update.message.reply_text(
            "⚠️ Вакансии не найдены.\nПопробуй другое слово или английский вариант (Python, Driver, Sales)"
        )
        return

    for r in results:
        await update.message.reply_text(r)

# ── START ───────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    logger.info("✅ JobBot 3.0 запущен (FINAL)")
    app.run_polling()

if __name__ == "__main__":
    main()
