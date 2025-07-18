import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

app = Flask(__name__)

users_payment = {}
user_waiting_for_receipt = set()

# ... (متن‌های ABOUT_BOOK_TEXT, ABOUT_AUTHOR_TEXT, AUDIOBOOK_TEXT مانند قبل)

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("کتاب صوتی", callback_data="audiobook")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if member.status in ["left", "kicked"]:
            await update.message.reply_text(
                f"لطفا ابتدا عضو کانال @{CHANNEL_USERNAME} شوید و دوباره /start را ارسال کنید."
            )
            return
    except Exception as e:
        print(f"خطا در بررسی عضویت کانال: {e}")
        await update.message.reply_text("خطا در بررسی عضویت کانال. لطفا بعدا امتحان کنید.")
        return

    await update.message.reply_text(
        f"سلام {user.first_name} 👋\nبه ربات کتاب هوژین حرمان خوش آمدید.",
        reply_markup=main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        msg = (
            "شماره کارت:\n5859 8311 3314 0268\n\n"
            "مبلغ: 110,000 تومان\n"
            "لطفا پس از پرداخت، تصویر فیش واریزی را ارسال کنید."
        )
        user_waiting_for_receipt.add(query.from_user.id)
        await query.edit_message_text(msg)
    elif query.data == "feedback":
        await query.edit_message_text("لطفا نظر خود را ارسال کنید:")
    elif query.data == "about_book":
        await query.edit_message_text(ABOUT_BOOK_TEXT)
    elif query.data == "about_author":
        await query.edit_message_text(ABOUT_AUTHOR_TEXT)
    elif query.data == "audiobook":
        await query.edit_message_text(AUDIOBOOK_TEXT)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
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
            "username": user.username or user.first_name,
        }
        user_waiting_for_receipt.remove(user_id)

        if receipt_file_id:
            if update.message.photo:
                await context.bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=receipt_file_id,
                    caption=f"فیش پرداختی از @{users_payment[user_id]['username']} (ID: {user_id})",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("تایید ✅", callback_data=f"approve_{user_id}"),
                            InlineKeyboardButton("رد ❌", callback_data=f"reject_{user_id}")
                        ]
                    ])
                )
            elif update.message.document:
                await context.bot.send_document(
                    chat_id=ADMIN_ID,
                    document=receipt_file_id,
                    caption=f"فیش پرداختی از @{users_payment[user_id]['username']} (ID: {user_id})",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("تایید ✅", callback_data=f"approve_{user_id}"),
                            InlineKeyboardButton("رد ❌", callback_data=f"reject_{user_id}")
                        ]
                    ])
                )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"پیام پرداخت از @{users_payment[user_id]['username']} (ID: {user_id}):\n\n{text}",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("تایید ✅", callback_data=f"approve_{user_id}"),
                        InlineKeyboardButton("رد ❌", callback_data=f"reject_{user_id}")
                    ]
                ])
            )

        await update.message.reply_text("✅ فیش پرداخت شما دریافت شد. پس از تأیید، کتاب برای شما ارسال خواهد شد.")
        return

    # اگر پیام معمولی بود (برای بخش انتقادات و پیشنهادات)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"پیام جدید از @{user.username or user.first_name} (ID: {user_id}):\n\n{text}"
    )
    await update.message.reply_text("پیام شما دریافت شد. با تشکر از نظر شما!")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    admin_id = query.from_user.id
    
    if admin_id != ADMIN_ID:
        await query.edit_message_text("⛔ شما مجوز انجام این عمل را ندارید!")
        return

    if not (data.startswith("approve_") or data.startswith("reject_")):
        return

    action, user_id = data.split("_")
    user_id = int(user_id)

    if user_id not in users_payment:
        await query.edit_message_text("⚠️ کاربر یافت نشد یا قبلاً پردازش شده است.")
        return

    if action == "approve":
        users_payment[user_id]["status"] = "approved"
        await query.edit_message_text(f"✅ پرداخت کاربر {user_id} تأیید شد.")
        
        try:
            pdf_path = "books/hozhin_harman.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=InputFile(f, filename="hozhin_harman.pdf"),
                        caption="📚 کتاب هوژین حرمان"
                    )
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ پرداخت شما تأیید شد! کتاب در بالا برای شما ارسال گردید.\nبا تشکر از خرید شما! ❤️"
                )
            else:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text="❌ فایل کتاب یافت نشد! لطفاً مسیر را بررسی کنید."
                )
        except Exception as e:
            print(f"خطا در ارسال کتاب: {e}")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"❌ خطا در ارسال کتاب به کاربر {user_id}: {str(e)}"
            )
    else:
        users_payment[user_id]["status"] = "rejected"
        await query.edit_message_text(f"❌ پرداخت کاربر {user_id} رد شد.")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ پرداخت شما تأیید نشد.\nلطفاً:\n1. مجدداً فیش واریزی را ارسال کنید\n2. یا با پشتیبانی تماس بگیرید."
        )

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ دستور نامعتبر. لطفاً از منوی اصلی استفاده کنید.")

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(buy|feedback|about_book|about_author|audiobook)$"))
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), message_handler))
    application.add_handler(CallbackQueryHandler(admin_callback_handler))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    setup_handlers(application)
    application.run_polling()

if __name__ == "__main__":
    print("✅ ربات در حال راه‌اندازی...")
    run_bot()
