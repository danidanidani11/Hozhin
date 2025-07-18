from flask import Flask, request
import telegram
from telegram import *
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
import os
import json

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
bot = telegram.Bot(token=TOKEN)
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@fromheartsoul"
CARD_NUMBER = "5859 8311 3314 0268"
BOOK_PRICE = "۱۱۰ هزار تومان"

app = Flask(__name__)
user_state = {}

def check_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not check_membership(user_id):
        bot.send_message(chat_id=user_id,
                         text="برای استفاده از ربات ابتدا عضو کانال شوید:",
                         reply_markup=InlineKeyboardMarkup([
                             [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                             [InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership")]
                         ]))
        return
    send_menu(user_id)

def send_menu(chat_id):
    keyboard = [
        ["📘 خرید کتاب"],
        ["✉️ انتقادات و پیشنهادات"],
        ["📖 درباره کتاب", "🖋 درباره نویسنده"]
    ]
    bot.send_message(chat_id=chat_id, text="یکی از گزینه‌ها را انتخاب کنید:", 
                     reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

def handle_buttons(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "📘 خرید کتاب":
        bot.send_message(chat_id=user_id, text=f"قیمت کتاب: {BOOK_PRICE}\nلطفاً مبلغ را به کارت زیر واریز کرده و فیش را ارسال کنید:\n`{CARD_NUMBER}`", parse_mode="Markdown")
        user_state[user_id] = "waiting_for_receipt"

    elif text == "✉️ انتقادات و پیشنهادات":
        bot.send_message(chat_id=user_id, text="پیام خود را بنویسید:")
        user_state[user_id] = "waiting_for_feedback"

    elif text == "📖 درباره کتاب":
        bot.send_message(chat_id=user_id, text="📖 کتاب «هوژین و حرمان» روایت سفری عاشقانه و عمیق در دل واقعیت و رویا است...")

    elif text == "🖋 درباره نویسنده":
        bot.send_message(chat_id=user_id, text="🖋 نویسنده این کتاب، با نگاهی شاعرانه و نثری روان، داستانی پرکشش خلق کرده است...")

def callback_query_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if query.data == "check_membership":
        if check_membership(user_id):
            bot.send_message(chat_id=user_id, text="✅ عضویت شما تایید شد.")
            send_menu(user_id)
        else:
            bot.send_message(chat_id=user_id, text="❌ هنوز عضو کانال نیستید.")

def message_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_state:
        state = user_state[user_id]

        # دریافت فیش و ارسال به ادمین
        if state == "waiting_for_receipt":
            if update.message.photo:
                file = update.message.photo[-1].file_id
                caption = f"🧾 فیش پرداختی از کاربر [{update.message.from_user.full_name}](tg://user?id={user_id})"
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{user_id}"),
                     InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")]
                ])
                bot.send_photo(chat_id=ADMIN_ID, photo=file, caption=caption, parse_mode="Markdown", reply_markup=buttons)
                bot.send_message(chat_id=user_id, text="فیش شما ارسال شد. منتظر تایید ادمین باشید.")
                user_state.pop(user_id)
            else:
                bot.send_message(chat_id=user_id, text="لطفاً فیش پرداختی را به صورت عکس ارسال کنید.")

        # دریافت پیشنهاد و ارسال به ادمین
        elif state == "waiting_for_feedback":
            message = update.message.text
            feedback = f"✉️ پیام از کاربر [{update.message.from_user.full_name}](tg://user?id={user_id}):\n\n{message}"
            bot.send_message(chat_id=ADMIN_ID, text=feedback, parse_mode="Markdown")
            bot.send_message(chat_id=user_id, text="✅ پیام شما ارسال شد. ممنون از بازخوردتان.")
            user_state.pop(user_id)
    else:
        send_menu(user_id)

# بررسی تایید یا رد فیش توسط ادمین
def admin_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data.startswith("approve_"):
        user_id = int(data.split("_")[1])
        bot.send_message(chat_id=user_id, text="✅ پرداخت شما تایید شد. کتاب بزودی برای شما ارسال خواهد شد.")
        query.edit_message_caption(caption="🧾 فیش تایید شد ✅")

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        bot.send_message(chat_id=user_id, text="❌ پرداخت شما تایید نشد. لطفاً مجدداً تلاش کنید.")
        query.edit_message_caption(caption="🧾 فیش رد شد ❌")

# راه‌اندازی دیسپچر
dispatcher = Dispatcher(bot, None, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_buttons))
dispatcher.add_handler(MessageHandler(Filters.all, message_handler))
dispatcher.add_handler(telegram.ext.CallbackQueryHandler(callback_query_handler))
dispatcher.add_handler(telegram.ext.CallbackQueryHandler(admin_callback))

# راه‌اندازی Flask و Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "ربات فعال است."

if __name__ == "__main__":
    # تنظیم وبهوک برای اجرا در Render
    import logging
    logging.basicConfig(level=logging.INFO)
    URL = "https://hozhin.onrender.com"  # آدرس رندر خود را اینجا وارد کنید
    bot.set_webhook(f"{URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
