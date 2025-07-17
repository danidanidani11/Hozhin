from flask import Flask, request
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import os
import json

TOKEN = '7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0'
ADMIN_ID = 5542927340
CHANNEL_USERNAME = '@fromheartsoul'
BOOK_PRICE = '۱۱۰,۰۰۰ تومان'
CARD_NUMBER = '5859 8311 3314 0268'

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# چک عضویت کاربر در کانال
def is_user_member(user_id):
    try:
        member = bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'creator', 'administrator']
    except:
        return False

# منوی اصلی
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📘 خرید کتاب", callback_data='buy')],
        [InlineKeyboardButton("💬 انتقادات و پیشنهادات", callback_data='feedback')],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data='about_book')],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data='about_author')],
        [InlineKeyboardButton("🔒 کتاب صوتی (به زودی)", callback_data='audio')],
    ]
    return InlineKeyboardMarkup(keyboard)

# استارت
def start(update, context):
    user_id = update.effective_user.id
    if not is_user_member(user_id):
        join_button = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال", url=f'https://t.me/{CHANNEL_USERNAME[1:]}')]])
        bot.send_message(chat_id=user_id, text="برای استفاده از ربات ابتدا در کانال عضو شوید:", reply_markup=join_button)
        return

    bot.send_message(chat_id=user_id, text="به ربات رسمی کتاب هوژین و حرمان خوش آمدید 🌸", reply_markup=main_menu())

# هندلر کلیک دکمه‌ها
def button_handler(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    query.answer()

    if not is_user_member(user_id):
        join_button = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال", url=f'https://t.me/{CHANNEL_USERNAME[1:]}')]])
        bot.send_message(chat_id=user_id, text="لطفاً ابتدا در کانال عضو شوید:", reply_markup=join_button)
        return

    if data == 'buy':
        text = f"""📘 برای خرید کتاب، لطفاً مبلغ {BOOK_PRICE} را به شماره کارت زیر واریز کرده و تصویر فیش پرداختی را ارسال کنید:

💳 شماره کارت: {CARD_NUMBER}
🔖 مبلغ: {BOOK_PRICE}

پس از بررسی توسط ادمین، کتاب برای شما ارسال خواهد شد."""
        bot.send_message(chat_id=user_id, text=text)

        context.user_data['waiting_for_receipt'] = True

    elif data == 'feedback':
        bot.send_message(chat_id=user_id, text="✍️ لطفاً نظر، پیشنهاد یا انتقاد خود را ارسال کنید.")
        context.user_data['waiting_for_feedback'] = True

    elif data == 'about_book':
        text = """📖 *درباره کتاب هوژین و حرمان:*

روایتی احساسی و عاشقانه از دلدادگی، دل‌بستگی و جدال بین عشق و سرنوشت. این کتاب در دل خود، صداقت و درونیات انسانی را به تصویر می‌کشد.

نویسنده: مریم نجفی"""
        bot.send_message(chat_id=user_id, text=text, parse_mode='Markdown')

    elif data == 'about_author':
        text = """✍️ *درباره نویسنده:*

مریم نجفی، نویسنده جوان و خوش‌ذوق ایرانی، با قلمی روان و احساسی، توانسته روایت‌هایی عاشقانه و قابل لمس خلق کند که مخاطب را درگیر داستان می‌کند."""
        bot.send_message(chat_id=user_id, text=text, parse_mode='Markdown')

    elif data == 'audio':
        bot.send_message(chat_id=user_id, text="🔒 کتاب صوتی در حال آماده‌سازی است و به زودی در دسترس قرار خواهد گرفت.")

# دریافت پیام‌های متنی یا عکس (فیش یا بازخورد)
def handle_message(update, context):
    user_id = update.effective_user.id

    # فیش خرید
    if context.user_data.get('waiting_for_receipt'):
        msg = update.message
        context.user_data['waiting_for_receipt'] = False

        caption = f"🧾 فیش پرداختی از کاربر:\n\n👤 {msg.from_user.full_name}\n🆔 {msg.from_user.id}"
        if msg.photo:
            photo = msg.photo[-1].file_id
            bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=caption,
                           reply_markup=InlineKeyboardMarkup([
                               [InlineKeyboardButton("✅ تأیید", callback_data=f'approve_{user_id}'),
                                InlineKeyboardButton("❌ رد", callback_data=f'reject_{user_id}')]
                           ]))
            bot.send_message(chat_id=user_id, text="✅ فیش شما ارسال شد و در حال بررسی است. نتیجه به زودی اعلام خواهد شد.")
        else:
            bot.send_message(chat_id=user_id, text="⚠️ لطفاً فقط *تصویر فیش پرداختی* را ارسال کنید.", parse_mode='Markdown')

    # پیام انتقادی/پیشنهادی
    elif context.user_data.get('waiting_for_feedback'):
        context.user_data['waiting_for_feedback'] = False
        feedback_text = update.message.text

        text = f"📩 پیامی از کاربر:\n\n👤 {update.message.from_user.full_name}\n🆔 {user_id}\n📝 متن:\n{feedback_text}"
        bot.send_message(chat_id=ADMIN_ID, text=text)

        bot.send_message(chat_id=user_id, text="✅ پیام شما ارسال شد. در صورت نیاز، پاسخ داده خواهد شد.")

# پاسخ ادمین به فیش‌ها
def admin_decision_handler(update, context):
    query = update.callback_query
    data = query.data
    query.answer()

    if data.startswith('approve_'):
        user_id = int(data.split('_')[1])
        bot.send_message(chat_id=user_id, text="✅ فیش شما با موفقیت تأیید شد. کتاب به زودی برایتان ارسال می‌شود.")
        bot.send_message(chat_id=ADMIN_ID, text=f"📦 ارسال کتاب برای کاربر {user_id} را فراموش نکنید.")
    elif data.startswith('reject_'):
        user_id = int(data.split('_')[1])
        bot.send_message(chat_id=user_id, text="❌ فیش ارسالی شما مورد تأیید قرار نگرفت. لطفاً بررسی و دوباره ارسال کنید.")
        bot.send_message(chat_id=ADMIN_ID, text=f"❗️ فیش کاربر {user_id} رد شد.")

# Flask setup برای Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return "ربات فروش کتاب فعال است."

# تنظیم هندلرها
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CallbackQueryHandler(button_handler))
dispatcher.add_handler(CallbackQueryHandler(admin_decision_handler, pattern='^(approve_|reject_)'))
dispatcher.add_handler(MessageHandler(Filters.all, handle_message))

# راه‌اندازی سرور
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT)
