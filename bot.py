import telebot
from telebot import types

# تنظیمات اصلی
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL = "fromheartsoul"  # بدون @
CARD_NUMBER = "5859 8311 3314 0268"
BOOK_PRICE = "110 هزارتومان"

# ایجاد ربات
bot = telebot.TeleBot(TOKEN)

# دیکشنری‌های ذخیره اطلاعات
user_payments = {}  # {user_id: {"payment_proof": photo/file, "status": "pending"}}
user_messages = {}   # برای انتقادات و پیشنهادات

# بررسی عضویت کاربر در کانال
def check_membership(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# صفحه اصلی
def main_menu(user_id):
    if not check_membership(user_id):
        bot.send_message(user_id, f"⚠️ برای استفاده از ربات، باید در کانال ما عضو شوید:\n@{CHANNEL}")
        return
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📕 خرید کتاب')
    btn2 = types.KeyboardButton('💬 انتقادات و پیشنهادات')
    btn3 = types.KeyboardButton('📖 درباره کتاب')
    btn4 = types.KeyboardButton('✍️ درباره نویسنده')
    btn5 = types.KeyboardButton('🎧 کتاب صوتی (به زودی)')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(user_id, "منوی اصلی:", reply_markup=markup)

# دستور /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if check_membership(message.from_user.id):
        main_menu(message.from_user.id)
    else:
        bot.send_message(message.from_user.id, f"سلام! برای استفاده از ربات، لطفا در کانال ما عضو شوید:\n@{CHANNEL}\nسپس /start را دوباره بزنید.")

# پردازش پیام‌های متنی
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    
    if not check_membership(user_id):
        bot.send_message(user_id, f"⚠️ لطفا ابتدا در کانال ما عضو شوید:\n@{CHANNEL}")
        return
    
    if message.text == '📕 خرید کتاب':
        msg = f"""
📌 اطلاعات پرداخت:
شماره کارت: {CARD_NUMBER}
مبلغ: {BOOK_PRICE}

لطفا پس از واریز، فیش پرداخت (عکس یا متن) را همینجا ارسال کنید.

⚠️ توجه:
- پس از تایید پرداخت، فایل کتاب برای شما ارسال می‌شود.
- ممکن است تایید پرداخت کمی زمان‌بر باشد.
- در صورت مشکل، از بخش انتقادات و پیشنهادات پیام بدهید.
"""
        bot.send_message(user_id, msg)
    
    elif message.text == '💬 انتقادات و پیشنهادات':
        msg = """
اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند، لطفا پیام خود را ارسال کنید.

مطمئن باشید نظرات شما خوانده می‌شود و باارزش خواهد بود. ☺️
"""
        sent = bot.send_message(user_id, msg)
        bot.register_next_step_handler(sent, process_feedback)
    
    elif message.text == '📖 درباره کتاب':
        about_book = """
📚 رمان هوژین و حرمان:
روایتی عاشقانه با تلفیق سبک‌های سورئالیسم، رئالیسم و روان‌شناختی.

🔹 هوژین: واژه‌ای کردی به معنای "نور زندگی" و نماد امید
🔹 حرمان: نماد اندوه و افسردگی عمیق

📖 روش مطالعه:
- بار اول: بخش 1 → 2 → 3
- بار دوم: بخش 2 → 1 → 3
(برای دریافت دو برداشت متفاوت)

📜 نکات:
- برخی بخش‌ها بر اساس واقعیت هستند
- اشعار از شاعران ایرانی انتخاب شده‌اند
- مطالب داخل «» از نامه‌ها یا بیت‌های کوتاه الهام گرفته شده‌اند
"""
        bot.send_message(user_id, about_book)
    
    elif message.text == '✍️ درباره نویسنده':
        about_author = """
سلام رفقا! 🙋🏻‍♂
مانی محمودی، نویسنده کتاب هوژین و حرمان.

🔹 شروع نویسندگی از 13 سالگی
🔹 اولین اثر: هوژین و حرمان
🔹 در حال نوشتن آثار جدید

امیدوارم از کتاب لذت ببرید! 😊❤️
"""
        bot.send_message(user_id, about_author)
    
    elif message.text == '🎧 کتاب صوتی (به زودی)':
        bot.send_message(user_id, "بخش کتاب صوتی به زودی فعال خواهد شد. ⏳")

# پردازش فیش پرداخت
@bot.message_handler(content_types=['photo', 'document', 'text'])
def handle_payment_proof(message):
    user_id = message.from_user.id
    
    if message.text and not message.text.startswith(('📕', '💬', '📖', '✍️', '🎧')):
        # اگر پیام متنی معمولی است (ممکن است فیش متنی باشد)
        if user_id in user_payments and user_payments[user_id]['status'] == 'pending':
            user_payments[user_id]['payment_proof'] = message.text
            
            # ارسال به ادمین برای تایید
            markup = types.InlineKeyboardMarkup()
            btn_approve = types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}")
            btn_reject = types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")
            markup.add(btn_approve, btn_reject)
            
            bot.send_message(ADMIN_ID, f"📩 فیش پرداخت جدید از کاربر {user_id}:\n\n{message.text}", reply_markup=markup)
            bot.send_message(user_id, "فیش پرداخت شما برای تایید ارسال شد. لطفا منتظر بمانید.")
    
    elif message.photo or message.document:
        # اگر کاربر عکس یا فایل ارسال کرده (فیش پرداخت)
        user_payments[user_id] = {
            "payment_proof": message.photo[0].file_id if message.photo else message.document.file_id,
            "type": "photo" if message.photo else "document",
            "status": "pending"
        }
        
        # ارسال به ادمین برای تایید
        markup = types.InlineKeyboardMarkup()
        btn_approve = types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}")
        btn_reject = types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")
        markup.add(btn_approve, btn_reject)
        
        if message.photo:
            bot.send_photo(ADMIN_ID, message.photo[0].file_id, 
                          caption=f"📸 فیش پرداخت جدید از کاربر {user_id}", 
                          reply_markup=markup)
        else:
            bot.send_document(ADMIN_ID, message.document.file_id,
                            caption=f"📄 فیش پرداخت جدید از کاربر {user_id}", 
                            reply_markup=markup)
        
        bot.send_message(user_id, "فیش پرداخت شما برای تایید ارسال شد. لطفا منتظر بمانید.")

