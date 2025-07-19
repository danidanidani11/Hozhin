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
PDF_PATH = "hozhin_harman.pdf"
WEBHOOK_URL = "https://hozhin-bot.onrender.com"  # آدرس واقعی خود را قرار دهید

app = Flask(__name__)

# ایجاد ربات تلگرام
bot = Application.builder().token(TOKEN).build()

# متون فارسی
TEXTS = {
    'start': 'سلام! به ربات کتاب هوژین خوش آمدید. لطفاً گزینه مورد نظر را انتخاب کنید:',
    'buy': '📚 برای خرید کتاب لطفاً فیش پرداخت 110 هزار تومانی را ارسال کنید\nشماره کارت: 5859831133140268',
    'suggestion': '💬 لطفاً نظرات و پیشنهادات خود را ارسال کنید',
    'about_book': '📖 درباره کتاب: رمان هوژین و حرمان...',
    'about_author': '✍️ درباره نویسنده: مانی محمودی...',
    'audio': '🎧 کتاب صوتی به زودی منتشر می‌شود',
    'receipt_received': '✅ فیش شما دریافت شد و در حال بررسی است',
    'suggestion_received': '🙏 سپاس! نظر شما ثبت شد',
    'payment_approved': '✅ پرداخت شما تأیید شد. کتاب ارسال شد.',
    'payment_rejected': '❌ پرداخت شما تأیید نشد. لطفاً مجدداً تلاش کنید.'
}

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("💬 پیشنهادات", callback_data="suggestion")],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🎧 کتاب صوتی", callback_data="audio_book")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TEXTS['start'], reply_markup=main_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except:
        pass

    if query.data == "buy":
        await query.edit_message_text(TEXTS['buy'])
        context.user_data['state'] = 'waiting_receipt'
    
    elif query.data == "suggestion":
        await query.edit_message_text(TEXTS['suggestion'])
        context.user_data['state'] = 'waiting_suggestion'
    
    elif query.data == "about_book":
        await query.edit_message_text(TEXTS['about_book'], reply_markup=main_menu())
    
    elif query.data == "about_author":
        await query.edit_message_text(TEXTS['about_author'], reply_markup=main_menu())
    
    elif query.data == "audio_book":
        await query.edit_message_text(TEXTS['audio'], reply_markup=main_menu())

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    if state == 'waiting_receipt' and update.message.photo:
        receipt = await update.message.forward(ADMIN_ID)
        await bot.bot.send_message(
            ADMIN_ID,
            f"📩 فیش پرداخت جدید از کاربر {update.effective_user.id}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{update.effective_user.id}_{receipt.message_id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{update.effective_user.id}_{receipt.message_id}")
            ]])
        )
        await update.message.reply_text(TEXTS['receipt_received'])
        context.user_data['state'] = None
    
    elif state == 'waiting_suggestion':
        await bot.bot.send_message(
            ADMIN_ID,
            f"📝 پیشنهاد جدید از کاربر {update.effective_user.id}:\n{update.message.text}"
        )
        await update.message.reply_text(TEXTS['suggestion_received'])
        context.user_data['state'] = None

async def approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_id, msg_id = query.data.split('_')
    try:
        if action == "approve":
            if os.path.exists(PDF_PATH):
                with open(PDF_PATH, 'rb') as f:
                    await bot.bot.send_document(
                        chat_id=int(user_id),
                        document=f,
                        caption=TEXTS['payment_approved']
                    )
            await bot.bot.delete_message(chat_id=ADMIN_ID, message_id=int(msg_id))
            await query.edit_message_text(f"✅ پرداخت کاربر {user_id} تأیید شد")
        else:
            await bot.bot.send_message(
                chat_id=int(user_id),
                text=TEXTS['payment_rejected']
            )
            await bot.bot.delete_message(chat_id=ADMIN_ID, message_id=int(msg_id))
            await query.edit_message_text(f"❌ پرداخت کاربر {user_id} رد شد")
    except Exception as e:
        logger.error(f"خطا: {e}")

# تنظیم هندلرها
bot.add_handler(CommandHandler('start', start))
bot.add_handler(CallbackQueryHandler(button_click))
bot.add_handler(CallbackQueryHandler(approval_handler, pattern=r"^(approve|reject)_"))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
bot.add_handler(MessageHandler(filters.PHOTO, message_handler))

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(), bot.bot)
        Thread(target=lambda: asyncio.run(bot.process_update(update))).start()
        return {'status': 'ok'}
    except Exception as e:
        logger.error(f'خطا در وب‌هوک: {e}')
        return {'status': 'error'}, 500

@app.route('/')
def home():
    return "ربات فعال است"

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bot.initialize())
        loop.run_until_complete(bot.bot.set_webhook(f'{WEBHOOK_URL}/{TOKEN}'))
    finally:
        loop.close()

if __name__ == '__main__':
    run_bot()
    app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)
