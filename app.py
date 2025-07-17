from flask import Flask, request
import telebot
from telebot import types
import os

app = Flask(__name__)

# تنظیمات
TOKEN = os.getenv('TOKEN', '7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0')
ADMIN_ID = int(os.getenv('ADMIN_ID', '5542927340'))
CHANNEL = os.getenv('CHANNEL', 'fromheartsoul')
CARD_NUMBER = os.getenv('CARD_NUMBER', '5859 8311 3314 0268')
BOOK_PRICE = os.getenv('BOOK_PRICE', '110 هزارتومان')

bot = telebot.TeleBot(TOKEN)

# ذخیره اطلاعات
user_payments = {}
user_messages = {}

# صفحه اصلی Flask
@app.route('/')
def home():
    return "ربات فروش کتاب هوژین و حرمان فعال است!"

# وب‌هک برای تلگرام
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_update = request.stream.read().decode('utf-8')
        update = types.Update.de_json(json_update)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

# بررسی عضویت در کانال
def is_member(user_id):
    try:
        return bot.get_chat_member(f"@{CHANNEL}", user_id).status in ['member', 'administrator', 'creator']
    except:
        return False

# منوی اصلی
def show_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton('📕 خرید کتاب'),
        types.KeyboardButton('💬 انتقادات و پیشنهادات'),
        types.KeyboardButton('📖 درباره کتاب'),
        types.KeyboardButton('✍️ درباره نویسنده'),
        types.KeyboardButton('🎧 کتاب صوتی (به زودی)')
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, "منوی اصلی:", reply_markup=markup)

# دستور /start
@bot.message_handler(commands=['start'])
def start(message):
    if is_member(message.from_user.id):
        show_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, f"⚠️ برای استفاده از ربات، لطفا در کانال ما عضو شوید:\n@{CHANNEL}\nسپس /start را مجددا ارسال کنید.")

# پردازش پیام‌ها
@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    if not is_member(message.from_user.id):
        bot.send_message(message.chat.id, f"⚠️ لطفا ابتدا در کانال ما عضو شوید:\n@{CHANNEL}")
        return
    
    text = message.text
    
    if text == '📕 خرید کتاب':
        send_payment_info(message.chat.id)
    elif text == '💬 انتقادات و پیشنهادات':
        request_feedback(message.chat.id)
    elif text == '📖 درباره کتاب':
        send_book_info(message.chat.id)
    elif text == '✍️ درباره نویسنده':
        send_author_info(message.chat.id)
    elif text == '🎧 کتاب صوتی (به زودی)':
        bot.send_message(message.chat.id, "این بخش به زودی فعال خواهد شد.")

# اطلاعات پرداخت
def send_payment_info(chat_id):
    msg = f"""
💳 اطلاعات پرداخت:
شماره کارت: <code>{CARD_NUMBER}</code>
مبلغ: {BOOK_PRICE}

پس از واریز، فیش پرداخت (عکس یا متن) را ارسال کنید.
"""
    bot.send_message(chat_id, msg, parse_mode='HTML')

# دریافت فیش پرداخت
@bot.message_handler(content_types=['photo', 'document', 'text'])
def handle_payment(message):
    if message.content_type == 'text' and message.text.startswith(('📕', '💬', '📖', '✍️', '🎧')):
        return
    
    user_id = message.from_user.id
    user_payments[user_id] = {
        'proof': message.photo[-1].file_id if message.photo else (
            message.document.file_id if message.document else message.text
        ),
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
        bot.send_photo(ADMIN_ID, user_payments[user_id]['proof'], 
                      caption=f"فیش پرداخت از کاربر {user_id}", reply_markup=markup)
    elif message.document:
        bot.send_document(ADMIN_ID, user_payments[user_id]['proof'],
                         caption=f"فیش پرداخت از کاربر {user_id}", reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, f"فیش متنی از کاربر {user_id}:\n\n{message.text}", reply_markup=markup)
    
    bot.send_message(user_id, "فیش شما برای تایید ارسال شد. لطفا صبر کنید.")

# درباره کتاب
def send_book_info(chat_id):
    text = """
📚 رمان هوژین و حرمان:
روایتی عاشقانه با تلفیق سبک‌های سورئالیسم، رئالیسم و روان

🔸 هوژین: واژه‌ای کردی به معنای نور زندگی
🔸 حرمان: نماد اندوه و افسردگی

📖 روش مطالعه:
- بار اول: بخش ۱ → ۲ → ۳
- بار دوم: بخش ۲ → ۱ → ۳
(برای دریافت دو برداشت متفاوت)

📜 نکات:
- برخی بخش‌ها واقعی هستند
- اشعار از شاعران ایرانی انتخاب شده‌اند
- مطالب داخل «» از نامه‌ها یا بیت‌های کوتاه الهام گرفته شده‌اند
"""
    bot.send_message(chat_id, text)

# درباره نویسنده
def send_author_info(chat_id):
    text = """
سلام رفقا! 🙋🏻‍♂
مانی محمودی، نویسنده کتاب هوژین و حرمان.

🔹 شروع نویسندگی از ۱۳ سالگی
🔹 اولین اثر: هوژین و حرمان
🔹 در حال نوشتن آثار جدید

امیدوارم از کتاب لذت ببرید! 😊❤️
"""
    bot.send_message(chat_id, text)

# انتقادات و پیشنهادات
def request_feedback(chat_id):
    msg = bot.send_message(chat_id, """
💬 انتقادات و پیشنهادات:
لطفا نظر خود را ارسال کنید.

نظرات شما خوانده شده و ارزشمند خواهد بود. ☺️
""")
    bot.register_next_step_handler(msg, process_feedback)

def process_feedback(message):
    user_id = message.from_user.id
    user_messages[user_id] = message.text
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✍️ پاسخ", callback_data=f"reply_{user_id}"))
    
    bot.send_message(ADMIN_ID, f"پیام جدید از کاربر {user_id}:\n\n{message.text}", reply_markup=markup)
    bot.send_message(user_id, "پیام شما ثبت شد. سپاس!")

# پردازش کلیک‌های اینلاین
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    action, user_id = call.data.split('_')
    user_id = int(user_id)
    
    if action == 'approve':
        bot.send_message(ADMIN_ID, f"پرداخت کاربر {user_id} تایید شد.")
        bot.send_message(user_id, "✅ پرداخت شما تایید شد. کتاب به زودی ارسال می‌شود.")
        # ارسال فایل کتاب:
        # bot.send_document(user_id, open('book.pdf', 'rb'))
        del user_payments[user_id]
        
    elif action == 'reject':
        bot.send_message(ADMIN_ID, f"پرداخت کاربر {user_id} رد شد.")
        bot.send_message(user_id, "❌ پرداخت شما تایید نشد. لطفا مجددا تلاش کنید.")
        del user_payments[user_id]
        
    elif action == 'reply':
        msg = bot.send_message(ADMIN_ID, "پاسخ خود را وارد کنید:")
        bot.register_next_step_handler(msg, lambda m: send_reply(m, user_id))

def send_reply(message, user_id):
    bot.send_message(user_id, f"📩 پاسخ ادمین:\n\n{message.text}")
    bot.send_message(ADMIN_ID, "✅ پاسخ ارسال شد.")

# تنظیم وب‌هک
if __name__ == '__main__':
    if os.getenv('ENV') == 'production':
        bot.remove_webhook()
        bot.set_webhook(url='https://hozhin.onrender.com/webhook')
    else:
        bot.polling()
