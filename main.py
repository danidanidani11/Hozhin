import os
from flask import Flask, request
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

app = Flask(__name__)
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# متن‌ها
about_book = "📖 متن درباره کتاب..."
about_author = "✍️ متن درباره نویسنده..."
suggest_text = "🗣 لطفاً نظراتتان را ارسال کنید."
payment_text = """
💳 شماره کارت: 5859 8311 3314 0268
هزینه کتاب: ۱۱۰ هزار تومان

بعد از پرداخت، عکس یا فایل رسید را همینجا بفرستید.
"""

# کیبورد اصلی
def main_keyboard():
    rows = [
        ["📘 خرید کتاب", "🗣 انتقادات و پیشنهادات"],
        ["📖 درباره کتاب", "✍️ درباره نویسنده"],
        ["🔊 کتاب صوتی (به زودی)"]
    ]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, callback_data=text)] for row in rows for text in row
    ])

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! به ربات کتاب «هوژین حرمان» خوش آمدید 🌿",
        reply_markup=main_keyboard()
    )

# دکمه‌ها
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "📘 خرید کتاب":
        await query.message.reply_text(payment_text)
    elif data == "🗣 انتقادات و پیشنهادات":
        await query.message.reply_text(suggest_text)
    elif data == "📖 درباره کتاب":
        await query.message.reply_text(about_book)
    elif data == "✍️ درباره نویسنده":
        await query.message.reply_text(about_author)
    elif data.startswith("تایید_"):
        user_id = int(data.split("_")[1])
        await bot.send_document(chat_id=user_id, document=InputFile("books/hozhin_harman.pdf"))
        await query.edit_message_text("✅ فیش تایید شد.")
    elif data.startswith("رد_"):
        user_id = int(data.split("_")[1])
        await bot.send_message(chat_id=user_id, text="❌ فیش شما رد شد.")
        await query.edit_message_text("❌ فیش رد شد.")

# رسید کاربران
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    caption = f"📥 فیش جدید از {user.full_name} ({user_id})"
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"تایید_{user_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"رد_{user_id}")
        ]
    ])

    if update.message.photo:
        photo = update.message.photo[-1].file_id
        await bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=caption, reply_markup=markup)
    elif update.message.document:
        file = update.message.document.file_id
        await bot.send_document(chat_id=ADMIN_ID, document=file, caption=caption, reply_markup=markup)
    elif update.message.text:
        await bot.send_message(chat_id=ADMIN_ID, text=caption + "\n\n" + update.message.text, reply_markup=markup)

# هندلرها
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(handle_buttons))
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_user_message))

# Webhook route برای تلگرام
@app.route(f"/{TOKEN}", methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "ok"

# تست صفحه اصلی
@app.route("/")
def index():
    return "ربات هوژین حرمان فعال است."

# اجرای اپلیکیشن
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"https://hozhin.onrender.com/{TOKEN}"
    )
