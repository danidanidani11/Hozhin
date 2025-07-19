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

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Basic settings
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@fromheartsoul"
PDF_FILE_PATH = "/books/hozhin_harman.pdf"

# Create Flask app
app = Flask(__name__)

# Create Telegram application
bot_app = Application.builder().token(TOKEN).build()

# Texts for different sections
BUY_BOOK_TEXT = """لطفا فیش پرداخت را همینجا ارسال کنید تا مورد تأیید قرار بگیرد.
هزینه کتاب ۱۱۰ هزارتومان است.
شماره کارت: **5859 8311 3314 0268**
ممکن است تأیید فیش کمی زمان‌بر باشد، پس لطفا صبور باشید.
در صورت تأیید، فایل PDF کتاب برایتان ارسال می‌شود.
اگر مشکلی پیش آمد، در بخش انتقادات و پیشنهادات برای ما ارسال کنید."""

SUGGESTION_TEXT = """اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند، حتما در این بخش بنویسید تا بررسی شود.
مطمئن باشید نظرات شما خوانده می‌شود و باارزش خواهد بود. ☺️"""

ABOUT_BOOK_TEXT = """رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد..."""  # [rest of text unchanged]

ABOUT_AUTHOR_TEXT = """سلام رفقا 🙋🏻‍♂
مانی محمودی هستم، نویسنده کتاب هوژین حرمان..."""  # [rest of text unchanged]

AUDIO_BOOK_TEXT = "این بخش به زودی فعال می‌شود."

# Main menu
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 خرید کتاب", callback_data="buy_book")],
        [InlineKeyboardButton("💬 انتقادات و پیشنهادات", callback_data="suggestion")],
        [InlineKeyboardButton("ℹ️ درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🎧 کتاب صوتی", callback_data="audio_book")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Approval menu for admin
def approval_menu(user_id, receipt_message_id):
    keyboard = [
        [
            InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"confirm_{user_id}_{receipt_message_id}"),
            InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{user_id}_{receipt_message_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"سلام {user.first_name}!\nبه بات هوژین و حرمان خوش آمدید. 😊\nلطفاً از منوی زیر یکی از گزینه‌ها را انتخاب کنید:"
    await update.message.reply_text(welcome_text, reply_markup=main_menu())

# Button handler with fix for double-click issue
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Edit message to prevent double-click
    await query.edit_message_reply_markup(reply_markup=None)

    if query.data == "buy_book":
        await query.message.reply_text(BUY_BOOK_TEXT)
        context.user_data["state"] = "waiting_for_receipt"
    elif query.data == "suggestion":
        await query.message.reply_text(SUGGESTION_TEXT)
        context.user_data["state"] = "waiting_for_suggestion"
    elif query.data == "about_book":
        await query.message.reply_text(ABOUT_BOOK_TEXT, reply_markup=main_menu())
    elif query.data == "about_author":
        await query.message.reply_text(ABOUT_AUTHOR_TEXT, reply_markup=main_menu())
    elif query.data == "audio_book":
        await query.message.reply_text(AUDIO_BOOK_TEXT, reply_markup=main_menu())
    elif query.data.startswith("confirm_"):
        # Handle payment confirmation
        _, user_id, receipt_message_id = query.data.split("_")
        user_id = int(user_id)
        
        try:
            if os.path.exists(PDF_FILE_PATH):
                with open(PDF_FILE_PATH, "rb") as file:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=file,
                        caption="فیش شما تأیید شد! فایل PDF کتاب برای شما ارسال شد. امیدوارم لذت ببرید! 😊"
                    )
                await context.bot.delete_message(
                    chat_id=ADMIN_ID,
                    message_id=int(receipt_message_id)
                )
                await query.message.reply_text(f"فایل PDF برای کاربر {user_id} ارسال شد.")
            else:
                await query.message.reply_text("فایل PDF یافت نشد. لطفاً بررسی کنید.")
        except Exception as e:
            logger.error(f"Error approving payment: {str(e)}")
            await query.message.reply_text("خطا در ارسال فایل. لطفاً دوباره تلاش کنید.")
            
    elif query.data.startswith("reject_"):
        # Handle payment rejection
        _, user_id, receipt_message_id = query.data.split("_")
        user_id = int(user_id)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="متأسفانه فیش شما تأیید نشد. لطفاً دوباره تلاش کنید یا با ادمین تماس بگیرید.",
                reply_markup=main_menu()
            )
            await context.bot.delete_message(
                chat_id=ADMIN_ID,
                message_id=int(receipt_message_id)
            )
            await query.message.reply_text(f"فیش کاربر {user_id} رد شد.")
        except Exception as e:
            logger.error(f"Error rejecting payment: {str(e)}")
            await query.message.reply_text("خطا در رد پرداخت. لطفاً دوباره تلاش کنید.")

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    state = context.user_data.get("state")

    if state == "waiting_for_receipt":
        if update.message.photo:
            # Forward receipt to admin
            receipt_msg = await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=chat_id,
                message_id=update.message.message_id
            )
            
            # Send approval buttons
            approval_msg = await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"فیش پرداخت از کاربر {user_id}",
                reply_markup=approval_menu(user_id, receipt_msg.message_id)
            )
            
            await update.message.reply_text(
                "فیش شما دریافت شد و برای تأیید به ادمین ارسال شد. لطفاً منتظر بمانید.",
                reply_markup=main_menu()
            )
            context.user_data["state"] = None
        else:
            await update.message.reply_text("لطفاً تصویر فیش پرداخت را ارسال کنید.")
    elif state == "waiting_for_suggestion":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"پیشنهاد/انتقاد از کاربر {user_id}:\n{update.message.text}"
        )
        await update.message.reply_text(
            "ممنون از نظر شما! پیام شما به ادمین ارسال شد.",
            reply_markup=main_menu()
        )
        context.user_data["state"] = None

# Add handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(button))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
bot_app.add_handler(MessageHandler(filters.PHOTO, handle_message))

# Webhook route - synchronous version
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in webhook")
            return {"status": "error", "message": "No JSON data"}, 400
        
        update = Update.de_json(data, bot_app.bot)
        if update:
            # Run the async function in a new thread
            Thread(target=asyncio.run, args=(bot_app.process_update(update),)).start()
            logger.info("Webhook processed successfully")
            return {"status": "ok"}
        else:
            logger.error("Invalid update received")
            return {"status": "error", "message": "Invalid update"}, 400
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

# Set webhook - synchronous version
def set_webhook_sync():
    webhook_url = f"https://hozhin.onrender.com/{TOKEN}"
    try:
        asyncio.run(bot_app.bot.set_webhook(url=webhook_url))
        logger.info("Webhook set successfully")
    except Exception as e:
        logger.error(f"Failed to set webhook: {str(e)}")

# Initialize function - synchronous version
def initialize_sync():
    asyncio.run(bot_app.initialize())
    set_webhook_sync()

# Main route
@app.route("/")
def index():
    return "Telegram Bot is running!"

# Run initialization when app starts
with app.app_context():
    initialize_sync()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
