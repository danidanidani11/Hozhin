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

# تنظیمات پایه
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
PDF_PATH = "hozhin_harman.pdf"  # فایل باید در همان پوشه اصلی باشد

app = Flask(__name__)
bot = Application.builder().token(TOKEN).build()

# متون فارسی
TEXTS = {
    'start': 'سلام! به ربات کتاب هوژین خوش آمدید 📚\nلطفا گزینه مورد نظر را انتخاب کنید:',
    'buy': '💰 لطفا فیش پرداخت 110 هزار تومانی را ارسال کنید\nشماره کارت: 5859831133140268',
    'suggestion': '💡 لطفا نظرات و پیشنهادات خود را ارسال کنید',
    'about_book': '📖 درباره کتاب:\nرمان هوژین و حرمان...',
    'about_author': '✍️ درباره نویسنده:\nمانی محمودی...',
    'audio': '🔊 کتاب صوتی به زودی منتشر می‌شود',
    'waiting': '⏳ در حال پردازش...',
    'approved': '✅ پرداخت شما تایید شد. کتاب ارسال شد.',
    'rejected': '❌ پرداخت تایید نشد. لطفا مجددا تلاش کنید.'
}

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("💬 ارسال نظر", callback_data="suggestion")],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🔊 کتاب صوتی", callback_data="audio_book")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TEXTS['start'], reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "buy":
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

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    if state == 'waiting_payment' and update.message.photo:
        await update.message.reply_text(TEXTS['waiting'])
        await update.message.forward(ADMIN_ID)
        await context.bot.send_message(
            ADMIN_ID,
            f"پرداخت جدید از کاربر {update.effective_user.id}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ تایید", callback_data=f"approve_{update.effective_user.id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{update.effective_user.id}")
            ]])
        )
        context.user_data['state'] = None
    
    elif state == 'waiting_suggestion':
        await update.message.reply_text(TEXTS['waiting'])
        await context.bot.send_message(
            ADMIN_ID,
            f"نظر جدید از {update.effective_user.id}:\n{update.message.text}"
        )
        context.user_data['state'] = None

async def approve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("approve_"):
        user_id = query.data.split('_')[1]
        try:
            with open(PDF_PATH, 'rb') as f:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f,
                    caption=TEXTS['approved']
                )
            await query.edit_message_text(f"✅ پرداخت کاربر {user_id} تایید شد")
        except Exception as e:
            logger.error(f"خطا: {e}")
    
    elif query.data.startswith("reject_"):
        user_id = query.data.split('_')[1]
        await context.bot.send_message(
            chat_id=user_id,
            text=TEXTS['rejected']
        )
        await query.edit_message_text(f"❌ پرداخت کاربر {user_id} رد شد")

# تنظیم هندلرها
bot.add_handler(CommandHandler('start', start))
bot.add_handler(CallbackQueryHandler(button_handler))
bot.add_handler(CallbackQueryHandler(approve_handler, pattern="^(approve|reject)_"))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
bot.add_handler(MessageHandler(filters.PHOTO, message_handler))

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    try:
        data = await request.get_json()
        update = Update.de_json(data, bot.bot)
        await bot.process_update(update)
        return {'status': 'ok'}
    except Exception as e:
        logger.error(f'خطا: {e}')
        return {'status': 'error'}, 500

@app.route('/')
def home():
    return "ربات در حال اجراست"

async def main():
    await bot.initialize()
    await bot.bot.set_webhook(f'https://your-domain.com/{TOKEN}')
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    asyncio.run(main())
