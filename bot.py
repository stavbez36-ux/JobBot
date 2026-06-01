import os
import logging
import urllib.request
import urllib.parse
import feedparser
import json

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


# ── ПОИСК ВАКАНСИЙ ───────────────────────────────────
def search_vacancies(query: str, limit: int = 5):
    q = urllib.parse.quote(query)
    url = f"https://api.hh.ru/vacancies?text={q}&per_page={limit}&area=113"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "JobBot/1.0 (job search telegram bot)"}
        )
        data = urllib.request.urlopen(req, timeout=10).read()
        parsed = json.loads(data)
        logger.info(f"HH ответ: {str(parsed)[:500]}")
        items = parsed.get("items", [])
        results = []
        for v in items:
            name = v.get("name", "—")
            employer = v.get("employer", {}).get("name", "—")
            salary = v.get("salary")
            link = v.get("alternate_url", "—")
            if salary:
                sal = f"{salary.get('from', '')}–{salary.get('to', '')} {salary.get('currency', '')}".strip("–")
            else:
                sal = "не указана"
            results.append(f"💼 {name}\n🏢 {employer}\n💰 {sal}\n🔗 {link}")
        return results
    except Exception as e:
        logger.error(f"HH API error: {e}")
        return []

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
    logger.info(f"Получен запрос: {text}")
    await update.message.chat.send_action("typing")
    results = search_vacancies(text)
    logger.info(f"Найдено вакансий: {len(results)}")

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

