import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import asyncio

# تنظیم لاگ‌گیری
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# تنظیمات اولیه
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@fromheartsoul"
PDF_FILE_PATH = "hozhin_harman.pdf"

# ایجاد اپلیکیشن Flask
app = Flask(__name__)

# ایجاد اپلیکیشن تلگرام
bot_app = Application.builder().token(TOKEN).build()

# متن‌های بخش‌های مختلف
BUY_BOOK_TEXT = """لطفا فیش پرداخت را همینجا ارسال کنید تا مورد تأیید قرار بگیرد.
هزینه کتاب ۱۱۰ هزارتومان است.
شماره کارت: **5859 8311 3314 0268**
ممکن است تأیید فیش کمی زمان‌بر باشد، پس لطفا صبور باشید.
در صورت تأیید، فایل PDF کتاب برایتان ارسال می‌شود.
اگر مشکلی پیش آمد، در بخش انتقادات و پیشنهادات برای ما ارسال کنید."""

SUGGESTION_TEXT = """اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند، حتما در این بخش بنویسید تا بررسی شود.
مطمئن باشید نظرات شما خوانده می‌شود و باارزش خواهد بود. ☺️"""

ABOUT_BOOK_TEXT = """رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد. ... [متن کامل در پاسخ‌های قبلی]"""

ABOUT_AUTHOR_TEXT = """سلام رفقا 🙋🏻‍♂
مانی محمودی هستم، نویسنده کتاب هوژین حرمان.
نویسنده‌ای جوان هستم که با کنار هم گذاشتن نامه‌های متعدد موفق به نوشتن این کتاب شدم. ... [متن کامل در پاسخ‌های قبلی]"""

AUDIO_BOOK_TEXT = "این بخش به زودی فعال می‌شود."

# منوی اصلی
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 خرید کتاب", callback_data="buy_book")],
        [InlineKeyboardButton("💬 انتقادات و پیشنهادات", callback_data="suggestion")],
        [InlineKeyboardButton("ℹ️ درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🎧 کتاب صوتی", callback_data="audio_book")],
    ]
    return InlineKeyboardMarkup(keyboard)

# هندلر شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"سلام {user.first_name}!\nبه بات هوژین و حرمان خوش آمدید. 😊\nلطفاً از منوی زیر یکی از گزینه‌ها را انتخاب کنید:"
    await update.message.reply_text(welcome_text, reply_markup=main_menu())

# هندلر دکمه‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy_book":
        await query.message.reply_text(BUY_BOOK_TEXT)
        context.user_data["state"] = "waiting_for_receipt"
    elif query.data == "suggestion":
        await query.message.reply_text(SUGGESTION_TEXT)
        context.user_data["state"] = "waiting_for_suggestion"
    elif query.data == "about_book":
        await query.message.reply_text(ABOUT_BOOK_TEXT)
    elif query.data == "about_author":
        await query.message.reply_text(ABOUT_AUTHOR_TEXT)
    elif query.data == "audio_book":
        await query.message.reply_text(AUDIO_BOOK_TEXT)

# هندلر پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = context.user_data.get("state")

    if state == "waiting_for_receipt" and update.message.photo:
        photo = update.message.photo[-1]
        await update.message.reply_text("فیش پرداخت دریافت شد. در انتظار تأیید ادمین...")
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=f"فیش پرداخت از کاربر {user_id}. برای تأیید، از /approve {user_id} استفاده کنید."
        )
    elif state == "waiting_for_suggestion":
        suggestion = update.message.text
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"پیشنهاد/انتقاد از کاربر {user_id}:\n{suggestion}"
        )
        await update.message.reply_text("ممنون از نظرتون! پیشنهاد شما برای ادمین ارسال شد.")
        context.user_data["state"] = None
    else:
        await update.message.reply_text("لطفاً از منوی اصلی یک گزینه انتخاب کنید.", reply_markup=main_menu())

# هندلر تأیید فیش
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("فقط ادمین می‌تواند از این دستور استفاده کند.")
        return

    try:
        user_id = int(context.args[0])
        if os.path.exists(PDF_FILE_PATH):
            with open(PDF_FILE_PATH, "rb") as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    caption="فیش شما تأیید شد! فایل PDF کتاب برایتان ارسال شد."
                )
            await update.message.reply_text(f"فایل PDF برای کاربر {user_id} ارسال شد.")
        else:
            await update.message.reply_text("خطا: فایل PDF یافت نشد.")
    except (IndexError, ValueError):
        await update.message.reply_text("لطفاً آیدی کاربر را به درستی وارد کنید. مثال: /approve 123456789")
    except Exception as e:
        await update.message.reply_text(f"خطا در ارسال فایل: {str(e)}")

# ثبت هندلرها
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(button))
bot_app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
bot_app.add_handler(CommandHandler("approve", approve))

# مسیر Flask برای بررسی سرور
@app.route("/")
def home():
    return "Telegram Bot is running!"

# مسیر وب‌هوک
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in webhook")
            return {"status": "error", "message": "No JSON data"}, 400
        update = Update.de_json(data, bot_app.bot)
        if update:
            await bot_app.process_update(update)
            logger.info("Webhook processed successfully")
            return {"status": "ok"}
        else:
            logger.error("Invalid update received")
            return {"status": "error", "message": "Invalid update"}, 400
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

# اجرای سرور
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
