from flask import Flask, request, jsonify
import telebot
from telebot import types
import os
import logging
import time
from threading import Thread

# تنظیمات پایه
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# تنظیمات ربات
TOKEN = os.getenv('TOKEN', '7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0')
ADMIN_ID = int(os.getenv('ADMIN_ID', '5542927340'))
CHANNEL = os.getenv('CHANNEL', 'fromheartsoul')
CARD_NUMBER = os.getenv('CARD_NUMBER', '5859 8311 3314 0268')
BOOK_PRICE = os.getenv('BOOK_PRICE', '110 هزارتومان')
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', f'https://hozhin.onrender.com/webhook')

# ایجاد ربات
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ذخیره داده‌ها
user_data = {
    'payments': {},  # {user_id: {'proof': data, 'status': 'pending'/'approved'/'rejected'}}
    'feedbacks': {}  # {user_id: {'message': text, 'replied': bool}}
}

# --- توابع کمکی ---
def check_membership(user_id):
    """بررسی عضویت کاربر در کانال"""
    try:
        chat_member = bot.get_chat_member(f'@{CHANNEL}', user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f'خطا در بررسی عضویت: {e}')
        return False

def create_main_menu():
    """ساخت منوی اصلی"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton('📕 خرید کتاب'),
        types.KeyboardButton('💬 انتقادات و پیشنهادات'),
        types.KeyboardButton('📖 درباره کتاب'),
        types.KeyboardButton('✍️ درباره نویسنده'),
        types.KeyboardButton('🎧 کتاب صوتی')
    ]
    markup.add(*buttons)
    return markup

# --- مسیرهای Flask ---
@app.route('/')
def home():
    return jsonify({
        'status': 'active',
        'service': 'ربات فروش کتاب هوژین و حرمان',
        'version': '1.0.0'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_json()
        update = types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

# --- دستورات ربات ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if check_membership(user_id):
        bot.send_message(
            user_id,
            '👋 به ربات فروش کتاب هوژین و حرمان خوش آمدید!',
            reply_markup=create_main_menu()
        )
    else:
        bot.send_message(
            user_id,
            f'⚠️ برای استفاده از ربات، لطفاً در کانال ما عضو شوید:\n@{CHANNEL}\nسپس /start را مجدداً ارسال کنید.'
        )

@bot.message_handler(func=lambda m: m.text == '📕 خرید کتاب')
def handle_purchase(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        handle_start(message)
        return
    
    payment_info = f"""
💳 <b>اطلاعات پرداخت:</b>
<code>شماره کارت: {CARD_NUMBER}</code>
💰 مبلغ: {BOOK_PRICE}

📌 پس از واریز، فیش پرداخت (عکس یا متن) را همینجا ارسال کنید.