# پردازش انتقادات و پیشنهادات
def process_feedback(message):
    user_id = message.from_user.id
    user_messages[user_id] = message.text
    
    # ارسال به ادمین با امکان پاسخ
    markup = types.InlineKeyboardMarkup()
    btn_reply = types.InlineKeyboardButton("✍️ پاسخ", callback_data=f"reply_{user_id}")
    markup.add(btn_reply)
    
    bot.send_message(ADMIN_ID, f"📝 پیام جدید از کاربر {user_id}:\n\n{message.text}", reply_markup=markup)
    bot.send_message(user_id, "پیام شما با موفقیت ارسال شد. با تشکر از نظر شما!")

# پردازش کلیک روی دکمه‌های اینلاین
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    action, user_id = call.data.split('_')
    user_id = int(user_id)
    
    if action == "approve":
        # تایید پرداخت توسط ادمین
        user_payments[user_id]['status'] = 'approved'
        bot.send_message(ADMIN_ID, f"✅ پرداخت کاربر {user_id} تایید شد.")
        
        # ارسال پیام به کاربر
        bot.send_message(user_id, "✅ پرداخت شما تایید شد. لطفا فایل کتاب را دریافت کنید:")
        # TODO: اینجا باید فایل کتاب را ارسال کنید
        # bot.send_document(user_id, open('book.pdf', 'rb'))
        
        # حذف از لیست pending
        del user_payments[user_id]
    
    elif action == "reject":
        # رد پرداخت توسط ادمین
        user_payments[user_id]['status'] = 'rejected'
        bot.send_message(ADMIN_ID, f"❌ پرداخت کاربر {user_id} رد شد.")
        bot.send_message(user_id, "❌ متاسفانه پرداخت شما تایید نشد. لطفا دوباره تلاش کنید.")
        del user_payments[user_id]
    
    elif action == "reply":
        # پاسخ به پیام کاربر
        sent = bot.send_message(ADMIN_ID, "لطفا پاسخ خود را وارد کنید:")
        bot.register_next_step_handler(sent, lambda m: send_reply(m, user_id))

# ارسال پاسخ ادمین به کاربر
def send_reply(message, user_id):
    bot.send_message(user_id, f"📩 پاسخ ادمین به پیام شما:\n\n{message.text}")
    bot.send_message(ADMIN_ID, "✅ پاسخ شما ارسال شد.")

# شروع ربات
print("✅ ربات فعال شد!")
bot.polling()
