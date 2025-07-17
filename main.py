from flask import Flask, request
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import json
import os

TOKEN = '7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0'
ADMIN_ID = 5542927340
CHANNEL_ID = '@fromheartsoul'

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)
pending_receipts = {}

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def start(update, context):
    user_id = update.effective_user.id
    if not check_subscription(user_id):
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_ID[1:]}")],
                    [InlineKeyboardButton("بررسی عضویت ✅", callback_data='check_membership')]]
        update.message.reply_text("برای استفاده از ربات ابتدا در کانال عضو شوید 👇", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    main_menu(update, context)

def main_menu(update, context):
    keyboard = [
        ['📚 خرید کتاب', '📬 انتقادات و پیشنهادات'],
        ['ℹ️ درباره کتاب', '👤 درباره نویسنده'],
        ['🔊 کتاب صوتی']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    if update.message:
        update.message.reply_text("یکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup)
    elif update.callback_query:
        update.callback_query.message.reply_text("یکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup)

def handle_message(update, context):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == '📚 خرید کتاب':
        update.message.reply_text(
            "شماره کارت:\n5859 8311 3314 0268\n\n"
            "💳 لطفا فیش را همینجا ارسال کنید تا مورد تأیید قرار بگیرد.\n"
            "💰 هزینه کتاب: ۱۱۰ هزار تومان\n"
            "⏳ ممکن است تایید فیش کمی زمان‌بر باشد، لطفا صبور باشید.\n"
            "📘 در صورت تایید، فایل PDF کتاب برایتان ارسال خواهد شد.\n\n"
            "❗ اگر مشکلی داشتید از بخش «انتقادات و پیشنهادات» اقدام کنید."
        )
        context.user_data['awaiting_receipt'] = True

    elif text == '📬 انتقادات و پیشنهادات':
        update.message.reply_text(
            "اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند، "
            "در این بخش بنویسید تا بررسی شود.\n"
            "مطمئن باشید نظرات شما خوانده میشود و باارزش خواهد بود.☺️"
        )
        context.user_data['awaiting_feedback'] = True

    elif text == 'ℹ️ درباره کتاب':
        update.message.reply_text("""رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد...
(ادامه در بخش بعدی فایل)""")

    elif text == '👤 درباره نویسنده':
        update.message.reply_text(
            "سلام رفقا 🙋🏻‍♂\n"
            "مانی محمودی هستم نویسنده کتاب هوژین حرمان...\n"
            "امیدوارم لذت ببرید😄❤️"
        )

    elif text == '🔊 کتاب صوتی':
        update.message.reply_text("🔜 این بخش به زودی فعال می‌شود.")

    else:
        if context.user_data.get('awaiting_feedback'):
            bot.send_message(chat_id=ADMIN_ID, text=f"📬 پیام از کاربر {user_id}:\n{text}")
            update.message.reply_text("پیام شما با موفقیت برای ادمین ارسال شد ✅")
            context.user_data['awaiting_feedback'] = False

def handle_photo_or_text(update, context):
    user_id = update.message.from_user.id
    if context.user_data.get('awaiting_receipt'):
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            caption = f"📥 فیش واریزی از کاربر {user_id}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}_{file_id}")],
                [InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")]
            ])
            bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, reply_markup=keyboard)
        else:
            text = update.message.text
            caption = f"📥 فیش متنی از کاربر {user_id}:\n{text}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}_text")],
                [InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")]
            ])
            bot.send_message(chat_id=ADMIN_ID, text=caption, reply_markup=keyboard)
        update.message.reply_text("فیش شما برای ادمین ارسال شد. منتظر تایید بمانید.")
        context.user_data['awaiting_receipt'] = False

def handle_callback(update, context):
    query = update.callback_query
    data = query.data
    query.answer()

    if data == 'check_membership':
        if check_subscription(query.from_user.id):
            query.edit_message_text("✅ عضویت شما تایید شد.")
            main_menu(update, context)
        else:
            query.edit_message_text("❗ هنوز در کانال عضو نشده‌اید. لطفاً مجدد تلاش کنید.")

    elif data.startswith("approve_"):
        parts = data.split('_')
        user_id = int(parts[1])
        file_type = parts[2]
        if file_type == "text":
            bot.send_message(chat_id=user_id, text="✅ فیش پرداختی شما تایید شد.\n📘 لطفا منتظر بمانید تا فایل کتاب برای شما ارسال شود.")
        else:
            file_id = parts[3]
            bot.send_message(chat_id=user_id, text="✅ فیش پرداختی شما تایید شد.\n📘 لطفا منتظر بمانید تا فایل کتاب برای شما ارسال شود.")
        bot.send_message(chat_id=ADMIN_ID, text=f"لطفاً فایل PDF کتاب را برای کاربر {user_id} ارسال نمایید.")

    elif data.startswith("reject_"):
        user_id = int(data.split('_')[1])
        bot.send_message(chat_id=user_id, text="❌ فیش پرداختی شما مورد تایید قرار نگرفت.\nلطفاً بررسی کرده و مجدد ارسال نمایید.")

def handle_document(update, context):
    if update.message.document:
        if str(update.message.from_user.id) == str(ADMIN_ID):
            if update.message.reply_to_message:
                original_text = update.message.reply_to_message.caption or update.message.reply_to_message.text
                if "کاربر" in original_text:
                    user_id = int(original_text.split('کاربر')[1].split()[0])
                    bot.send_document(chat_id=user_id, document=update.message.document.file_id, caption="📕 این فایل کتاب شماست. با آرزوی مطالعه‌ای دلنشین 🌹")

def setup_dispatcher(dp):
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.photo | Filters.text, handle_photo_or_text))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'ربات فعال است.'

if __name__ == '__main__':
    from telegram.ext import Updater
    from telegram.ext import Dispatcher
    global dispatcher
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    setup_dispatcher(dispatcher)

    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT)

