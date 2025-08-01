import os
from flask import Flask, request
import telebot
from telebot import types

TOKEN = '7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0'
ADMIN_ID = 1383555301
CHANNEL_USERNAME = 'fromheartsoul'
PDF_PATH = 'books/hozhin_harman.pdf'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_state = {}
conversations = {}  # ذخیره مکالمات بین کاربر و ادمین

# --- توابع جدید برای عضویت اجباری ---
def check_membership(user_id):
    try:
        chat = bot.get_chat(f"@{CHANNEL_USERNAME}")
        if chat.type != "channel":
            print("⚠️ آدرس وارد شده یک کانال نیست!")
            return False
            
        member = bot.get_chat_member(chat.id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"خطا در بررسی عضویت: {e}")
        return False

def get_channel_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}"),
        types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_subscription")
    )
    return markup

# --- دکمه‌ها ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📖 خرید کتاب", "🗣️ انتقادات و پیشنهادات")
    markup.add("ℹ️ درباره کتاب", "✍️ درباره نویسنده")
    markup.add("🔊 کتاب صوتی (بزودی)")
    return markup

def get_back_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 بازگشت به منو")
    return markup

def get_reply_keyboard(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✍️ پاسخ", callback_data=f"reply_{user_id}"))
    return markup

# --- استارت با بررسی عضویت ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    if not check_membership(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"⚠️ برای استفاده از ربات، لطفاً در کانال ما عضو شوید:\n@{CHANNEL_USERNAME}",
            reply_markup=get_channel_keyboard()
        )
        return
    
    bot.send_message(
        message.chat.id,
        "به ربات فروش کتاب «هوژین و حرمان» خوش آمدید 🌸",
        reply_markup=get_main_keyboard()
    )

# --- هندلر بررسی عضویت ---
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def verify_subscription(call):
    if check_membership(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            "به ربات فروش کتاب «هوژین و حرمان» خوش آمدید 🌸",
            reply_markup=get_main_keyboard()
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ هنوز در کانال عضو نشده‌اید! لطفاً ابتدا عضویت را تکمیل کنید.",
            show_alert=True
        )

# --- خرید کتاب با بررسی عضویت ---
@bot.message_handler(func=lambda msg: msg.text == "📖 خرید کتاب")
def buy_book(message):
    if not check_membership(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"⚠️ برای خرید کتاب، لطفاً در کانال ما عضو شوید:\n@{CHANNEL_USERNAME}",
            reply_markup=get_channel_keyboard()
        )
        return
        
    user_state[message.chat.id] = 'awaiting_receipt'
    bot.send_message(message.chat.id, """5859 8311 3314 0268
لطفا فیش رو همینجا ارسال کنید تا مورد تایید قرار بگیرد.هزینه کتاب ۱۱۰ هزارتومان میباشد.
ممکن است تایید فیش کمی زمان‌بر باشد پس لطفا صبور باشید.
در صورت تایید فایل پی دی اف برایتان در همینجا ارسال میشود.
اگر هرگونه مشکلی برایتان پیش آمد در بخش انتقادات و پیشنهادات برای ما ارسال کنید تا بررسی شود.""", reply_markup=get_back_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "🔙 بازگشت به منو")
def back_to_menu(message):
    if message.chat.id in user_state:
        user_state.pop(message.chat.id)
    bot.send_message(message.chat.id, "منوی اصلی:", reply_markup=get_main_keyboard())

@bot.message_handler(content_types=['text', 'photo'], func=lambda msg: user_state.get(msg.chat.id) == 'awaiting_receipt')
def handle_receipt(message):
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
    bot.send_message(message.chat.id, "رسید شما برای بررسی ارسال شد ✅", reply_markup=get_main_keyboard())

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

