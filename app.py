import os
from flask import Flask, request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

app = Flask(__name__)

users_payment = {}
user_waiting_for_receipt = set()

# متن‌های ثابت
ABOUT_BOOK_TEXT = """..."""
ABOUT_AUTHOR_TEXT = """..."""
AUDIOBOOK_TEXT = "این بخش به زودی فعال میشود."

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("کتاب صوتی", callback_data="audiobook")],
    ]
    return InlineKeyboardMarkup(keyboard)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_data = request.get_json()
    update = Update.de_json(json_data, app.bot)
    app.application.update_queue.put(update)
    return 'ok'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if member.status in ["left", "kicked"]:
            await update.message.reply_text(
                f"لطفا ابتدا عضو کانال @{CHANNEL_USERNAME} شوید و دوباره /start را ارسال کنید."
            )
            return
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        await update.message.reply_text(
            "به ربات کتاب هوژین حرمان خوش آمدید.\n"
            f"متاسفانه بررسی عضویت کانال با مشکل مواجه شد. لطفا بعداً تلاش کنید."
        )
        return

    await update.message.reply_text(
        f"سلام {user.first_name} 👋\n"
        "به ربات کتاب هوژین حرمان خوش آمدید.",
        reply_markup=main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        user_waiting_for_receipt.add(query.from_user.id)
        await query.edit_message_text(
            "شماره کارت برای پرداخت:\n"
            "5859 8311 3314 0268\n\n"
            "لطفا فیش واریزی را همینجا ارسال کنید.\n"
            "هزینه کتاب: 110 هزار تومان\n"
            "پس از تایید، فایل PDF ارسال خواهد شد."
        )
    elif query.data == "feedback":
        await query.edit_message_text("پیام خود را ارسال کنید...")
    elif query.data == "about_book":
        await query.edit_message_text(ABOUT_BOOK_TEXT)
    elif query.data == "about_author":
        await query.edit_message_text(ABOUT_AUTHOR_TEXT)
    elif query.data == "audiobook":
        await query.edit_message_text(AUDIOBOOK_TEXT)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in user_waiting_for_receipt:
        # پردازش فیش پرداخت
        receipt = None
        if update.message.photo:
            receipt = update.message.photo[-1].file_id
        elif update.message.document:
            receipt = update.message.document.file_id
        else:
            receipt = update.message.text

        users_payment[user_id] = {
            "status": "pending",
            "receipt": receipt,
            "username": update.effective_user.username or update.effective_user.first_name
        }
        user_waiting_for_receipt.remove(user_id)

        # ارسال به ادمین
        if update.message.photo:
            msg = await context.bot.send_photo(
                ADMIN_ID, 
                photo=receipt,
                caption=f"پرداخت جدید از کاربر {user_id}"
            )
        elif update.message.document:
            msg = await context.bot.send_document(
                ADMIN_ID,
                document=receipt,
                caption=f"پرداخت جدید از کاربر {user_id}"
            )
        else:
            msg = await context.bot.send_message(
                ADMIN_ID,
                text=f"پرداخت جدید از کاربر {user_id}:\n{receipt}"
            )

        # افزودن دکمه‌های تایید/رد
        await context.bot.send_message(
            ADMIN_ID,
            text="لطفا پرداخت را بررسی کنید:",
            reply_to_message_id=msg.message_id,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("تایید ✅", callback_data=f"approve_{user_id}"),
                    InlineKeyboardButton("رد ❌", callback_data=f"reject_{user_id}")
                ]
            ])
        )

        await update.message.reply_text("فیش دریافت شد. در حال بررسی...")
    else:
        # انتقادات و پیشنهادات
        await context.bot.send_message(
            ADMIN_ID,
            f"پیام جدید از {update.effective_user.username or update.effective_user.first_name}:\n\n{update.message.text}"
        )
        await update.message.reply_text("پیام شما دریافت شد. با تشکر!")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("شما مجاز نیستید!")
        return

    action, user_id = query.data.split("_")
    user_id = int(user_id)

    if action == "approve":
        users_payment[user_id]["status"] = "approved"
        await query.edit_message_text("پرداخت تایید شد ✅")
        
        try:
            with open("books/hozhin_harman.pdf", "rb") as f:
                await context.bot.send_document(
                    user_id,
                    document=InputFile(f),
                    caption="کتاب هوژین حرمان\nبا تشکر از خرید شما!"
                )
        except Exception as e:
            print(f"Error sending book: {e}")
            await context.bot.send_message(
                ADMIN_ID,
                "خطا در ارسال کتاب! لطفا فایل را بررسی کنید."
            )
    else:
        users_payment[user_id]["status"] = "rejected"
        await query.edit_message_text("پرداخت رد شد ❌")
        await context.bot.send_message(
            user_id,
            "پرداخت شما تایید نشد. لطفا مجددا تلاش کنید."
        )

def run_bot():
    # ساخت برنامه تلگرام
    application = ApplicationBuilder().token(TOKEN).build()
    app.application = application
    app.bot = application.bot

    # افزودن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(approve|reject)_"))

    # تنظیم وب‌هوک
    async def set_webhook():
        await application.bot.set_webhook(
            url=f"https://YOUR_DOMAIN.com/{TOKEN}",
            drop_pending_updates=True
        )
        print("Webhook set up successfully")

    import asyncio
    asyncio.run(set_webhook())

    # اجرای سرور Flask
    from threading import Thread
    Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5000}).start()

if __name__ == "__main__":
    run_bot()
