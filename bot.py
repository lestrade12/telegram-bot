import os
import sqlite3
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ================== НАСТРОЙКИ ==================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1670884870  # твой Telegram ID

NAME, PHONE = range(2)

# ================== БАЗА ДАННЫХ ==================

def init_db():
    conn = sqlite3.connect("applications.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            name TEXT,
            phone TEXT,
            telegram_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

# ================== КОМАНДЫ ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📋 Услуги", "📞 Оставить заявку"],
        ["ℹ️ Контакты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Здравствуйте! 👋\n"
        "Я универсальный бизнес-бот.\n"
        "Выберите действие 👇",
        reply_markup=reply_markup
    )

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Наши услуги:\n"
        "1️⃣ Консультация\n"
        "2️⃣ Разработка\n"
        "3️⃣ Поддержка"
    )

async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Телефон: +998 XX XXX XX XX\n"
        "📧 Email: example@mail.com"
    )

# ================== ЗАЯВКА ==================

async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Как вас зовут?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введите ваш номер телефона 📱")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data["name"]
    phone = update.message.text
    user_id = update.message.from_user.id
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("applications.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO applications (created_at, name, phone, telegram_id) VALUES (?, ?, ?, ?)",
        (date, name, phone, user_id)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ Заявка принята!\n\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n\n"
        "Мы скоро с вами свяжемся 👍"
    )

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Заявка отменена.")
    return ConversationHandler.END

# ================== АДМИН ==================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Доступ запрещён")
        return

    conn = sqlite3.connect("applications.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT created_at, name, phone
        FROM applications
        ORDER BY id DESC
        LIMIT 5
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📭 Заявок пока нет.")
        return

    text = "📋 Последние заявки:\n\n"
    for created_at, name, phone in rows:
        text += (
            f"🕒 {created_at}\n"
            f"👤 {name}\n"
            f"📞 {phone}\n"
            f"———\n"
        )

    await update.message.reply_text(text)

# ================== УМНЫЕ ОТВЕТЫ ==================

async def smart_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "цена" in text or "стоимость" in text:
        await update.message.reply_text(
            "💰 Стоимость зависит от задачи.\n"
            "Оставьте заявку, и мы свяжемся с вами."
        )
    elif "где" in text or "адрес" in text:
        await update.message.reply_text(
            "📍 Мы находимся в Ташкенте.\n"
            "Также работаем онлайн."
        )
    else:
        await update.message.reply_text(
            "🤖 Я не совсем понял.\n"
            "Пожалуйста, используйте кнопки или оставьте заявку."
        )

# ================== ЗАПУСК ==================

def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📞 Оставить заявку$"), start_application)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.Regex("^📋 Услуги$"), services))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Контакты$"), contacts))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_reply))

    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
