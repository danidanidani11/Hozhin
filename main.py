from flask import Flask, request
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
CHANNEL_USERNAME = "@fromheartsoul"

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# بررسی عضویت
def check_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# هندلر /start
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if not check_membership(user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership")]
        ])
        bot.send_message(chat_id=user_id, text="برای استفاده از ربات، ابتدا عضو کانال شوید:", reply_markup=keyboard)
        return

    bot.send_message(chat_id=user_id, text="🎉 خوش آمدید! عضویت شما تایید شد.")

# بررسی دکمه "عضو شدم"
def callback_query_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "check_membership":
        if check_membership(user_id):
            bot.send_message(chat_id=user_id, text="✅ عضویت شما تایید شد. خوش آمدید!")
        else:
            bot.send_message(chat_id=user_id, text="❌ هنوز عضو نیستید. لطفاً ابتدا عضو شوید.")

# دیسپچر
dispatcher = Dispatcher(bot, None, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))

# وب‌هوک برای رندر
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    import os
    bot.set_webhook("https://hozhin.onrender.com/" + TOKEN)  # آدرس رندر خودتو بذار
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
