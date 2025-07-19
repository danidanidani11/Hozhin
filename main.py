import os
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
WEBHOOK_URL = "https://hozhin.onrender.com/webhook"
PDF_PATH = "books/hozhin_harman.pdf"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 🛠️ منوی اصلی
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 خرید کتاب", callback_data="buy"))
    markup.add(InlineKeyboardButton("📖 درباره کتاب", callback_data="about"))
    markup.add(InlineKeyboardButton("👤 درباره نویسنده", callback_data="author"))
    markup.add(InlineKeyboardButton("💬 ارسال نظر", callback_data="feedback"))
    markup.add(InlineKeyboardButton("🎧 کتاب صوتی (بزودی)", callback_data="audio"))
    return markup

# /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "سلام! به ربات هوژین حرمان خوش آمدید.\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=main_menu()
    )

# دکمه‌ها
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    data = c.data
    if data == "buy":
        bot.send_message(c.message.chat.id, "💳 لطفاً رسید پرداخت را ارسال کنید (عکس یا فایل).")
    elif data == "about":
        bot.send_message(c.message.chat.id, "📖 درباره کتاب: ...")
    elif data == "author":
        bot.send_message(c.message.chat.id, "👤 درباره نویسنده: ...")
    elif data == "feedback":
        bot.send_message(c.message.chat.id, "✍️ لطفاً نظر خود را ارسال نمایید.")
    elif data == "audio":
        bot.send_message(c.message.chat.id, "🔊 کتاب صوتی بزودی فعال خواهد شد.")
    bot.answer_callback_query(c.id)

# دریافت رسید یا نظر
@bot.message_handler(content_types=['text', 'photo', 'document'])
def handle_message(message):
    if message.chat.id == ADMIN_ID:
        return
    user = message.from_user
    info = f"🧾 پیام جدید از {user.full_name} (ID: {user.id})"
    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{info}\n\n💬 {message.text}")
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=info)
    elif message.content_type == 'document':
        bot.send_document(ADMIN_ID, message.document.file_id, caption=info)
    bot.send_message(message.chat.id, "✅ پیام شما برای ادمین ارسال شد.")

# 🌟 فرمان ارسال کتاب توسط ادمین
@bot.message_handler(commands=['sendbook'])
def sendbook(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "فرمت اشتباه. مثال صحیح:\n/sendbook 12345678")
        return
    user_id = int(parts[1])
    if not os.path.exists(PDF_PATH):
        bot.reply_to(message, "فایل کتاب موجود نیست.")
        return
    bot.send_document(user_id, InputFile(PDF_PATH))
    bot.reply_to(message, "✅ کتاب ارسال شد.")

# 🧷 ویـب هوک (Flask endpoint)
@app.route('/')
def home():
    return 'ربات فعال است'

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
