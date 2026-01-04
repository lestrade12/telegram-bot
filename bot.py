import logging
import os
import sqlite3
from datetime import datetime
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

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



TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения")

ADMIN_ID = 1670884870
BTN_SERVICES = "📋 Услуги"
BTN_APPLICATION = "📞 Оставить заявку"
BTN_CONTACTS = "ℹ️ Контакты"









from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)



NAME, PHONE = range(2)

# ---------- START ----------
def start(update: Update, context: CallbackContext): 


    keyboard = [
    [BTN_SERVICES, BTN_APPLICATION],
    [BTN_CONTACTS]
]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "Здравствуйте! 👋\n"
        "Я универсальный бизнес-бот.\n"
        "Выберите действие 👇",
        reply_markup=reply_markup
    )

# ---------- КНОПКИ ----------
def services(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Наши услуги:\n"
        "1️⃣ Консультация\n"
        "2️⃣ Разработка\n"
        "3️⃣ Поддержка"
    )

def contacts(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📞 Телефон: +998 XX XXX XX XX\n"
        "📧 Email: example@mail.com"
    )

# ---------- ЗАЯВКА ----------
def start_application(update: Update, context: CallbackContext):
    context.chat_data["in_application"] = True  # 🔒 флаг
    update.message.reply_text("Как вас зовут?")
    return NAME

def get_name(update: Update, context: CallbackContext):
    context.user_data["name"] = update.message.text
    update.message.reply_text("Введите ваш номер телефона 📱")
    return PHONE

def get_phone(update: Update, context: CallbackContext):
    try:
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

        update.message.reply_text(
            "✅ Заявка принята!\n\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n\n"
            "Мы скоро с вами свяжемся 👍"
        )

        context.chat_data["in_application"] = False
        context.user_data.clear()

        return ConversationHandler.END

    except Exception as e:
        logger.exception("Ошибка в get_phone")


        update.message.reply_text(
            "⚠️ Произошла ошибка.\n"
            "Пожалуйста, попробуйте позже или напишите нам напрямую."
        )

        context.chat_data["in_application"] = False
        context.user_data.clear()

        return ConversationHandler.END



def cancel(update: Update, context: CallbackContext):
    context.chat_data["in_application"] = False
    context.user_data.clear()
    update.message.reply_text("Заявка отменена.")
    return ConversationHandler.END  
    
def admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        update.message.reply_text("⛔ Доступ запрещён")
        return  # 🔴 ОЧЕНЬ ВАЖНО


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
        update.message.reply_text("📭 Заявок пока нет.")
        return

    text = "📋 Последние заявки:\n\n"
    for created_at, name, phone in rows:
        text += (
            f"🕒 {created_at}\n"
            f"👤 {name}\n"
            f"📞 {phone}\n"
            f"———\n"
        )

    update.message.reply_text(text)






# ---------- УМНЫЕ ОТВЕТЫ ----------
def smart_reply(update: Update, context: CallbackContext):
    # ❗ ЕСЛИ ИДЁТ ЗАЯВКА — МОЛЧИМ
    if context.chat_data.get("in_application"):
        return

    text = update.message.text.lower()

    if "цена" in text or "стоимость" in text:
        update.message.reply_text(
            "💰 Стоимость зависит от задачи.\n"
            "Оставьте заявку, и мы свяжемся с вами."
        )

    elif "где" in text or "адрес" in text:
        update.message.reply_text(
            "📍 Мы находимся в Ташкенте.\n"
            "Также работаем онлайн."
        )

    elif "график" in text or "время" in text:
        update.message.reply_text(
            "⏰ График работы:\n"
            "Пн–Сб: 9:00–18:00"
        )

    else:
        update.message.reply_text(
            "🤖 Я не совсем понял.\n"
            "Пожалуйста, используйте кнопки или оставьте заявку."
        )

# ---------- НАСТРОЙКА ----------
init_db()
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

conv_handler = ConversationHandler(
   entry_points=[
    MessageHandler(Filters.regex(f"^{BTN_APPLICATION}$"), start_application)
]
,
    states={
        NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
        PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

dp.add_handler(CommandHandler("start", start))  
dp.add_handler(CommandHandler("admin", admin))

dp.add_handler(MessageHandler(Filters.text(BTN_SERVICES), services))
dp.add_handler(MessageHandler(Filters.text(BTN_CONTACTS), contacts))


dp.add_handler(conv_handler)

dp.add_handler(MessageHandler(Filters.text & ~Filters.command, smart_reply))

def main():
    logger.info("Бот запущен")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()


