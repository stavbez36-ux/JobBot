import os
import logging
import urllib.request
import urllib.parse
import json
import traceback

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── Настройка логов ──────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Токены ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logger.error("❌ Не заданы TELEGRAM_TOKEN или GEMINI_API_KEY")
    logger.error("   Windows PowerShell:")
    logger.error('   $env:TELEGRAM_TOKEN="токен"')
    logger.error('   $env:GEMINI_API_KEY="ключ"')
    logger.error("   py -3.12 bot.py")
    exit(1)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY
)

# ── История диалогов ─────────────────────────────────────────────────────────
conversations: dict[int, list] = {}

SYSTEM_PROMPT = """Ты — дружелюбный бот для поиска работы и подработок JobBot. Отвечаешь на русском языке.

Твои задачи:
1. Помогать пользователям найти вакансии и подработки
2. Искать актуальные вакансии на hh.ru, superjob.ru, rabota.ru, LinkedIn, Indeed, XING, StepStone
3. Для фриланса и подработок — fl.ru, profi.ru, youdo.com, kwork.ru, upwork.com
4. Показывать конкретные результаты: название, компания, зарплата, ссылка
5. Задавать уточняющие вопросы если запрос расплывчатый

Формат вакансий:
💼 Название вакансии
🏢 Компания: название
💰 Зарплата: сумма (если указана)
🔗 Ссылка: url

Показывай 3–5 вакансий за раз. Будь лаконичен и полезен."""

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["💻 Удалённая работа", "📦 Подработка на выходных"],
        ["🎨 Дизайнер / Фронтенд", "📞 Менеджер по продажам"],
        ["🚗 Курьер / Водитель", "💡 Другая профессия"],
    ],
    resize_keyboard=True,
)


# ── Запрос к Gemini ───────────────────────────────────────────────────────────
def ask_gemini(chat_id: int, user_text: str) -> str:
    history = conversations.setdefault(chat_id, [])
    history.append({"role": "user", "parts": [{"text": user_text}]})

    if len(history) > 20:
        del history[: len(history) - 20]

    payload = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": history,
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7},
        "tools": [{"google_search": {}}],
    }).encode("utf-8")

    req = urllib.request.Request(
        GEMINI_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    reply = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "Не удалось получить ответ, попробуйте ещё раз.")
    )

    history.append({"role": "model", "parts": [{"text": reply}]})
    return reply


# ── Handlers ──────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conversations.pop(update.effective_chat.id, None)
    await update.message.reply_text(
        "👋 Привет! Я *JobBot* — помогаю найти работу и подработку.\n\n"
        "Расскажите, что ищете — профессию, город, формат работы "
        "(офис / удалёнка / подработка), желаемую зарплату.\n\n"
        "Или выберите быстрый вариант:",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conversations.pop(update.effective_chat.id, None)
    await update.message.reply_text(
        "🔄 Диалог сброшен. Начнём сначала! Что ищете?",
        reply_markup=MAIN_KEYBOARD,
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Как пользоваться JobBot:*\n\n"
        "Напишите что ищете, например:\n"
        "• «удалённая работа Python-разработчика от 100к»\n"
        "• «подработка курьером в Москве»\n"
        "• «вакансии дизайнера в Берлине»\n\n"
        "*Команды:*\n"
        "/start — начать заново\n"
        "/reset — сбросить диалог\n"
        "/help — справка",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    await update.message.chat.send_action("typing")

    try:
        reply = ask_gemini(chat_id, text)
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "⚠️ Произошла ошибка. Попробуйте ещё раз или /reset"
        )


# ── Запуск ────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ JobBot (Gemini) запущен! Нажмите Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
