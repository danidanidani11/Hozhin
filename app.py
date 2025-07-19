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

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تنظیمات اصلی
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
PDF_PATH = "hozhin_harman.pdf"  # فایل باید در همان پوشه باشد

app = Flask(__name__)

# ایجاد ربات تلگرام
application = Application.builder().token(TOKEN).build()

# متون فارسی کامل
TEXTS = {
    'start': '🌺 سلام! به ربات کتاب هوژین و حرمان خوش آمدید\n\nلطفاً گزینه مورد نظر را انتخاب کنید:',
    'buy': '''📚 خرید کتاب هوژین و حرمان

💰 هزینه کتاب: 110,000 تومان
💳 شماره کارت: 5859 8311 3314 0268
📸 لطفاً پس از پرداخت، فیش واریزی را ارسال کنید''',
    
    'suggestion': '''💌 بخش نظرات و پیشنهادات

لطفاً نظرات، انتقادات و پیشنهادات خود را درباره کتاب با ما در میان بگذارید''',
    
    'about_book': '''📖 درباره کتاب هوژین و حرمان

رمان هوژین و حرمان روایتی عاشقانه است که... [توضیحات کامل کتاب]''',
    
    'about_author': '''✍️ درباره نویسنده

مانی محمودی، نویسنده جوان ایرانی... [توضیحات کامل درباره نویسنده]''',
    
    'audio': '''🎧 کتاب صوتی

نسخه صوتی کتاب به زودی منتشر خواهد شد''',
    
    'waiting_payment': '''⏳ فیش پرداخت شما دریافت شد

در حال بررسی پرداخت شما هستیم. لطفاً شکیبا باشید...''',
    
    'waiting_suggestion': '''🙏 سپاس از شما!

نظر شما با موفقیت ثبت شد و در اسرع وقت بررسی خواهد شد''',
    
    'payment_approved': '''✅ پرداخت شما تأیید شد

لینک دانلود کتاب:
[لینک دانلود کتاب]

با تشکر از خرید شما!''',
    
    'payment_rejected': '''❌ مشکل در پرداخت

متأسفانه پرداخت شما تأیید نشد. لطفاً:
1. مجدداً پرداخت را انجام دهید
2. فیش واضح و خوانا ارسال کنید
3. در صورت مشکل با پشتیبانی تماس بگیرید'''
}

# ایجاد منوی اصلی
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📚 خرید کتاب", callback_data="buy_book")],
        [InlineKeyboardButton("💬 نظرات و پیشنهادات", callback_data="send_suggestion")],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🎧 کتاب صوتی", callback_data="audio_book")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ایجاد کیبورد تأیید/رد برای ادمین
def admin_approval_keyboard(user_id, receipt_msg_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"approve_{user_id}_{receipt_msg_id}"),
            InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{user_id}_{receipt_msg_id}")
        ]
    ])

# دستور /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            text=TEXTS['start'],
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"خطا در start_command: {e}")

# مدیریت کلیک روی دکمه‌ها
async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "buy_book":
            await query.edit_message_text(
                text=TEXTS['buy'],
                reply_markup=main_menu_keyboard()
            )
            context.user_data['state'] = 'waiting_payment'
        
        elif query.data == "send_suggestion":
            await query.edit_message_text(
                text=TEXTS['suggestion'],
                reply_markup=main_menu_keyboard()
            )
            context.user_data['state'] = 'waiting_suggestion'
        
        elif query.data == "about_book":
            await query.edit_message_text(
                text=TEXTS['about_book'],
                reply_markup=main_menu_keyboard()
            )
        
        elif query.data == "about_author":
            await query.edit_message_text(
                text=TEXTS['about_author'],
                reply_markup=main_menu_keyboard()
            )
        
        elif query.data == "audio_book":
            await query.edit_message_text(
                text=TEXTS['audio'],
                reply_markup=main_menu_keyboard()
            )
            
    except Exception as e:
        logger.error(f"خطا در button_click_handler: {e}")

