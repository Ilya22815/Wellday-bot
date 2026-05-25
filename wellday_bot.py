import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ── НАСТРОЙКИ ──────────────────────────────────────────────
BOT_TOKEN = "8962401930:AAEskSZRbSF3UThF7OebkYLBZZgUwRb4u_s"
OWNER_ID = 8819726375  # Твой Telegram ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── ПРИВЕТСТВИЕ ────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "Здравствуйте"

    keyboard = [
        [InlineKeyboardButton("💆 Что такое Wellday?", callback_data="about")],
        [InlineKeyboardButton("💰 Стоимость", callback_data="price")],
        [InlineKeyboardButton("📋 Как это работает?", callback_data="how")],
        [InlineKeyboardButton("🎁 Записаться на пробный день", callback_data="trial")],
        [InlineKeyboardButton("📞 Связаться с нами", callback_data="contact")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Привет, {name}! 👋\n\n"
        f"Добро пожаловать в *Wellday* — профессиональный корпоративный массаж для вашей команды.\n\n"
        f"Мы приезжаем к вам в офис раз в неделю и проводим полноценные сеансы массажа по 60 минут прямо в рабочее время. "
        f"Ваши сотрудники не теряют личное время — всё происходит в офисе.\n\n"
        f"Выберите что вас интересует:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    # Уведомление владельцу
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"🔔 Новый пользователь!\n"
             f"Имя: {user.full_name}\n"
             f"Username: @{user.username or 'нет'}\n"
             f"ID: {user.id}"
    )

# ── КНОПКИ ─────────────────────────────────────────────────
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    back_button = [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
    back_markup = InlineKeyboardMarkup(back_button)

    if query.data == "about":
        await query.edit_message_text(
            "💆 *О сервисе Wellday*\n\n"
            "Wellday — это корпоративный массаж для офисных сотрудников.\n\n"
            "8 часов за столом разрушают спину и шею. Хронический стресс снижает продуктивность и увеличивает больничные.\n\n"
            "*Мы решаем это просто:*\n"
            "• Приезжаем к вам в офис раз в неделю\n"
            "• Проводим сеансы по 60 минут на кушетке\n"
            "• Всё оборудование привозим сами\n"
            "• Сотрудники записываются как на обычную встречу\n\n"
            "Сертифицированный специалист с опытом работы с офисными патологиями.",
            parse_mode="Markdown",
            reply_markup=back_markup
        )

    elif query.data == "price":
        keyboard = [
            [InlineKeyboardButton("🎁 Хочу пробный день", callback_data="trial")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")],
        ]
        await query.edit_message_text(
            "💰 *Стоимость*\n\n"
            "📦 *Старт* — 50 000 ₽/мес\n"
            "4 выезда · до 4 сеансов в день · первый месяц\n\n"
            "⭐ *Стандарт* — 70 000 ₽/мес\n"
            "4 выезда · до 6 сеансов в день · гибкий график\n\n"
            "🔥 *Расширенный* — по запросу\n"
            "8–12 выездов в месяц · приоритетное расписание\n\n"
            "_Первый пробный день — бесплатно!_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "how":
        await query.edit_message_text(
            "📋 *Как это работает?*\n\n"
            "*1.* Короткий созвон — 20 минут\n"
            "Обсуждаем формат, день недели, количество сотрудников\n\n"
            "*2.* Пробный день бесплатно\n"
            "Приезжаем, проводим 3–4 сеанса. Команда оценивает — вы решаете\n\n"
            "*3.* Подписываем договор\n"
            "Простой договор на оздоровительные услуги\n\n"
            "*4.* Еженедельные выезды\n"
            "Сотрудники записываются сами. Вам нужна только переговорка",
            parse_mode="Markdown",
            reply_markup=back_markup
        )

    elif query.data == "trial":
        await query.edit_message_text(
            "🎁 *Записаться на пробный день*\n\n"
            "Отлично! Первый день — бесплатно.\n\n"
            "Напишите нам:\n"
            "• Название вашей компании\n"
            "• Количество сотрудников\n"
            "• Удобное время для созвона\n\n"
            "Мы свяжемся с вами в течение дня и договоримся о дате! 🤝",
            parse_mode="Markdown",
            reply_markup=back_markup
        )
        # Уведомление владельцу
        user = update.effective_user
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"🔥 Хочет записаться на пробный день!\n"
                 f"Имя: {user.full_name}\n"
                 f"Username: @{user.username or 'нет'}\n"
                 f"ID: {user.id}\n\n"
                 f"Напиши ему: tg://user?id={user.id}"
        )

    elif query.data == "contact":
        await query.edit_message_text(
            "📞 *Связаться с нами*\n\n"
            "📱 Телефон: +7-977-697-90-12\n"
            "📧 Email: WellDay365@yandex.ru\n"
            "🌐 Сайт: well-day.ru\n\n"
            "Или просто напишите сообщение прямо здесь — мы ответим в течение дня!",
            parse_mode="Markdown",
            reply_markup=back_markup
        )

    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("💆 Что такое Wellday?", callback_data="about")],
            [InlineKeyboardButton("💰 Стоимость", callback_data="price")],
            [InlineKeyboardButton("📋 Как это работает?", callback_data="how")],
            [InlineKeyboardButton("🎁 Записаться на пробный день", callback_data="trial")],
            [InlineKeyboardButton("📞 Связаться с нами", callback_data="contact")],
        ]
        await query.edit_message_text(
            "Выберите что вас интересует:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ── СВОБОДНЫЕ СООБЩЕНИЯ ────────────────────────────────────
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # Пересылаем владельцу
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"💬 Новое сообщение!\n"
             f"От: {user.full_name} (@{user.username or 'нет'})\n"
             f"ID: {user.id}\n\n"
             f"Текст: {text}\n\n"
             f"Ответить: tg://user?id={user.id}"
    )

    keyboard = [[InlineKeyboardButton("📋 Главное меню", callback_data="back")]]
    await update.message.reply_text(
        "Спасибо за сообщение! 🙏\n\n"
        "Мы получили его и свяжемся с вами в течение дня.\n\n"
        "Или выберите раздел в меню:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ── ЗАПУСК ─────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
