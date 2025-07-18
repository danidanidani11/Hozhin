from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request

TOKEN = "توکن_تو"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

app = Flask(__name__)

ABOUT_BOOK_TEXT = "..."  # متن درباره کتاب
ABOUT_AUTHOR_TEXT = "..."  # متن درباره نویسنده
AUDIOBOOK_TEXT = "این بخش به زودی فعال میشود."

users_payment = {}
user_waiting_for_receipt = set()

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("کتاب صوتی", callback_data="audiobook")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if member.status in ["left", "kicked"]:
            await update.message.reply_text(f"لطفا ابتدا عضو کانال @{CHANNEL_USERNAME} شوید و دوباره /start را ارسال کنید.")
            return
    except:
        await update.message.reply_text("خطا در بررسی عضویت کانال. لطفا بعدا امتحان کنید.")
        return

    await update.message.reply_text(
        f"سلام {user.first_name} 👋\n"
        "به ربات کتاب هوژین حرمان خوش آمدید.",
        reply_markup=main_menu_keyboard()
    )

# بقیه هندلرها هم مشابه با async و با Application ثبت میشن...

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = await request.get_json()
    update = Update.de_json(data, app.bot)
    await app.bot.update_queue.put(update)
    return "ok"

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    app.bot = application.bot

    application.add_handler(CommandHandler("start", start))
    # اضافه کردن بقیه هندلرها به application...

    # اجرای فلاسک و ربات به صورت همزمان (اگر لازم)
    import threading

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()

    application.run_polling()
