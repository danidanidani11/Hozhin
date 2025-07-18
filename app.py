import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ==== تنظیمات اصلی ====
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

# ==== Flask App ====
app = Flask(__name__)
users_payment = {}
user_waiting_for_receipt = set()

# ==== متون ====
ABOUT_BOOK_TEXT = "🔸 متن درباره کتاب (همان متن بلند قبلی) 🔸"
ABOUT_AUTHOR_TEXT = "✍️ معرفی نویسنده: مانی محمودی ..."
AUDIOBOOK_TEXT = "🔊 این بخش به زودی فعال خواهد شد."

# ==== منوی اصلی ====
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("💬 انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("🖊️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🎧 کتاب صوتی", callback_data="audiobook")]
    ])

# ==== Webhook route ====
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    update = Update.de_json(data, app.bot)
    app.application.create_task(app.application.process_update(update))
    return "ok"

# ==== استارت ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if member.status in ["left", "kicked"]:
            await update.message.reply_text(
                f"🔒 لطفاً ابتدا عضو کانال @{CHANNEL_USERNAME} شوید و سپس مجدد /start را ارسال کنید."
            )
            return
    except:
        await update.message.reply_text("⛔ خطا در بررسی عضویت. لطفاً بعداً دوباره تلاش کنید.")
        return

    await update.message.reply_text(
        f"سلام {user.first_name} 🌟\nبه ربات فروش کتاب خوش آمدید.",
        reply_markup=main_menu_keyboard()
    )

# ==== دکمه‌های منو ====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if query.data == "buy":
        user_waiting_for_receipt.add(user.id)
        await query.edit_message_text(
            "💳 شماره کارت برای پرداخت:\n"
            "`5859 8311 3314 0268`\n\n"
            "لطفاً فیش واریزی را همین‌جا ارسال کنید.\n"
            "✅ مبلغ: ۱۱۰ هزارتومان\n"
            "🕰 تأیید ممکن است کمی زمان‌بر باشد."
        , parse_mode="Markdown")

    elif query.data == "feedback":
        await query.edit_message_text("✍️ لطفاً پیام یا پیشنهاد خود را بنویسید و ارسال کنید:")

    elif query.data == "about_book":
        await query.edit_message_text(ABOUT_BOOK_TEXT)

    elif query.data == "about_author":
        await query.edit_message_text(ABOUT_AUTHOR_TEXT)

    elif query.data == "audiobook":
        await query.edit_message_text(AUDIOBOOK_TEXT)

# ==== مدیریت پیام‌ها ====
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    receipt_file_id = None

    if user.id in user_waiting_for_receipt:
        if update.message.photo:
            receipt_file_id = update.message.photo[-1].file_id
        elif update.message.document:
            receipt_file_id = update.message.document.file_id

        users_payment[user.id] = {
            "status": "pending",
            "receipt": receipt_file_id or text,
            "username": user.username or user.first_name,
        }
        user_waiting_for_receipt.remove(user.id)

        # ارسال به ادمین
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user.id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{user.id}")
            ]
        ])

        caption = f"🧾 فیش پرداختی از @{user.username or user.first_name} (ID: {user.id})"
        if receipt_file_id:
            if update.message.photo:
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=receipt_file_id, caption=caption, reply_markup=markup)
            else:
                await context.bot.send_document(chat_id=ADMIN_ID, document=receipt_file_id, caption=caption, reply_markup=markup)
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=caption + f"\n\n{text}", reply_markup=markup)

        await update.message.reply_text("✅ فیش شما دریافت شد و در حال بررسی است.")
        return

    # پیام‌های متنی معمولی
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 پیام از @{user.username or user.first_name}:\n{text}")
    await update.message.reply_text("✅ پیام شما دریافت شد. ممنون از نظر شما!")

# ==== بررسی تأیید یا رد توسط ادمین ====
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    admin_id = update.effective_user.id
    await query.answer()

    if admin_id != ADMIN_ID:
        await query.edit_message_text("⛔ شما اجازه این کار را ندارید.")
        return

    if data.startswith("approve_") or data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        if user_id not in users_payment:
            await query.edit_message_text("❗ کاربر یافت نشد.")
            return

        if data.startswith("approve_"):
            users_payment[user_id]["status"] = "approved"
            await query.edit_message_text(f"✅ پرداخت کاربر {user_id} تأیید شد.")

            pdf_path = "books/hozhin_harman.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    await context.bot.send_document(chat_id=user_id, document=InputFile(f, filename="hozhin_harman.pdf"))
                await context.bot.send_message(chat_id=user_id, text="📕 کتاب برای شما ارسال شد. از خریدتان متشکریم! ❤️")
            else:
                await context.bot.send_message(chat_id=ADMIN_ID, text="⚠️ فایل PDF پیدا نشد.")
        else:
            users_payment[user_id]["status"] = "rejected"
            await query.edit_message_text(f"❌ پرداخت کاربر {user_id} رد شد.")
            await context.bot.send_message(chat_id=user_id, text="❌ پرداخت تأیید نشد. لطفاً فیش را مجدد ارسال کنید.")

# ==== دستورات ناشناس ====
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستور ناشناخته است. از منوی اصلی استفاده کنید.")

# ==== اجرای اپلیکیشن ====
def run_app():
    application = ApplicationBuilder().token(TOKEN).build()
    app.application = application
    app.bot = application.bot

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(buy|feedback|about_book|about_author|audiobook)$"))
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), message_handler))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(approve_|reject_)"))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()

if __name__ == "__main__":
    run_app()
