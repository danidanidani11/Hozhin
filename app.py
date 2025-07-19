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
WEBHOOK_URL = "https://hozhin-bot.onrender.com"  # ← اینجا آدرس واقعی سرور خود را قرار دهید

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("💬 پیشنهادات", callback_data="suggestion")],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🎧 کتاب صوتی", callback_data="audio_book")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TEXTS['start'], reply_markup=main_menu())

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
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

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    if state == 'waiting_receipt' and update.message.photo:
        receipt = await update.message.forward(ADMIN_ID)
        await context.bot.send_message(
            ADMIN_ID,
            f"📩 فیش پرداخت از کاربر {update.effective_user.id}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{update.effective_user.id}_{receipt.message_id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{update.effective_user.id}_{receipt.message_id}")
            ]])
        )
        await update.message.reply_text(TEXTS['receipt_received'])
        context.user_data['state'] = None
    
    elif state == 'waiting_suggestion':
        await context.bot.send_message(
            ADMIN_ID,
            f"📝 نظر جدید از {update.effective_user.id}:\n{update.message.text}"
        )
        await update.message.reply_text(TEXTS['suggestion_received'])
        context.user_data['state'] = None

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_id, msg_id = query.data.split('_')
    try:
        if action == "approve":
            if os.path.exists(PDF_PATH):
                with open(PDF_PATH, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=int(user_id),
                        document=f,
                        caption=TEXTS['payment_approved']
                    )
            await context.bot.delete_message(chat_id=ADMIN_ID, message_id=int(msg_id))
            await query.edit_message_text(f"✅ پرداخت کاربر {user_id} تأیید شد")
        else:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=TEXTS['payment_rejected']
            )
            await context.bot.delete_message(chat_id=ADMIN_ID, message_id=int(msg_id))
            await query.edit_message_text(f"❌ پرداخت کاربر {user_id} رد شد")
    except Exception as e:
        logger.error(f"خطا: {e}")

# تنظیم هندلرها
application.add_handler(CommandHandler('start', start))
application.add_handler(CallbackQueryHandler(handle_buttons))
application.add_handler(CallbackQueryHandler(handle_approval, pattern="^(approve|reject)_"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
application.add_handler(MessageHandler(filters.PHOTO, handle_messages))

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    try:
        data = await request.get_json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return {'status': 'ok'}
    except Exception as e:
        logger.error(f'خطا در وب‌هوک: {e}')
        return {'status': 'error'}, 500

@app.route('/')
def home():
    return "ربات فعال است"

async def setup():
    await application.initialize()
    await application.bot.set_webhook(f'{WEBHOOK_URL}/{TOKEN}')

def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup())
    loop.close()

if __name__ == '__main__':
    run()
    app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)
