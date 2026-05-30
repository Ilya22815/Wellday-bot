import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

BOT_TOKEN = "8962401930:AAEskSZRbSF3UThF7OebkYLBZZgUwRb4u_s"
OWNER_ID = 8819726375

logging.basicConfig(level=logging.INFO)

MAIN_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("💆 Что такое Wellday?", callback_data="about")],
    [InlineKeyboardButton("💰 Стоимость", callback_data="price")],
    [InlineKeyboardButton("📋 Как это работает?", callback_data="how")],
    [InlineKeyboardButton("🎁 Записаться на пробный день", callback_data="trial")],
    [InlineKeyboardButton("📞 Связаться с нами", callback_data="contact")],
])
BACK_KEYBOARD = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]])

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Добро пожаловать в *Wellday* — корпоративный массаж для вашей команды.\n\n"
        "Приезжаем в офис раз в неделю, сеансы 60 минут прямо в рабочее время.\n\n"
        "Выберите что вас интересует:",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD
    )
    try:
        context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"🔔 Новый пользователь!\nИмя: {user.full_name}\nUsername: @{user.username or 'нет'}\nID: {user.id}"
        )
    except:
        pass

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == "about":
        query.edit_message_text(
            "💆 *О сервисе Wellday*\n\n"
            "8 часов за столом разрушают спину и шею.\n\n"
            "*Мы решаем это просто:*\n"
            "• Приезжаем в офис раз в неделю\n"
            "• Сеансы 60 минут на кушетке\n"
            "• Всё оборудование привозим сами\n"
            "• Сотрудники записываются как на встречу",
            parse_mode="Markdown",
            reply_markup=BACK_KEYBOARD
        )
    elif data == "price":
        query.edit_message_text(
            "💰 *Стоимость*\n\n"
            "📦 *Старт* — 50 000 ₽/мес\n"
            "4 выезда · до 4 сеансов в день\n\n"
            "⭐ *Стандарт* — 70 000 ₽/мес\n"
            "4 выезда · до 6 сеансов в день\n\n"
            "🔥 *Расширенный* — по запросу\n\n"
            "_Первый пробный день — бесплатно!_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Хочу пробный день", callback_data="trial")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back")],
            ])
        )
    elif data == "how":
        query.edit_message_text(
            "📋 *Как это работает?*\n\n"
            "*1.* Короткий созвон 20 минут\n"
            "*2.* Пробный день бесплатно\n"
            "*3.* Подписываем договор\n"
            "*4.* Еженедельные выезды\n\n"
            "Вам нужна только переговорка!",
            parse_mode="Markdown",
            reply_markup=BACK_KEYBOARD
        )
    elif data == "trial":
        user = update.effective_user
        query.edit_message_text(
            "🎁 *Записаться на пробный день*\n\n"
            "Первый день — бесплатно!\n\n"
            "Напишите нам:\n"
            "• Название компании\n"
            "• Количество сотрудников\n"
            "• Удобное время для созвона\n\n"
            "Свяжемся в течение дня! 🤝",
            parse_mode="Markdown",
            reply_markup=BACK_KEYBOARD
        )
        try:
            context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"🔥 Хочет записаться!\nИмя: {user.full_name}\nUsername: @{user.username or 'нет'}\nID: {user.id}"
            )
        except:
            pass
    elif data == "contact":
        query.edit_message_text(
            "📞 *Связаться с нами*\n\n"
            "📱 Телефон: +7-977-697-90-12\n"
            "📧 Email: info@well-day.ru\n"
            "🌐 Сайт: well-day.ru\n\n"
            "Или напишите прямо здесь!",
            parse_mode="Markdown",
            reply_markup=BACK_KEYBOARD
        )
    elif data == "back":
        query.edit_message_text(
            "Выберите что вас интересует:",
            reply_markup=MAIN_KEYBOARD
        )

def message(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text
    try:
        context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"💬 Сообщение!\nОт: {user.full_name} (@{user.username or 'нет'})\nID: {user.id}\n\nТекст: {text}"
        )
    except:
        pass
    update.message.reply_text(
        "Спасибо! Получили ваше сообщение и свяжемся в течение дня. 🙏",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 Главное меню", callback_data="back")]])
    )

if __name__ == "__main__":
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message))
    print("Бот запущен!")
    updater.start_polling()
    updater.idle()
