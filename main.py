import os
from flask import Flask, request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"
WEBHOOK_URL = "https://hozhin.onrender.com"

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

pending_users = {}  # user_id -> message_id


# ---------- دکمه‌ها ----------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📕 خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("✉️ انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("👤 درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🔊 کتاب صوتی (به‌زودی)", callback_data="coming_soon")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ---------- دستورات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "به ربات رسمی کتاب هوژین حرمان خوش آمدید 🌹",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        await query.message.reply_text(
            """5859 8311 3314 0268

لطفا فیش را همینجا ارسال کنید تا بررسی و تأیید شود.
هزینه کتاب ۱۱۰ هزارتومان می‌باشد.
ممکن است تأیید کمی زمان‌بر باشد، لطفاً صبور باشید.

در صورت تأیید فایل PDF کتاب برای شما ارسال خواهد شد.

در صورت بروز هرگونه مشکل، لطفاً در بخش «انتقادات و پیشنهادات» مطرح کنید."""
        )
    elif query.data == "feedback":
        await query.message.reply_text("لطفاً انتقادات و پیشنهادات خود را ارسال کنید 📝")
    elif query.data == "about_book":
        await query.message.reply_text(
            """📖 درباره کتاب:

رمان هوژین و حرمان روایتی عاشقانه و تلفیقی از سبک‌های سورئالیسم، رئالیسم و روان است...

(ادامه متن کامل شما اینجاست)

در صورت خرید امیدوارم لذت ببرید."""
        )
    elif query.data == "about_author":
        await query.message.reply_text(
            """👤 درباره نویسنده:

سلام رفقا 🙋🏻‍♂
مانی محمودی هستم نویسنده کتاب هوژین حرمان...

(ادامه متن کامل شما اینجاست)"""
        )
    elif query.data == "coming_soon":
        await query.message.reply_text("🔊 این بخش به‌زودی فعال می‌شود.")


# ---------- دریافت پیام کاربر ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    # پیام ارسالی را برای ادمین فوروارد کن
    msg = await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.message.chat_id, message_id=update.message.message_id)

    # دکمه تایید و رد برای ادمین بفرست
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"accept_{update.message.chat_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{update.message.chat_id}")
        ]
    ])
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"بررسی فیش برای کاربر {user.full_name}", reply_markup=keyboard)

    pending_users[update.message.chat_id] = update.message.chat_id


# ---------- ادمین تایید یا رد می‌کند ----------
async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("accept_"):
        user_id = int(query.data.split("_")[1])
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ فیش شما تایید شد. فایل کتاب در ادامه ارسال می‌شود."
        )
        await context.bot.send_document(chat_id=user_id, document=InputFile("books/hozhin_harman.pdf"))

    elif query.data.startswith("reject_"):
        user_id = int(query.data.split("_")[1])
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ فیش شما تایید نشد. لطفاً دوباره بررسی و ارسال فرمایید."
        )


# ---------- اضافه کردن هندلرها ----------
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler, pattern="^(buy|feedback|about_book|about_author|coming_soon)$"))
application.add_handler(CallbackQueryHandler(admin_decision, pattern="^(accept|reject)_"))
application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))


# ---------- Flask Webhook ----------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"


@app.route("/", methods=["GET"])
def home():
    return "ربات فعال است."


if __name__ == "__main__":
    # ست کردن Webhook
    import asyncio

    async def set_webhook():
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

    asyncio.run(set_webhook())
    application.run_polling()  # فقط یک بار برای اطمینان اجرا، ولی وبهوک فعال است
    app.run(port=10000)
