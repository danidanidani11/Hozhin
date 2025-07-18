import os
import asyncio
from flask import Flask, request, abort
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340  # ایدی ادمین خودت
CHANNEL_USERNAME = "‏fromheartsoul"

app = Flask(__name__)

users_payment = {}
user_waiting_for_receipt = set()

ABOUT_BOOK_TEXT = """متن درباره کتاب..."""
ABOUT_AUTHOR_TEXT = """متن درباره نویسنده..."""
AUDIOBOOK_TEXT = "این بخش به زودی فعال میشود."

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("کتاب صوتی", callback_data="audiobook")],
    ]
    return InlineKeyboardMarkup(keyboard)

# این متغیر برای نگهداری application و loop هست
application = None
loop = asyncio.new_event_loop()

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        # استفاده از loop به صورت sync
        loop.run_until_complete(application.process_update(update))
        return "ok"
    else:
        abort(405)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if member.status in ["left", "kicked"]:
            await update.message.reply_text(
                f"لطفا ابتدا عضو کانال @{CHANNEL_USERNAME} شوید و دوباره /start را ارسال کنید."
            )
            return
    except Exception:
        await update.message.reply_text("خطا در بررسی عضویت کانال. لطفا بعدا امتحان کنید.")
        return

    await update.message.reply_text(
        f"سلام {user.first_name} 👋\n"
        "به ربات کتاب خوش آمدید.",
        reply_markup=main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        msg = (
            "شماره کارت:\n"
            "5859 8311 3314 0268\n\n"
            "لطفا فیش واریزی را ارسال کنید."
        )
        user_waiting_for_receipt.add(query.from_user.id)
        await query.edit_message_text(msg)

    elif query.data == "feedback":
        msg = "لطفا پیام خود را ارسال کنید."
        await query.edit_message_text(msg)

    elif query.data == "about_book":
        await query.edit_message_text(ABOUT_BOOK_TEXT)

    elif query.data == "about_author":
        await query.edit_message_text(ABOUT_AUTHOR_TEXT)

    elif query.data == "audiobook":
        await query.edit_message_text(AUDIOBOOK_TEXT)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""

    if user_id in user_waiting_for_receipt:
        receipt_file_id = None
        if update.message.photo:
            receipt_file_id = update.message.photo[-1].file_id
        elif update.message.document:
            receipt_file_id = update.message.document.file_id

        users_payment[user_id] = {
            "status": "pending",
            "receipt": receipt_file_id if receipt_file_id else text,
            "username": update.effective_user.username or update.effective_user.first_name,
        }
        user_waiting_for_receipt.remove(user_id)

        if receipt_file_id:
            if update.message.photo:
                await context.bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=receipt_file_id,
                    caption=f"فیش پرداختی از @{users_payment[user_id]['username']} (ID: {user_id})",
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton("تایید ✅", callback_data=f"approve_{user_id}"),
                            InlineKeyboardButton("رد ❌", callback_data=f"reject_{user_id}")
                        ]]
                    )
                )
            elif update.message.document:
                await context.bot.send_document(
                    chat_id=ADMIN_ID,
                    document=receipt_file_id,
                    caption=f"فیش پرداختی از @{users_payment[user_id]['username']} (ID: {user_id})",
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton("تایید ✅", callback_data=f"approve_{user_id}"),
                            InlineKeyboardButton("رد ❌", callback_data=f"reject_{user_id}")
                        ]]
                    )
                )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"فیش پرداختی متنی از @{users_payment[user_id]['username']} (ID: {user_id}):\n\n{text}",
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton("تایید ✅", callback_data=f"approve_{user_id}"),
                        InlineKeyboardButton("رد ❌", callback_data=f"reject_{user_id}")
                    ]]
                )
            )

        await update.message.reply_text("فیش شما دریافت شد و در حال بررسی است. لطفا شکیبا باشید.")
        return

    # انتقادات و پیشنهادات به ادمین ارسال میشه
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"پیام از @{update.effective_user.username or update.effective_user.first_name} (ID: {user_id}):\n\n{text}",
    )
    await update.message.reply_text("پیام شما به ادمین ارسال شد. ممنون!")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    admin_id = update.effective_user.id
    await query.answer()

    if admin_id != ADMIN_ID:
        await query.edit_message_text("شما اجازه انجام این کار را ندارید.")
        return

    if data.startswith("approve_") or data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        if user_id not in users_payment:
            await query.edit_message_text("کاربر یافت نشد یا فیش قبلا بررسی شده.")
            return

        if data.startswith("approve_"):
            users_payment[user_id]["status"] = "approved"
            await query.edit_message_text(f"✅ پرداخت کاربر {user_id} تایید شد.")

            pdf_path = "books/hozhin_harman.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    await context.bot.send_document(chat_id=user_id, document=InputFile(f, filename="hozhin_harman.pdf"))
                await context.bot.send_message(chat_id=user_id, text="پرداخت شما تایید شد. کتاب برای شما ارسال گردید. ممنون از خرید شما! ❤️")
            else:
                await context.bot.send_message(chat_id=ADMIN_ID, text="فایل کتاب موجود نیست!")

        else:
            users_payment[user_id]["status"] = "rejected"
            await query.edit_message_text(f"❌ پرداخت کاربر {user_id} رد شد.")
            await context.bot.send_message(chat_id=user_id, text="پرداخت شما تایید نشد. لطفا دوباره فیش را ارسال کنید یا با پشتیبانی تماس بگیرید.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستور ناشناخته. لطفا از منوی اصلی استفاده کنید.")

def main():
    global application
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(buy|feedback|about_book|about_author|audiobook)$"))
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), message_handler))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(approve_|reject_)"))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

if __name__ == "__main__":
    main()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
