import os
import logging
import feedparser
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── Настройка логов ──────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Токены и настройки ───────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = None  # используем update.effective_chat.id для каждого пользователя

if not TELEGRAM_TOKEN:
    logger.error("❌ Не задан TELEGRAM_TOKEN")
    exit(1)

# ── Главное меню ─────────────────────────────────────────────────────────────
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["💻 Удалённая работа", "📦 Подработка на выходных"],
        ["🎨 Дизайнер / Фронтенд", "📞 Менеджер по продажам"],
        ["🚗 Курьер / Водитель", "💡 Другая профессия"],
    ],
    resize_keyboard=True,
)

# ── RSS источники вакансий ───────────────────────────────────────────────────
RSS_SOURCES = {
    "💻 Удалённая работа": [
        "https://hh.ru/rss/vacancies?text=Python+remote&area=1",
        "https://www.superjob.ru/rss/vacancies.xml?keywords=Python+remote"
    ],
    "📦 Подработка на выходных": [
        "https://hh.ru/rss/vacancies?text=подработка&area=1"
    ],
    "🎨 Дизайнер / Фронтенд": [
        "https://hh.ru/rss/vacancies?text=designer&area=1"
    ],
    "📞 Менеджер по продажам": [
        "https://hh.ru/rss/vacancies?text=менеджер+по+продажам&area=1"
    ],
    "🚗 Курьер / Водитель": [
        "https://hh.ru/rss/vacancies?text=курьер&area=1"
    ],
    "💡 Другая профессия": [
        "https://hh.ru/rss/vacancies?text=vacancy&area=1"
    ],
}

# ── Получение вакансий из RSS ────────────────────────────────────────────────
def get_vacancies(category: str, limit: int = 5):
    urls = RSS_SOURCES.get(category, [])
    vacancies = []
    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            salary = entry.get("salary", "не указана")
            vacancies.append(f"💼 {entry.title}\n💰 {salary}\n🔗 {entry.link}")
    return vacancies

# ── Handlers ──────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я *JobBot* — помогаю найти работу и подработку.\n\n"
        "Выберите категорию вакансий или напишите что ищете:",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )

async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔄 Диалог сброшен. Выберите категорию или напишите запрос:",
        reply_markup=MAIN_KEYBOARD,
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Как пользоваться JobBot:*\n\n"
        "Выберите категорию вакансий или напишите запрос вручную, например:\n"
        "• «удалённая работа Python»\n"
        "• «подработка курьером в Москве»\n\n"
        "*Команды:*\n"
        "/start — начать заново\n"
        "/reset — сбросить диалог\n"
        "/help — справка",
        parse_mode="Markdown",
    )

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.chat.send_action("typing")

    # Если пользователь выбрал категорию с клавиатуры
    if text in RSS_SOURCES:
        vacancies = get_vacancies(text)
        if not vacancies:
            await update.message.reply_text("⚠️ Вакансий пока нет. Попробуйте позже.")
            return
        for v in vacancies:
            await update.message.reply_text(v)
    else:
        await update.message.reply_text(
            "⚠️ Я пока могу показывать вакансии только по готовым категориям."
        )

# ── Запуск ────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ JobBot (RSS) запущен! Нажмите Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
