import os
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

app = Flask(__name__)
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# ===== متن‌ها =====
about_book = """📖 رمان هوژین و حرمان...
(اینجا متن کامل درباره کتاب بذار)"""
about_author = """✍️ سلام رفقا...
(اینجا متن کامل درباره نویسنده بذار)"""
suggest_text = "🗣 اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت کمک کند..."
payment_text = """💳 5859 8311 3314 0268

لطفا فیش را همینجا ارسال کنید. هزینه کتاب ۱۱۰ هزار تومان است.
ممکن است تایید فیش کمی زمان‌بر باشد.
در صورت تایید، فایل PDF برایتان ارسال خواهد شد.
"""

# ===== صفحه اصلی
def get_main_keyboard():
    buttons = [
        ["📘 خرید کتاب", "🗣 انتقادات و پیشنهادات"],
        ["📖 درباره کتاب", "✍️ درباره نویسنده"],
        ["🔊 کتاب صوتی (به زودی)"]
    ]
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text, callback_data=text)] for row in buttons for text in row]
    )

# ===== وب‌هوک
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "ok"

@app.route("/")
def home():
    return "ربات فعال است."

# ===== دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "به ربات هوژین حرمان خوش آمدید 🌿",
        reply_markup=get_main_keyboard()
    )

# ===== کلیک روی دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await query.edit_message_text("✅ فیش تایید شد و فایل ارسال شد.")
    elif data.startswith("رد_"):
        user_id = int(data.split("_")[1])
        await bot.send_message(chat_id=user_id, text="❌ فیش شما رد شد.")
        await query.edit_message_text("❌ فیش رد شد.")

# ===== پردازش پیام‌ها (فیش یا نظر)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    caption = f"📥 فیش جدید از {user.full_name} ({user.id})"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"تایید_{user.id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"رد_{user.id}")
        ]
    ])

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, reply_markup=keyboard)
    elif update.message.document:
        await bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption=caption, reply_markup=keyboard)
    elif update.message.text:
        await bot.send_message(chat_id=ADMIN_ID, text=f"{caption}\n\n{update.message.text}", reply_markup=keyboard)

# ===== اتصال هندلرها
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

# ===== اجرای وب‌هوک
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"https://hozhin.onrender.com/{TOKEN}"
    )