# مدیریت تأیید/رد پرداخت توسط ادمین
async def payment_approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        action, user_id, receipt_msg_id = query.data.split('_')
        
        if action == "approve":
            # ارسال کتاب به کاربر
            if os.path.exists(PDF_PATH):
                with open(PDF_PATH, 'rb') as pdf_file:
                    await context.bot.send_document(
                        chat_id=int(user_id),
                        document=pdf_file,
                        caption=TEXTS['payment_approved']
                    )
            
            # حذف پیام فیش از چت ادمین
            await context.bot.delete_message(
                chat_id=ADMIN_ID,
                message_id=int(receipt_msg_id)
            )
            
            await query.edit_message_text(
                text=f"✅ پرداخت کاربر {user_id} با موفقیت تأیید شد"
            )
        
        elif action == "reject":
            # ارسال پیام رد پرداخت به کاربر
            await context.bot.send_message(
                chat_id=int(user_id),
                text=TEXTS['payment_rejected']
            )
            
            # حذف پیام فیش از چت ادمین
            await context.bot.delete_message(
                chat_id=ADMIN_ID,
                message_id=int(receipt_msg_id)
            )
            
            await query.edit_message_text(
                text=f"❌ پرداخت کاربر {user_id} رد شد"
            )
            
    except Exception as e:
        logger.error(f"خطا در payment_approval_handler: {e}")

# مدیریت پیام‌های کاربران
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_state = context.user_data.get('state')
        
        # اگر کاربر در حال ارسال فیش پرداخت است
        if user_state == 'waiting_payment' and update.message.photo:
            # ارسال فیش به ادمین
            forwarded_msg = await update.message.forward(chat_id=ADMIN_ID)
            
            # ارسال کیبورد تأیید/رد به ادمین
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💸 فیش پرداخت جدید از کاربر {update.effective_user.id}",
                reply_markup=admin_approval_keyboard(
                    user_id=update.effective_user.id,
                    receipt_msg_id=forwarded_msg.message_id
                )
            )
            
            # پاسخ به کاربر
            await update.message.reply_text(
                text=TEXTS['waiting_payment'],
                reply_markup=main_menu_keyboard()
            )
            
            context.user_data['state'] = None
        
        # اگر کاربر در حال ارسال نظر است
        elif user_state == 'waiting_suggestion':
            # ارسال نظر به ادمین
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📝 نظر جدید از کاربر {update.effective_user.id}:\n\n{update.message.text}"
            )
            
            # پاسخ به کاربر
            await update.message.reply_text(
                text=TEXTS['waiting_suggestion'],
                reply_markup=main_menu_keyboard()
            )
            
            context.user_data['state'] = None
            
    except Exception as e:
        logger.error(f"خطا در message_handler: {e}")

# تنظیم هندلرها
application.add_handler(CommandHandler('start', start_command))
application.add_handler(CallbackQueryHandler(button_click_handler, pattern="^(buy_book|send_suggestion|about_book|about_author|audio_book)$"))
application.add_handler(CallbackQueryHandler(payment_approval_handler, pattern=r"^(approve|reject)_\d+_\d+$"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
application.add_handler(MessageHandler(filters.PHOTO, message_handler))

# وب‌هوک
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        # دریافت آپدیت
        update = Update.de_json(request.get_json(), application.bot)
        
        # ایجاد یک ترد جدید برای پردازش آپدیت
        Thread(target=lambda: asyncio.run(application.process_update(update))).start()
        
        return {'status': 'ok'}
    
    except Exception as e:
        logger.error(f'خطا در وب‌هوک: {e}')
        return {'status': 'error'}, 500

@app.route('/')
def home():
    return "ربات کتاب هوژین و حرمان در حال اجراست"

# راه‌اندازی اولیه
def setup():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # تنظیم وب‌هوک
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.bot.set_webhook(
            url=f'https://YOUR_DOMAIN.com/{TOKEN}'
        ))
        
        logger.info("تنظیمات اولیه با موفقیت انجام شد")
    except Exception as e:
        logger.error(f"خطا در راه‌اندازی: {e}")
    finally:
        loop.close()

if __name__ == '__main__':
    # اجرای تنظیمات اولیه
    setup()
    
    # اجرای سرور Flask
    app.run(host='0.0.0.0', port=10000, debug=False)
