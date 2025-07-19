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
        "به ربات فروش کتاب «هوژین و حرمان» خوش آمدید 🌸",
        reply_markup=get_main_keyboard()
    )

# --- خرید کتاب ---
@bot.message_handler(func=lambda msg: msg.text == "📖 خرید کتاب")
def buy_book(message):
    user_state[message.chat.id] = 'awaiting_receipt'
    bot.send_message(message.chat.id, "لطفاً رسید پرداخت خود را ارسال کنید (عکس یا متن).")

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

# --- درباره کتاب ---
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ درباره کتاب")
def about_book(message):
    bot.send_message(message.chat.id, "رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد.نام هوژین واژه ای کردی است که تعبیر آن کسی است که با آمدنش نور زندگی شما میشود و زندگی را تازه میکند؛در معنای کلی امید را به شما برمیگرداند.حرمان نیز واژه ای کردی_عربی است که معنای آن در وصف کسی است که بالاترین حد اندوه و افسردگی را تجربه کرده و با این حال آن را رها کرده است.در تعبیری مناسب تر؛هوژین در کتاب برای حرمان روزنه نور و امیدی بوده است که باعث رهایی حرمان از غم و اندوه میشود و دلیل اصلی رهایی برای حرمان تلقی میشود.کاژه هم به معنای کسی است که در کنار او احساس امنیت دارید. 
کتاب از نگاه اول شخص روایت میشود و پیشنهاد من این است که ابتدا کتاب را به ترتیب از بخش اول تا سوم بخوانید؛اما اگر علاقه داشتید مجدداً آن را مطالعه کنید،برای بار دوم، ابتدا بخش دوم و سپس بخش اول و در آخر بخش سوم را بخوانید.در این صورت دو برداشت متفاوت از کتاب خواهید داشت که هر کدام زاویه نگاه متفاوتی در شما به وجود می آورد. 
برخی بخش ها و تجربه های کتاب بر اساس داستان واقعی روایت شده و برخی هم سناریوهای خیالی و خاص همراه بوده است که دانستن آن برای شما خالی از لطف نیست.یک سری نکات شایان ذکر است که به عنوان  خواننده کتاب حق دارید بدانید.اگر در میان بند های کتاب شعری را مشاهده کردید؛آن ابیات توسط شاعران فرهیخته کشور عزیزمان ایران نوشته شده است و با تحقیق و جست و جو میتوانید متن کامل و نام نویسنده را دریابید.اگر مطلبی را داخل "این کادر" دیدید به معنای این است که آن مطلب احتمالا برگرفته از نامه ها یا بیت های کوتاه است.در آخر هم اگر جملاتی را مشاهده کردید که از قول فلانی روایت شده است و مانند آن را قبلا شنیده اید؛احتمالا برگرفته از مطالبی است که ملکه ذهن من بوده و آنها را در طول کتاب استفاده کرده ام.

درصورت خرید امیدوارم لذت ببرید.")

# --- درباره نویسنده ---
@bot.message_handler(func=lambda msg: msg.text == "✍️ درباره نویسنده")
def about_author(message):
    bot.send_message(message.chat.id, "سلام رفقا 🙋🏻‍♂
مانی محمودی هستم نویسنده کتاب هوژین حرمان.
نویسنده ای جوان هستم که با کنار هم گذاشتن نامه های متعدد موفق به نوشتن این کتاب شدم.کار نویسندگی را از سن ۱۳ سالگی با کمک معلم ادبیاتم شروع کردم و تا امروز به این کار را ادامه می‌دهم.این کتاب اولین اثر بنده هستش و در تلاش هستم تا در طی سالیان آینده کتاب های بیشتری خلق کنم.

بیشتر از این وقتتون رو نمیگیرم.امیدوار لذت ببرید😄❤️")

# --- کتاب صوتی ---
@bot.message_handler(func=lambda msg: msg.text == "🔊 کتاب صوتی (بزودی)")
def audio_book(message):
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