# --- انتقادات و پیشنهادات با بررسی عضویت ---
@bot.message_handler(func=lambda msg: msg.text == "🗣️ انتقادات و پیشنهادات")
def suggestions(message):
    if not check_membership(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"⚠️ برای استفاده از این بخش، لطفاً در کانال ما عضو شوید:\n@{CHANNEL_USERNAME}",
            reply_markup=get_channel_keyboard()
        )
        return
        
    user_state[message.chat.id] = 'awaiting_feedback'
    bot.send_message(message.chat.id, """اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند حتما در این بخش بنویسید تا بررسی شود
مطمئن باشید نظرات شما خوانده میشود و باارزش خواهد بود.☺️""", reply_markup=get_back_keyboard())

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id) == 'awaiting_feedback')
def receive_feedback(message):
    user_state.pop(message.chat.id)
    feedback_msg = bot.send_message(
        ADMIN_ID, 
        f"📩 پیام جدید از کاربر {message.from_user.id}:\n\n{message.text}",
        reply_markup=get_reply_keyboard(message.from_user.id)
    )
    
    # ذخیره اطلاعات مکالمه
    conversations[message.from_user.id] = {
        'last_admin_msg_id': feedback_msg.message_id,
        'last_user_msg_id': message.message_id
    }
    
    bot.send_message(
        message.chat.id, 
        "✅ پیام شما ارسال شد. ممنون از همراهی‌تان.", 
        reply_markup=get_main_keyboard()
    )

# --- مدیریت پاسخ ادمین به کاربر ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def handle_admin_reply(call):
    user_id = int(call.data.split("_")[1])
    bot.answer_callback_query(call.id)
    
    # تنظیم وضعیت برای پاسخ ادمین
    user_state[call.from_user.id] = f'admin_reply_{user_id}'
    bot.send_message(
        ADMIN_ID,
        f"لطفا پاسخ خود را برای کاربر {user_id} ارسال کنید:",
        reply_markup=types.ForceReply(selective=True)
    )

# --- دریافت پاسخ ادمین و ارسال به کاربر ---
@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and msg.reply_to_message and 'لطفا پاسخ خود را برای کاربر' in msg.reply_to_message.text)
def send_admin_reply(message):
    try:
        # استخراج شناسه کاربر از پیام
        user_id = int(message.reply_to_message.text.split()[-1])
        
        # ارسال پاسخ به کاربر
        bot.send_message(
            user_id,
            f"📩 پاسخ ادمین به پیام شما:\n\n{message.text}",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("✍️ پاسخ", callback_data="reply_to_admin")
            )
        )
        
        # ذخیره اطلاعات مکالمه
        if user_id not in conversations:
            conversations[user_id] = {}
            
        conversations[user_id]['last_admin_msg_id'] = message.message_id
        
        bot.send_message(
            ADMIN_ID,
            f"✅ پاسخ شما برای کاربر {user_id} ارسال شد."
        )
        
        # حذف وضعیت پاسخ
        if f'admin_reply_{user_id}' in user_state.values():
            for key, value in list(user_state.items()):
                if value == f'admin_reply_{user_id}':
                    user_state.pop(key)
                    break
                    
    except Exception as e:
        bot.send_message(ADMIN_ID, f"خطا در ارسال پاسخ: {e}")

