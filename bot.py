import urllib.request
import urllib.parse
import feedparser

def search_vacancies(query: str, limit: int = 5):
    encoded = urllib.parse.quote(query)

    url = f"https://hh.ru/rss/vacancies?text={encoded}&area=1"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    try:
        response = urllib.request.urlopen(req, timeout=10)
        data = response.read()

        feed = feedparser.parse(data)

        results = []
        for entry in feed.entries[:limit]:
            results.append(f"💼 {entry.title}\n🔗 {entry.link}")

        # если hh пустой — fallback
        if results:
            return results

    except Exception:
        pass

    # fallback (второй источник)
    url2 = f"https://www.superjob.ru/rss/vacancies.xml?keywords={encoded}"
    feed2 = feedparser.parse(url2)

    results2 = []
    for entry in feed2.entries[:limit]:
        results2.append(f"💼 {entry.title}\n🔗 {entry.link}")

    return results2


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
