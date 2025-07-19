import os
from flask import Flask, request
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
import asyncio

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

app = Flask(__name__)
bot = Bot(token=TOKEN)

# ===== متن‌ها =====
about_book = """رمان هوژین و حرمان..."""
about_author = """سلام رفقا 🙋🏻‍♂..."""
suggest_text = """اگر درباره کتاب پیشنهاد یا انتقادی دارید..."""
payment_text = """5859 8311 3314 0268

لطفا فیش رو همینجا ارسال کنید تا مورد تایید قرار بگیرد.هزینه کتاب ۱۱۰ هزارتومان میباشد.
ممکن است تایید فیش کمی زمان‌بر باشد پس لطفا صبور باشید.
در صورت تایید فایل پی دی اف برایتان در همینجا ارسال میشود.
اگر هرگونه مشکلی برایتان پیش آمد در بخش انتقادات و پیشنهادات برای ما ارسال کنید تا بررسی شود."""

# ===== دکمه‌های منو =====
def get_main_keyboard():
    buttons = [
        ["📘 خرید کتاب", "🗣 انتقادات و پیشنهادات"],
        ["📖 درباره کتاب", "✍️ درباره نویسنده"],
        ["🔊 کتاب صوتی (به زودی)"]
    ]
    return [[InlineKeyboardButton(text, callback_data=text)] for row in buttons for text in row]

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await application.update_queue.put(update)
    return "ok"

@app.route("/")
def index():
    return "ربات فعال است."

# ===== هندلر استارت =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("به ربات هوژین حرمان خوش آمدید 🌿", reply_markup=InlineKeyboardMarkup(get_main_keyboard()))

# ===== هندلر دکمه‌ها =====
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
        await bot.send_message(chat_id=user_id, text="❌ فیش ارسالی شما رد شد.")
        await query.edit_message_text("❌ فیش رد شد.")

# ===== دریافت فیش/نظر =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if update.message.photo or update.message.document or update.message.text:
        caption = f"📥 فیش جدید از: {user.full_name} ({user.id})"
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

# ===== اجرای برنامه =====
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

# ===== اجرای Flask =====
if __name__ == "__main__":
    async def run():
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
    
    asyncio.run(run())
