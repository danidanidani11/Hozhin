from flask import Flask, request, jsonify
import telebot
from telebot import types
import os
import logging

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# تنظیمات ربات
TOKEN = os.getenv('TOKEN', '7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0')
ADMIN_ID = int(os.getenv('ADMIN_ID', '5542927340'))
CHANNEL = os.getenv('CHANNEL', 'fromheartsoul')
CARD_NUMBER = os.getenv('CARD_NUMBER', '5859 8311 3314 0268')
BOOK_PRICE = os.getenv('BOOK_PRICE', '110 هزارتومان')
PORT = int(os.getenv('PORT', 5000))

bot = telebot.TeleBot(TOKEN)

# دیکشنری‌های ذخیره اطلاعات
user_payments = {}
user_messages = {}

# صفحه اصلی
@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "bot": "کتاب هوژین و حرمان",
        "version": "1.0"
    })

# وب‌هک تلگرام
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_json()
        update = types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

# --- توابع کمکی ---
def is_member(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False

def show_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton('📕 خرید کتاب'),
        types.KeyboardButton('💬 انتقادات و پیشنهادات'),
        types.KeyboardButton('📖 درباره کتاب'),
        types.KeyboardButton('✍️ درباره نویسنده'),
        types.KeyboardButton('🎧 کتاب صوتی')
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, "منوی اصلی:", reply_markup=markup)

# --- دستورات ربات ---
@bot.message_handler(commands=['start'])
def start(message):
    if is_member(message.from_user.id):
        show_menu(message.chat.id)
    else:
        bot.send_message(
            message.chat.id,
            f"سلام! برای استفاده از ربات، لطفاً در کانال ما عضو شوید:\n@{CHANNEL}\nسپس /start را مجدداً ارسال کنید."
        )

@bot.message_handler(func=lambda m: m.text == '📕 خرید کتاب')
def handle_purchase(message):
    msg = f"""
💳 اطلاعات پرداخت:
<code>شماره کارت: {CARD_NUMBER}</code>
💰 مبلغ: {BOOK_PRICE}

پس از واریز، فیش پرداخت (عکس یا متن) را ارسال کنید.
"""
    bot.send_message(message.chat.id, msg, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == '📖 درباره کتاب')
def handle_about_book(message):
    text = """
📚 رمان هوژین و حرمان:
روایتی عاشقانه با تلفیق سبک‌های سورئالیسم، رئالیسم و روان‌شناختی.

🔹 هوژین: واژه‌ای کردی به معنای "نور زندگی"
🔹 حرمان: نماد اندوه و افسردگی عمیق

📖 روش مطالعه پیشنهادی:
- بار اول: بخش ۱ → ۲ → ۳
- بار دوم: بخش ۲ → ۱ → ۳
(برای دریافت دو برداشت متفاوت)
"""
    bot.send_message(message.chat.id, text)

# --- پردازش پرداخت‌ها ---
@bot.message_handler(content_types=['photo', 'document', 'text'])
def handle_payment(message):
    if message.content_type == 'text' and message.text.startswith(('📕', '💬', '📖', '✍️', '🎧')):
        return
    
    user_id = message.from_user.id
    proof = None
    
    if message.photo:
        proof = message.photo[-1].file_id
    elif message.document:
        proof = message.document.file_id
    else:
        proof = message.text
    
    user_payments[user_id] = {
        'proof': proof,
        'type': message.content_type,
        'status': 'pending'
    }
    
    # ارسال به ادمین
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")
    )
    
    if message.photo:
        bot.send_photo(ADMIN_ID, proof, caption=f"فیش پرداخت از کاربر {user_id}", reply_markup=markup)
    elif message.document:
        bot.send_document(ADMIN_ID, proof, caption=f"فیش پرداخت از کاربر {user_id}", reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, f"فیش متنی از کاربر {user_id}:\n\n{message.text}", reply_markup=markup)
    
    bot.send_message(user_id, "✅ فیش پرداخت شما دریافت شد و در حال بررسی است.")

# --- مدیریت کال‌بک‌ها ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        action, user_id = call.data.split('_')
        user_id = int(user_id)
        
        if action == 'approve':
            bot.send_message(user_id, "✅ پرداخت شما تأیید شد. لینک دانلود کتاب:\n[لینک دانلود]")
            bot.send_message(ADMIN_ID, f"پرداخت کاربر {user_id} تأیید شد.")
            user_payments.pop(user_id, None)
            
        elif action == 'reject':
            bot.send_message(user_id, "❌ پرداخت شما تأیید نشد. لطفاً با پشتیبانی تماس بگیرید.")
            bot.send_message(ADMIN_ID, f"پرداخت کاربر {user_id} رد شد.")
            user_payments.pop(user_id, None)
            
    except Exception as e:
        logger.error(f"Error in callback: {e}")

# --- راه‌اندازی ربات ---
if __name__ == '__main__':
    if os.getenv('RENDER'):
        logger.info("Running in production mode")
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"https://hozhin.onrender.com/webhook")
    else:
        logger.info("Running in development mode")
        bot.polling()
