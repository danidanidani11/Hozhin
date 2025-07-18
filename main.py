import os
import json
from flask import Flask, request
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

TOKEN = '7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0'
CHANNEL_USERNAME = 'fromheartsoul'
ADMIN_ID = 5542927340

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

users_file = 'users.json'

def load_users():
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(users_file, 'w') as f:
        json.dump(data, f)

def check_membership(user_id):
    try:
        member = bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def get_main_menu():
    buttons = [
        ['📘 خرید کتاب', '✉️ انتقادات و پیشنهادات'],
        ['📖 درباره کتاب', '👨‍💼 درباره نویسنده'],
        ['🎧 کتاب صوتی']
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot is running.'

def start(update, context):
    user = update.effective_user
    if not check_membership(user.id):
        join_btn = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}")]])
        update.message.reply_text("برای استفاده از ربات، ابتدا عضو کانال شوید:", reply_markup=join_btn)
        return
    context.bot.send_message(chat_id=update.effective_chat.id, text="به ربات خرید کتاب هوژین و حرمان خوش آمدید.", reply_markup=get_main_menu())

dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))

from telegram.ext import MessageHandler, CallbackQueryHandler

users = load_users()

def handle_text(update, context):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if not check_membership(update.message.from_user.id):
        join_btn = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}")]])
        update.message.reply_text("لطفاً ابتدا عضو کانال شوید:", reply_markup=join_btn)
        return

    if text == '📘 خرید کتاب':
        users[user_id] = {"state": "waiting_for_receipt"}
        save_users(users)
        msg = (
            "💳 شماره کارت: 5859 8311 3314 0268\n\n"
            "لطفا فیش پرداخت را همینجا ارسال کنید تا مورد بررسی قرار بگیرد.\n"
            "💰 هزینه کتاب: ۱۱۰ هزارتومان می‌باشد.\n"
            "⏳ ممکن است تایید فیش کمی زمان‌بر باشد پس لطفا صبور باشید.\n"
            "📕 پس از تأیید، فایل PDF برای شما ارسال خواهد شد.\n"
            "📩 هرگونه مشکل را از بخش «✉️ انتقادات و پیشنهادات» ارسال کنید."
        )
        update.message.reply_text(msg)

    elif text == '✉️ انتقادات و پیشنهادات':
        users[user_id] = {"state": "sending_feedback"}
        save_users(users)
        update.message.reply_text("لطفاً پیشنهاد یا انتقاد خود را بنویسید و ارسال کنید.\nنظرات شما برای ما باارزش است ☺️")

    elif text == '📖 درباره کتاب':
        book_info = (
            "رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است...\n\n"
            "نام هوژین واژه‌ای کردی است که تعبیر آن کسی است که با آمدنش نور زندگی شما می‌شود...\n\n"
            "اگر در میان بندهای کتاب شعری را مشاهده کردید؛ آن ابیات توسط شاعران فرهیخته نوشته شده‌اند...\n"
            "در صورت خرید امیدوارم لذت ببرید."
        )
        update.message.reply_text(book_info)

    elif text == '👨‍💼 درباره نویسنده':
        author_info = (
            "سلام رفقا 🙋🏻‍♂\n"
            "مانی محمودی هستم نویسنده کتاب هوژین حرمان.\n"
            "نویسنده‌ای جوان هستم که با کنار هم گذاشتن نامه‌ها موفق به نوشتن این کتاب شدم...\n"
            "امیدوارم لذت ببرید 😄❤️"
        )
        update.message.reply_text(author_info)

    elif text == '🎧 کتاب صوتی':
        update.message.reply_text("این بخش به زودی فعال می‌شود.")

    elif user_id in users and users[user_id].get("state") == "sending_feedback":
        context.bot.send_message(chat_id=ADMIN_ID, text=f"📬 پیام از {user_id}:\n{text}",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton("✉️ پاسخ دادن", callback_data=f"reply_{user_id}")]
                                 ]))
        update.message.reply_text("✅ پیام شما با موفقیت ارسال شد.")
        users[user_id]["state"] = None
        save_users(users)

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

def handle_media(update, context):
    user_id = str(update.message.from_user.id)

    if user_id in users and users[user_id].get("state") == "waiting_for_receipt":
        caption = f"🧾 فیش پرداخت از کاربر {user_id}\n\nبرای تأیید روی ✅ یا رد روی ❌ کلیک کنید."
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{user_id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")
            ]
        ])
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, reply_markup=keyboard)
        elif update.message.text:
            context.bot.send_message(chat_id=ADMIN_ID, text=caption + f"\n\nمتن فیش:\n{update.message.text}", reply_markup=keyboard)

        update.message.reply_text("✅ فیش شما با موفقیت ارسال شد. منتظر بررسی توسط ادمین باشید.")
        users[user_id]["state"] = None
        save_users(users)

def handle_callback(update, context):
    query = update.callback_query
    data = query.data
    query.answer()

    if data.startswith("confirm_"):
        user_id = data.split("_")[1]
        context.bot.send_message(chat_id=int(user_id),
                                 text="✅ فیش شما تایید شد. لطفاً منتظر دریافت فایل PDF کتاب باشید.")
        context.bot.send_message(chat_id=ADMIN_ID,
                                 text=f"کاربر {user_id} تایید شد. لطفاً فایل کتاب را برای او ارسال کنید.")

    elif data.startswith("reject_"):
        user_id = data.split("_")[1]
        context.bot.send_message(chat_id=int(user_id),
                                 text="❌ فیش شما تایید نشد. لطفاً بررسی کرده و دوباره ارسال کنید.")

    elif data.startswith("reply_"):
        user_id = data.split("_")[1]
        context.bot.send_message(chat_id=ADMIN_ID,
                                 text=f"لطفاً پاسخ خود را برای کاربر {user_id} بنویسید:")
        users[str(query.from_user.id)] = {"state": f"replying_to_{user_id}"}
        save_users(users)

def handle_admin_reply(update, context):
    admin_id = str(update.message.from_user.id)
    if admin_id not in users:
        return

    state = users[admin_id].get("state", "")
    if state and state.startswith("replying_to_"):
        target_id = state.split("_")[2]
        context.bot.send_message(chat_id=int(target_id), text=f"✉️ پاسخ ادمین:\n{update.message.text}")
        update.message.reply_text("✅ پاسخ برای کاربر ارسال شد.")
        users[admin_id]["state"] = None
        save_users(users)

dispatcher.add_handler(MessageHandler(Filters.photo | Filters.text & ~Filters.command, handle_media))
dispatcher.add_handler(CallbackQueryHandler(handle_callback))
dispatcher.add_handler(MessageHandler(Filters.text & Filters.user(user_id=ADMIN_ID), handle_admin_reply))
