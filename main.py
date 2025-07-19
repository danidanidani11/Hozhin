import os
from flask import Flask, request
import telebot
from telebot import types

TOKEN = '7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0'
ADMIN_ID = 5542927340
CHANNEL_USERNAME = 'fromheartsoul'
PDF_PATH = 'books/hozhin_harman.pdf'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_state = {}

# --- دکمه‌ها ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📖 خرید کتاب", "🗣️ انتقادات و پیشنهادات")
    markup.add("ℹ️ درباره کتاب", "✍️ درباره نویسنده")
    markup.add("🔊 کتاب صوتی (بزودی)")
    return markup

# --- استارت ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(
        message.chat.id,
        "به ربات فروش کتاب «هوژین حرمان» خوش آمدید 🌸",
        reply_markup=get_main_keyboard()
    )

# --- خرید کتاب ---
@bot.message_handler(func=lambda msg: msg.text == "📖 خرید کتاب")
def buy_book(message):
    user_state[message.chat.id] = 'awaiting_receipt'
    bot.send_message(message.chat.id, "لطفاً رسید پرداخت خود را ارسال کنید (عکس یا متن).")

@bot.message_handler(content_types=['text', 'photo'])
def handle_receipt(message):
    if user_state.get(message.chat.id) == 'awaiting_receipt':
        user_state.pop(message.chat.id)

        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            caption = message.caption or "رسید پرداخت"
            sent = bot.send_photo(
                ADMIN_ID, file_id, caption=f"{caption}\n\nاز طرف: {message.from_user.id}"
            )
        else:
            sent = bot.send_message(
                ADMIN_ID,
                f"رسید پرداخت از کاربر {message.from_user.id}:\n\n{message.text}"
            )

        # دکمه تایید و رد برای ادمین
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{message.chat.id}"),
            types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{message.chat.id}")
        )
        bot.send_message(ADMIN_ID, "آیا رسید را تایید می‌کنید؟", reply_markup=markup)
        bot.send_message(message.chat.id, "رسید شما برای بررسی ارسال شد ✅")

# --- پاسخ ادمین به تایید یا رد ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_approval(call):
    user_id = int(call.data.split("_")[1])
    if call.data.startswith("approve_"):
        bot.send_document(user_id, open(PDF_PATH, "rb"))
        bot.send_message(user_id, "📘 خرید شما تایید شد. فایل کتاب برایتان ارسال شد.")
        bot.send_message(ADMIN_ID, f"✅ فایل برای {user_id} ارسال شد.")
    else:
        bot.send_message(user_id, "❌ رسید شما رد شد. لطفاً مجدد تلاش کنید.")
        bot.send_message(ADMIN_ID, f"❌ رسید کاربر {user_id} رد شد.")
    bot.answer_callback_query(call.id)

# --- انتقادات و پیشنهادات ---
@bot.message_handler(func=lambda msg: msg.text == "🗣️ انتقادات و پیشنهادات")
def suggestions(message):
    user_state[message.chat.id] = 'awaiting_feedback'
    bot.send_message(message.chat.id, "لطفاً نظر یا انتقاد خود را بنویسید:")

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id) == 'awaiting_feedback')
def receive_feedback(message):
    user_state.pop(message.chat.id)
    bot.send_message(ADMIN_ID, f"📩 پیام از {message.from_user.id}:\n\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. ممنون از همراهی‌تان.")

# --- درباره کتاب و نویسنده ---
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ درباره کتاب")
def about_book(message):
    bot.send_message(message.chat.id, "📖 کتاب «هوژین حرمان» روایتگر...")

@bot.message_handler(func=lambda msg: msg.text == "✍️ درباره نویسنده")
def about_author(message):
    bot.send_message(message.chat.id, "👤 نویسنده این اثر...")

@bot.message_handler(func=lambda msg: msg.text == "🔊 کتاب صوتی (بزودی)")
def audio_book(message):
    bot.send_message(message.chat.id, "🔊 نسخه صوتی کتاب در حال آماده‌سازی است. به زودی منتشر خواهد شد.")

# --- Flask Webhook ---
@app.route('/', methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/')
def index():
    return "ربات فعال است."

if __name__ == '__main__':
    import telebot
    bot.remove_webhook()
    bot.set_webhook(url='https://hozhin.onrender.com')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