⚠️ توجه:
1. پس از تایید پرداخت، فایل کتاب برای شما ارسال می‌شود.
2. ممکن است تایید پرداخت تا 24 ساعت زمان ببرد.
3. در صورت مشکل، از بخش انتقادات و پیشنهادات پیام بدهید.
"""
    bot.send_message(user_id, payment_info)

@bot.message_handler(func=lambda m: m.text == '💬 انتقادات و پیشنهادات')
def handle_feedback(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        handle_start(message)
        return
    
    msg = bot.send_message(
        user_id,
        '💌 لطفاً نظر، انتقاد یا پیشنهاد خود را ارسال کنید:\n\n'
        'مطمئن باشید پیام شما خوانده خواهد شد و برای ما ارزشمند است.'
    )
    bot.register_next_step_handler(msg, process_feedback)

def process_feedback(message):
    user_id = message.from_user.id
    user_data['feedbacks'][user_id] = {
        'message': message.text,
        'replied': False
    }
    
    # ارسال به ادمین
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✍️ پاسخ', callback_data=f'reply_{user_id}'))
    
    bot.send_message(
        ADMIN_ID,
        f'📩 پیام جدید از کاربر {user_id}:\n\n{message.text}',
        reply_markup=markup
    )
    
    bot.send_message(user_id, '✅ پیام شما با موفقیت ثبت شد. سپاس از نظر شما!')

# --- پردازش پرداخت‌ها ---
@bot.message_handler(content_types=['photo', 'document', 'text'])
def handle_payment_proof(message):
    user_id = message.from_user.id
    
    # اگر پیام متنی معمولی است
    if message.content_type == 'text' and message.text in ['📕 خرید کتاب', '💬 انتقادات و پیشنهادات', '📖 درباره کتاب', '✍️ درباره نویسنده', '🎧 کتاب صوتی']:
        return
    
    # ذخیره فیش پرداخت
    if message.photo:
        proof = message.photo[-1].file_id
        proof_type = 'photo'
    elif message.document:
        proof = message.document.file_id
        proof_type = 'document'
    else:
        proof = message.text
        proof_type = 'text'
    
    user_data['payments'][user_id] = {
        'proof': proof,
        'type': proof_type,
        'status': 'pending',
        'timestamp': time.time()
    }
    
    # ارسال به ادمین برای تایید
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('✅ تایید', callback_data=f'approve_{user_id}'),
        types.InlineKeyboardButton('❌ رد', callback_data=f'reject_{user_id}')
    )
    
    if proof_type == 'photo':
        bot.send_photo(
            ADMIN_ID, 
            proof,
            caption=f'📸 فیش پرداخت جدید از کاربر {user_id}',
            reply_markup=markup
        )
    elif proof_type == 'document':
        bot.send_document(
            ADMIN_ID,
            proof,
            caption=f'📄 فیش پرداخت جدید از کاربر {user_id}',
            reply_markup=markup
        )
    else:
        bot.send_message(
            ADMIN_ID,
            f'📝 فیش متنی از کاربر {user_id}:\n\n{proof}',
            reply_markup=markup
        )
    
    bot.send_message(
        user_id,
        '✅ فیش پرداخت شما دریافت شد و در حال بررسی است.\n'
        'لطفاً صبور باشید، نتیجه بررسی به شما اعلام خواهد شد.'
    )

# --- مدیریت پاسخ‌های ادمین ---
@bot.callback_query_handler(func=lambda call: True)
def handle_admin_actions(call):
    try:
        action, user_id = call.data.split('_')
        user_id = int(user_id)
        
        if action == 'approve':
            # تایید پرداخت
            user_data['payments'][user_id]['status'] = 'approved'
            
            # ارسال کتاب به کاربر
            try:
                # TODO: اینجا باید فایل کتاب را ارسال کنید
                # با استفاده از bot.send_document(user_id, open('book.pdf', 'rb'))
                bot.send_message(
                    user_id,
                    '✅ پرداخت شما با موفقیت تایید شد!\n'
                    '📚 لینک دانلود کتاب:\n'
                    'https://example.com/download/book.pdf\n\n'
                    'امیدواریم از مطالعه کتاب لذت ببرید!'
                )
                
                # اطلاع به ادمین
                bot.answer_callback_query(call.id, 'پرداخت تایید شد')
                bot.send_message(
                    ADMIN_ID,
                    f'✅ پرداخت کاربر {user_id} تایید و کتاب ارسال شد.'
                )
            except Exception as e:
                logger.error(f'خطا در ارسال کتاب: {e}')
                bot.send_message(
                    ADMIN_ID,
                    f'⚠️ خطا در ارسال کتاب به کاربر {user_id}: {str(e)}'
                )
        
        elif action == 'reject':
            # رد پرداخت
            user_data['payments'][user_id]['status'] = 'rejected'
            
            bot.send_message(
                user_id,
                '❌ متأسفانه پرداخت شما تایید نشد.\n'
                'لطفاً با پشتیبانی تماس بگیرید یا مجدداً اقدام کنید.'
            )
            
            bot.answer_callback_query(call.id, 'پرداخت رد شد')
            bot.send_message(
                ADMIN_ID,
                f'❌ پرداخت کاربر {user_id} رد شد.'
            )
        
        elif action == 'reply':
            # پاسخ به پیام کاربر
            msg = bot.send_message(
                ADMIN_ID,
                f'✍️ لطفاً پاسخ خود به کاربر {user_id} را وارد کنید:'
            )
            bot.register_next_step_handler(msg, lambda m: send_reply(m, user_id))
    
    except Exception as e:
        logger.error(f'خطا در پردازش کال‌بک: {e}')
        bot.answer_callback_query(call.id, 'خطا در پردازش درخواست')

def send_reply(message, user_id):
    try:
        bot.send_message(
            user_id,
            f'📩 پاسخ ادمین به پیام شما:\n\n{message.text}'
        )
        bot.send_message(
            ADMIN_ID,
            f'✅ پاسخ شما به کاربر {user_id} ارسال شد.'
        )
        user_data['feedbacks'][user_id]['replied'] = True
    except Exception as e:
        logger.error(f'خطا در ارسال پاسخ: {e}')
        bot.send_message(
            ADMIN_ID,
            f'⚠️ خطا در ارسال پاسخ به کاربر {user_id}: {str(e)}'
        )

# --- راه‌اندازی سرور ---
def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def run_bot():
    if os.getenv('RENDER'):
        logger.info('حالت تولید: استفاده از وب‌هک')
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    else:
        logger.info('حالت توسعه: استفاده از پولینگ')
        bot.polling()

if __name__ == '__main__':
    # اجرای همزمان Flask و ربات تلگرام
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    run_bot()
