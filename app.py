import os
from flask import Flask, request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import asyncio

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

app = Flask(__name__)
application: Application = Application.builder().token(TOKEN).build()

users_payment = {}
user_waiting_for_receipt = set()

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running via webhook!"

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("کتاب صوتی", callback_data="audiobook")],
    ])

ABOUT_BOOK_TEXT = "📘 توضیحاتی درباره کتاب ..."
ABOUT_AUTHOR_TEXT = "✍ درباره نویسنده ..."
AUDIOBOOK_TEXT = "🎧 این بخش به زودی فعال میشود."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if member.status in ["left", "kicked"]:
            await update.message.reply_text(
                f"لطفا ابتدا عضو کانال @{CHANNEL_USERNAME} شوید و دوباره /start را ارسال کنید."
            )
            return
    except:
        await update.message.reply_text("خطا در بررسی عضویت کانال.")
        return

    await update.message.reply_text(
        f"سلام {user.first_name} 👋\nبه ربات خوش آمدید!",
        reply_markup=main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    if query.data == "buy":
        user_waiting_for_receipt.add(user.id)
        await query.edit_message_text(
            "💳 شماره کارت: 5859 8311 3314 0268\n"
            "مبلغ: ۱۱۰ هزار تومان\n\n"
            "لطفاً فیش پرداخت را ارسال کنید."
        )
    elif query.data == "feedback":
        await query.edit_message_text("📝 لطفاً نظر خود را ارسال کنید:")
    elif query.data == "about_book":
        await query.edit_message_text(ABOUT_BOOK_TEXT)
    elif query.data == "about_author":
        await query.edit_message_text(ABOUT_AUTHOR_TEXT)
    elif query.data == "audiobook":
        await query.edit_message_text(AUDIOBOOK_TEXT)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""
    receipt_file_id = None

    if user_id in user_waiting_for_receipt:
        if update.message.photo:
            receipt_file_id = update.message.photo[-1].file_id
        elif update.message.document:
            receipt_file_id = update.message.document.file_id

        users_payment[user_id] = {
            "status": "pending",
            "receipt": receipt_file_id or text,
            "username": update.effective_user.username or update.effective_user.first_name
        }
        user_waiting_for_receipt.remove(user_id)

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("تایید ✅", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("رد ❌", callback_data=f"reject_{user_id}")
        ]])

        if receipt_file_id:
            if update.message.photo:
                await context.bot.send_photo(
                    ADMIN_ID, photo=receipt_file_id,
                    caption=f"فیش از @{users_payment[user_id]['username']} (ID: {user_id})",
                    reply_markup=keyboard
                )
            else:
                await context.bot.send_document(
                    ADMIN_ID, document=receipt_file_id,
                    caption=f"فیش از @{users_payment[user_id]['username']} (ID: {user_id})",
                    reply_markup=keyboard
                )
        else:
            await context.bot.send_message(
                ADMIN_ID,
                text=f"فیش متنی از @{users_payment[user_id]['username']}:\n\n{text}",
                reply_markup=keyboard
            )
        await update.message.reply_text("✅ فیش دریافت شد. منتظر تایید بمانید.")
    else:
        await context.bot.send_message(
            ADMIN_ID,
            text=f"📨 پیام از @{update.effective_user.username or update.effective_user.first_name}:\n{text}"
        )
        await update.message.reply_text("پیام شما به ادمین ارسال شد.")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("⛔ شما مجاز نیستید.")
        return

    user_id = int(data.split("_")[1])
    if data.startswith("approve_"):
        users_payment[user_id]["status"] = "approved"
        await context.bot.send_message(user_id, "✅ پرداخت شما تایید شد.")
        if os.path.exists("books/hozhin_harman.pdf"):
            with open("books/hozhin_harman.pdf", "rb") as f:
                await context.bot.send_document(user_id, InputFile(f, "hozhin_harman.pdf"))
        await query.edit_message_text("پرداخت تایید شد.")
    elif data.startswith("reject_"):
        users_payment[user_id]["status"] = "rejected"
        await context.bot.send_message(user_id, "❌ پرداخت شما تایید نشد.")
        await query.edit_message_text("پرداخت رد شد.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستور ناشناخته است.")

def setup_bot():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(buy|feedback|about_book|about_author|audiobook)$"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(approve_|reject_)"))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

if __name__ == "__main__":
    setup_bot()
    # اجرای Flask توسط Render انجام می‌شود
