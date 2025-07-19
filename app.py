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
from threading import Thread

# تنظیمات لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تنظیمات اصلی
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
PDF_FILE_PATH = "/books/hozhin_harman.pdf"

# ساخت برنامه Flask
app = Flask(__name__)

# ساخت برنامه تلگرام
bot_app = Application.builder().token(TOKEN).build()

# متن‌های مختلف
TEXTS = {
    "buy": """لطفا فیش پرداخت را همینجا ارسال کنید...
(متن کامل خرید کتاب)""",
    "suggestion": """اگر پیشنهاد یا انتقادی دارید...
(متن کامل پیشنهادات)""",
    "about_book": """رمان هوژین و حرمان...
(متن کامل درباره کتاب)""",
    "about_author": """سلام رفقا 🙋🏻‍♂...
(متن کامل درباره نویسنده)""",
    "audio": "این بخش به زودی فعال می‌شود."
}

# منوی اصلی با کیبورد
def main_menu():
    buttons = [
        ["📚 خرید کتاب", "💬 انتقادات و پیشنهادات"],
        ["ℹ️ درباره کتاب", "✍️ درباره نویسنده"],
        ["🎧 کتاب صوتی"]
    ]
    keyboard = [[InlineKeyboardButton(text, callback_data=text)] for row in buttons for text in row]
    return InlineKeyboardMarkup([keyboard[i:i+2] for i in range(0, len(keyboard), 2)])

# منوی تایید/رد برای ادمین
def approval_menu(user_id, msg_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"approve_{user_id}_{msg_id}"),
            InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{user_id}_{msg_id}")
        ]
    ])

# هندلر شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! به ربات خوش آمدید. لطفاً گزینه مورد نظر را انتخاب کنید:",
        reply_markup=main_menu()
    )

# هندلر کلیک روی دکمه‌ها
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except:
        pass

    if "📚 خرید کتاب" in query.data:
        await query.message.reply_text(TEXTS["buy"])
        context.user_data["state"] = "waiting_receipt"
    
    elif "💬 انتقادات و پیشنهادات" in query.data:
        await query.message.reply_text(TEXTS["suggestion"])
        context.user_data["state"] = "waiting_suggestion"
    
    elif "ℹ️ درباره کتاب" in query.data:
        await query.message.reply_text(TEXTS["about_book"], reply_markup=main_menu())
    
    elif "✍️ درباره نویسنده" in query.data:
        await query.message.reply_text(TEXTS["about_author"], reply_markup=main_menu())
    
    elif "🎧 کتاب صوتی" in query.data:
        await query.message.reply_text(TEXTS["audio"], reply_markup=main_menu())
    
    elif query.data.startswith("approve_"):
        _, user_id, msg_id = query.data.split("_")
        try:
            with open(PDF_FILE_PATH, "rb") as file:
                await context.bot.send_document(
                    chat_id=int(user_id),
                    document=file,
                    caption="پرداخت شما تایید شد! کتاب پیوست شده است."
                )
            await context.bot.delete_message(chat_id=ADMIN_ID, message_id=int(msg_id))
            await query.message.reply_text(f"پرداخت کاربر {user_id} تایید شد.")
        except Exception as e:
            logger.error(f"خطا در تایید پرداخت: {e}")
    
    elif query.data.startswith("reject_"):
        _, user_id, msg_id = query.data.split("_")
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text="پرداخت شما رد شد. لطفاً مجدداً تلاش کنید."
            )
            await context.bot.delete_message(chat_id=ADMIN_ID, message_id=int(msg_id))
            await query.message.reply_text(f"پرداخت کاربر {user_id} رد شد.")
        except Exception as e:
            logger.error(f"خطا در رد پرداخت: {e}")

# هندلر پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    
    if state == "waiting_receipt" and update.message.photo:
        receipt = await update.message.forward(ADMIN_ID)
        await context.bot.send_message(
            ADMIN_ID,
            f"پرداخت جدید از کاربر {update.effective_user.id}",
            reply_markup=approval_menu(update.effective_user.id, receipt.message_id)
        )
        await update.message.reply_text("فیش شما دریافت شد و در حال بررسی است.")
        context.user_data["state"] = None
    
    elif state == "waiting_suggestion":
        await context.bot.send_message(
            ADMIN_ID,
            f"پیشنهاد جدید از کاربر {update.effective_user.id}:\n{update.message.text}"
        )
        await update.message.reply_text("پیشنهاد شما ثبت شد. سپاس!")
        context.user_data["state"] = None

# تنظیم هندلرها
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(button_click))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
bot_app.add_handler(MessageHandler(filters.PHOTO, handle_message))

# تابع برای اجرای async در thread جدید
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(coro)
    loop.close()

# وب‌هوک
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(), bot_app.bot)
        Thread(target=run_async, args=(bot_app.process_update(update),)).start()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"خطا در وب‌هوک: {e}")
        return {"status": "error"}, 500

# تنظیم وب‌هوک
async def setup_webhook():
    await bot_app.initialize()
    await bot_app.bot.set_webhook(f"https://hozhin.onrender.com/{TOKEN}")

# اجرای اولیه
def setup():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())
    loop.close()

if __name__ == "__main__":
    setup()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