# --- مدیریت پاسخ کاربر به ادمین ---
@bot.callback_query_handler(func=lambda call: call.data == "reply_to_admin")
def handle_user_reply(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    
    # تنظیم وضعیت برای پاسخ کاربر
    user_state[user_id] = 'user_reply_to_admin'
    
    bot.send_message(
        user_id,
        "لطفا پاسخ خود را ارسال کنید:",
        reply_markup=types.ForceReply(selective=True)
    )

# --- دریافت پاسخ کاربر و ارسال به ادمین ---
@bot.message_handler(func=lambda msg: msg.from_user.id in user_state and user_state[msg.from_user.id] == 'user_reply_to_admin')
def send_user_reply(message):
    user_id = message.from_user.id
    user_state.pop(user_id)
    
    # ارسال پاسخ به ادمین
    bot.send_message(
        ADMIN_ID,
        f"📩 پاسخ کاربر {user_id}:\n\n{message.text}",
        reply_markup=get_reply_keyboard(user_id)
    )
    
    # ذخیره اطلاعات مکالمه
    if user_id not in conversations:
        conversations[user_id] = {}
        
    conversations[user_id]['last_user_msg_id'] = message.message_id
    
    bot.send_message(
        user_id,
        "✅ پاسخ شما ارسال شد.",
        reply_markup=get_main_keyboard()
    )

# --- درباره کتاب با بررسی عضویت ---
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ درباره کتاب")
def about_book(message):
    if not check_membership(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"⚠️ برای مشاهده اطلاعات کتاب، لطفاً در کانال ما عضو شوید:\n@{CHANNEL_USERNAME}",
            reply_markup=get_channel_keyboard()
        )
        return
    
    bot.send_message(message.chat.id, """رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد.نام هوژین واژه ای کردی است که تعبیر آن کسی است که با آمدنش نور زندگی شما میشود و زندگی را تازه میکند؛در معنای کلی امید را به شما برمیگرداند.حرمان نیز واژه ای کردی_عربی است که معنای آن در وصف کسی است که بالاترین حد اندوه و افسردگی را تجربه کرده و با این حال آن را رها کرده است.در تعبیری مناسب تر؛هوژین در کتاب برای حرمان روزنه نور و امیدی بوده است که باعث رهایی حرمان از غم و اندوه میشود و دلیل اصلی رهایی برای حرمان تلقی میشود.کاژه هم به معنای کسی است که در کنار او احساس امنیت دارید. 
کتاب از نگاه اول شخص روایت میشود و پیشنهاد من این است که ابتدا کتاب را به ترتیب از بخش اول تا سوم بخوانید؛اما اگر علاقه داشتید مجدداً آن را مطالعه کنید،برای بار دوم، ابتدا بخش دوم و سپس بخش اول و در آخر بخش سوم را بخوانید.در این صورت دو برداشت متفاوت از کتاب خواهید داشت که هر کدام زاویه نگاه متفاوتی در شما به وجود می آورد. 
برخی بخش ها و تجربه های کتاب بر اساس داستان واقعی روایت شده و برخی هم سناریوهای خیالی و خاص همراه بوده است که دانستن آن برای شما خالی از لطف نیست.یک سری نکات شایان ذکر است که به عنوان  خواننده کتاب حق دارید بدانید.اگر در میان بند های کتاب شعری را مشاهده کردید؛آن ابیات توسط شاعران فرهیخته کشور عزیزمان ایران نوشته شده است و با تحقیق و جست و جو میتوانید متن کامل و نام نویسنده را دریابید.اگر مطلبی را داخل "این کادر" دیدید به معنای این است که آن مطلب احتمالا برگرفته از نامه ها یا بیت های کوتاه است.در آخر هم اگر جملاتی را مشاهده کردید که از قول فلانی روایت شده است و مانند آن را قبلا شنیده اید؛احتمالا برگرفته از مطالبی است که ملکه ذهن من بوده و آنها را در طول کتاب استفاده کرده ام.

درصورت خرید امیدوارم لذت ببرید.""")

# --- درباره نویسنده با بررسی عضویت ---
@bot.message_handler(func=lambda msg: msg.text == "✍️ درباره نویسنده")
def about_author(message):
    if not check_membership(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"⚠️ برای مشاهده اطلاعات نویسنده، لطفاً در کانال ما عضو شوید:\n@{CHANNEL_USERNAME}",
            reply_markup=get_channel_keyboard()
        )
        return
    
    bot.send_message(message.chat.id, """سلام رفقا 🙋🏻‍♂
مانی محمودی هستم نویسنده کتاب هوژین حرمان.
نویسنده ای جوان هستم که با کنار هم گذاشتن نامه های متعدد موفق به نوشتن این کتاب شدم.کار نویسندگی را از سن ۱۳ سالگی با کمک معلم ادبیاتم شروع کردم و تا امروز به این کار را ادامه می‌دهم.این کتاب اولین اثر بنده هستش و در تلاش هستم تا در طی سالیان آینده کتاب های بیشتری خلق کنم.

بیشتر از این وقتتون رو نمیگیرم.امیدوار لذت ببرید😄❤️""")

# --- کتاب صوتی با بررسی عضویت ---
@bot.message_handler(func=lambda msg: msg.text == "🔊 کتاب صوتی (بزودی)")
def audio_book(message):
    if not check_membership(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"⚠️ برای استفاده از این بخش، لطفاً در کانال ما عضو شوید:\n@{CHANNEL_USERNAME}",
            reply_markup=get_channel_keyboard()
        )
        return
    
    bot.send_message(message.chat.id, "این بخش بزودی فعال می‌شود")

# --- Fallback handler for debugging ---
@bot.message_handler(content_types=['text'])
def handle_unmatched(message):
    bot.send_message(message.chat.id, f"دستور نامعتبر: {message.text}. لطفاً از دکمه‌های منو استفاده کنید.")
    bot.send_message(ADMIN_ID, f"پیام نامعتبر از {message.from_user.id}: {message.text}")

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
    bot.remove_webhook()
    bot.set_webhook(url='https://hozhin.onrender.com')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
