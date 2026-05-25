import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8962401930:AAEskSZRbSF3UThF7OebkYLBZZgUwRb4u_s"
OWNER_ID = 8819726375

logging.basicConfig(level=logging.INFO)

MAIN_KEYBOARD = [
    [InlineKeyboardButton("💆 Что такое Wellday?", callback_data="about")],
    [InlineKeyboardButton("💰 Стоимость", callback_data="price")],
    [InlineKeyboardButton("📋 Как это работает?", callback_data="how")],
    [InlineKeyboardButton("🎁 Записаться на пробный день", callback_data="trial")],
    [InlineKeyboardButton("📞 Связаться с нами", callback_data="contact")],
]
BACK_KEYBOARD = [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Добро пожаловать в *Wellday* — профессиональный корпоративный массаж для вашей команды.\n\n"
        "Мы приезжаем в офис раз в неделю и проводим сеансы по 60 минут прямо в рабочее время. "
        "Сотрудники не теряют личное время — всё в офисе.\n\n"
        "Выберите что вас интересует:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(MAIN_KEYBOARD)
    )
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"🔔 Новый пользователь!\nИмя: {user.full_name}\nUsername: @{user.username or 'нет'}\nID: {user.id}"
        )
    except:
        pass

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "about":
        await query.edit_message_text(
            "💆 *О сервисе Wellday*\n\n"
            "8 часов за столом разрушают спину и шею. Хронический стресс снижает продуктивность.\n\n"
            "*Мы решаем это просто:*\n"
            "• Приезжаем в офис раз в неделю\n"
            "• Сеансы 60 минут на кушетке\n"
            "• Всё оборудование привозим сами\n"
            "• Сотрудники записываются как на встречу\n\n"
            "Сертифицированный специалист с опытом работы с офисными патологиями.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(BACK_KEYBOARD)
        )
    elif data == "price":
        await query.edit_message_text(
            "💰 *Стоимость*\n\n"
            "📦 *Старт* — 50 000 ₽/мес\n"
            "4 выезда · до 4 сеансов в день · первый месяц\n\n"
            "⭐ *Стандарт* — 70 000 ₽/мес\n"
            "4 выезда · до 6 сеансов в день\n\n"
            "🔥 *Расширенный* — по запросу\n"
            "8–12 выездов в месяц\n\n"
            "_Первый пробный день — бесплатно!_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Хочу пробный день", callback_data="trial")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back")],
            ])
        )
    elif data == "how":
        await query.edit_message_text(
            "📋 *Как это работает?*\n\n"
            "*1.* Короткий созвон — 20 минут\n"
            "*2.* Пробный день бесплатно\n"
            "*3.* Подписываем договор\n"
            "*4.* Еженедельные выезды\n\n"
            "Вам нужна только переговорка — всё остальное привозим сами.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(BACK_KEYBOARD)
        )
    elif data == "trial":
        user = update.effective_user
        await query.edit_message_text(
            "🎁 *Записаться на пробный день*\n\n"
            "Первый день — бесплатно!\n\n"
            "Напишите нам:\n"
            "• Название компании\n"
            "• Количество сотрудников\n"
            "• Удобное время для созвона\n\n"
            "Свяжемся в течение дня! 🤝",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(BACK_KEYBOARD)
        )
        try:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"🔥 Хочет записаться!\nИмя: {user.full_name}\nUsername: @{user.username or 'нет'}\nID: {user.id}"
            )
        except:
            pass
    elif data == "contact":
        await query.edit_message_text(
            "📞 *Связаться с нами*\n\n"
            "📱 Телефон: +7-977-697-90-12\n"
            "📧 Email: WellDay365@yandex.ru\n"
            "🌐 Сайт: well-day.ru\n\n"
            "Или напишите прямо здесь — ответим в течение дня!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(BACK_KEYBOARD)
        )
    elif data == "back":
        await query.edit_message_text(
            "Выберите что вас интересует:",
            reply_markup=InlineKeyboardMarkup(MAIN_KEYBOARD)
        )

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"💬 Сообщение!\nОт: {user.full_name} (@{user.username or 'нет'})\nID: {user.id}\n\nТекст: {text}"
        )
    except:
        pass
    await update.message.reply_text(
        "Спасибо! Получили ваше сообщение и свяжемся в течение дня. 🙏",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 Главное меню", callback_data="back")]])
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    print("Бот запущен!")
    app.run_polling(drop_pending_updates=True)
