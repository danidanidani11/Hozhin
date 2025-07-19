import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import asyncio
from threading import Thread

# تنظیمات پایه
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"
WEBHOOK_URL = "https://hozhin.onrender.com"
PDF_PATH = "books/hozhin_harman.pdf"

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# متون فارسی
TEXTS = {
    'start': 'سلام! به ربات کتاب هوژین و حرمان خوش آمدید. لطفاً گزینه مورد نظر را انتخاب کنید:',
    'buy': '''📚 خرید کتاب هوژین و حرمان

💳 شماره کارت: 5859 8311 3314 0268
💰 هزینه کتاب: 110,000 تومان

لطفا فیش پرداخت را همینجا ارسال کنید تا مورد تایید قرار بگیرد.
ممکن است تایید فیش کمی زمان‌بر باشد پس لطفا صبور باشید.
در صورت تایید فایل PDF برایتان ارسال میشود.
''',
    'suggestion': '''💌 انتقادات و پیشنهادات

اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند حتما در این بخش بنویسید تا بررسی شود.
مطمئن باشید نظرات شما خوانده میشود و باارزش خواهد بود. ☺️
''',
    'about_book': '''📖 درباره کتاب

رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد.نام هوژین واژه ای کردی است که تعبیر آن کسی است که با آمدنش نور زندگی شما میشود و زندگی را تازه میکند؛در معنای کلی امید را به شما برمیگرداند.حرمان نیز واژه ای کردی_عربی است که معنای آن در وصف کسی است که بالاترین حد اندوه و افسردگی را تجربه کرده و با این حال آن را رها کرده است.در تعبیری مناسب تر؛هوژین در کتاب برای حرمان روزنه نور و امیدی بوده است که باعث رهایی حرمان از غم و اندوه میشود و دلیل اصلی رهایی برای حرمان تلقی میشود.کاژه هم به معنای کسی است که در کنار او احساس امنیت دارید. 

[متن کامل درباره کتاب...]
''',
    'about_author': '''✍️ درباره نویسنده

سلام رفقا 🙋🏻‍♂
مانی محمودی هستم نویسنده کتاب هوژین حرمان.
نویسنده ای جوان هستم که با کنار هم گذاشتن نامه های متعدد موفق به نوشتن این کتاب شدم.کار نویسندگی را از سن ۱۳ سالگی با کمک معلم ادبیاتم شروع کردم و تا امروز به این کار را ادامه می‌دهم.این کتاب اولین اثر بنده هستش و در تلاش هستم تا در طی سالیان آینده کتاب های بیشتری خلق کنم.

بیشتر از این وقتتون رو نمیگیرم.امیدوار لذت ببرید😄❤️
''',
    'audio': '🔊 کتاب صوتی\n\nاین بخش به زودی فعال میشود',
    'payment_received': '✅ فیش پرداخت شما دریافت شد و برای تایید به ادمین ارسال شد.',
    'suggestion_received': '🙏 سپاس از نظر شما! پیام شما به ادمین ارسال شد.',
    'payment_approved': '✅ پرداخت شما تایید شد! لینک دانلود کتاب:\n[فایل PDF ارسال شد]',
    'payment_rejected': '❌ متاسفانه پرداخت شما تایید نشد. لطفا مجددا تلاش کنید.'
}

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 خرید کتاب", callback_data="buy_book")],
        [InlineKeyboardButton("💬 انتقادات و پیشنهادات", callback_data="suggestion")],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🔊 کتاب صوتی", callback_data="audio_book")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_approval_keyboard(user_id, msg_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"approve_{user_id}_{msg_id}"),
            InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{user_id}_{msg_id}")
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TEXTS['start'], reply_markup=main_menu())

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except:
        pass

    if query.data == "buy_book":
        await query.edit_message_text(TEXTS['buy'])
        context.user_data['state'] = 'waiting_payment'
    
    elif query.data == "suggestion":
        await query.edit_message_text(TEXTS['suggestion'])
        context.user_data['state'] = 'waiting_suggestion'
    
    elif query.data == "about_book":
        await query.edit_message_text(TEXTS['about_book'], reply_markup=main_menu())
    
    elif query.data == "about_author":
        await query.edit_message_text(TEXTS['about_author'], reply_markup=main_menu())
    
    elif query.data == "audio_book":
        await query.edit_message_text(TEXTS['audio'], reply_markup=main_menu())

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state = context.user_data.get('state')
    
    if user_state == 'waiting_payment' and (update.message.photo or update.message.text):
        # ارسال فیش به ادمین
        if update.message.photo:
            receipt_msg = await update.message.forward(chat_id=ADMIN_ID)
        else:
            receipt_msg = await update.message.copy(chat_id=ADMIN_ID)
        
        # ارسال کیبورد تایید/رد به ادمین
        await application.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💸 فیش پرداخت جدید از کاربر {update.effective_user.id}",
            reply_markup=admin_approval_keyboard(
                user_id=update.effective_user.id,
                msg_id=receipt_msg.message_id
            )
        )
        
        await update.message.reply_text(TEXTS['payment_received'])
        context.user_data['state'] = None
    
    elif user_state == 'waiting_suggestion':
        await application.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📝 نظر جدید از کاربر {update.effective_user.id}:\n\n{update.message.text}"
        )
        await update.message.reply_text(TEXTS['suggestion_received'])
        context.user_data['state'] = None

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_id, msg_id = query.data.split('_')
    
    try:
        if action == "approve":
            # ارسال کتاب به کاربر
            if os.path.exists(PDF_PATH):
                with open(PDF_PATH, 'rb') as pdf_file:
                    await application.bot.send_document(
                        chat_id=int(user_id),
                        document=pdf_file,
                        caption=TEXTS['payment_approved']
                    )
            
            await query.edit_message_text(f"✅ پرداخت کاربر {user_id} تایید شد")
        
        elif action == "reject":
            # ارسال پیام رد به کاربر
            await application.bot.send_message(
                chat_id=int(user_id),
                text=TEXTS['payment_rejected']
            )
            await query.edit_message_text(f"❌ پرداخت کاربر {user_id} رد شد")
        
        # حذف پیام فیش از چت ادمین
        await application.bot.delete_message(
            chat_id=ADMIN_ID,
            message_id=int(msg_id)
        )
        
    except Exception as e:
        logger.error(f"خطا در پردازش تایید/رد: {e}")

# تنظیم هندلرها
application.add_handler(CommandHandler('start', start))
application.add_handler(CallbackQueryHandler(handle_buttons))
application.add_handler(CallbackQueryHandler(handle_approval, pattern=r"^(approve|reject)_"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
application.add_handler(MessageHandler(filters.PHOTO, handle_messages))

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(), application.bot)
        Thread(target=lambda: asyncio.run(application.process_update(update))).start()
        return {'status': 'ok'}
    except Exception as e:
        logger.error(f'خطا در وب‌هوک: {e}')
        return {'status': 'error'}, 500

@app.route('/')
def home():
    return "ربات کتاب هوژین و حرمان در حال اجراست"

def setup_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.bot.set_webhook(f'{WEBHOOK_URL}/{TOKEN}'))
        logger.info("ربات با موفقیت راه‌اندازی شد")
    except Exception as e:
        logger.error(f"خطا در راه‌اندازی ربات: {e}")
    finally:
        loop.close()

if __name__ == '__main__':
    setup_bot()
    app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)
