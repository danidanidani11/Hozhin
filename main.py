import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)
from database import init_db, add_user, update_channel_status, get_user, add_receipt, update_receipt_status, get_receipt
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0")
ADMIN_ID = 5542927340
CHANNEL_ID = "@fromheartsoul"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)

    # بررسی عضویت در کانال
    if not await check_channel_membership(update, context):
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "لطفاً ابتدا در کانال @fromheartsoul عضو شوید و سپس /start را دوباره بزنید.",
            reply_markup=reply_markup
        )
        return

    keyboard = [
        [InlineKeyboardButton("خرید کتاب", callback_data="buy_book")],
        [InlineKeyboardButton("انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("کتاب صوتی", callback_data="audio_book")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("به بات کتاب هوژین و حرمان خوش آمدید!", reply_markup=reply_markup)

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            update_channel_status(user_id, True)
            return True
        return False
    except:
        return False

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if not get_user(user_id)[2]:  # بررسی عضویت در کانال
        await query.message.reply_text(
            "لطفاً ابتدا در کانال @fromheartsoul عضو شوید و سپس /start را دوباره بزنید."
        )
        return

    await query.answer()  # پاسخ به callback برای جلوگیری از خطا

    if query.data == "buy_book":
        await query.message.reply_text(
            "شماره کارت:\n5859 8311 3314 0268\n\n"
            "لطفا فیش را همینجا ارسال کنید تا مورد تایید قرار بگیرد. هزینه کتاب ۱۱۰ هزارتومان میباشد.\n"
            "ممکن است تایید فیش کمی زمان‌بر باشد پس لطفا صبور باشید.\n"
            "در صورت تایید فایل پی دی اف برایتان در همینجا ارسال میشود.\n"
            "اگر هرگونه مشکلی برایتان پیش آمد در بخش انتقادات و پیشنهادات برای ما ارسال کنید تا بررسی شود."
        )
        context.user_data['awaiting_receipt'] = True

    elif query.data == "feedback":
        await query.message.reply_text(
            "اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند حتما در این بخش بنویسید تا بررسی شود\n"
            "مطمئن باشید نظرات شما خوانده میشود و باارزش خواهد بود.☺️"
        )
        context.user_data['awaiting_feedback'] = True

    elif query.data == "about_book":
        await query.message.reply_text(
            "رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد. "
            # متن کامل مشابه قبل
        )

    elif query.data == "about_author":
        await query.message.reply_text(
            "سلام رفقا 🙋🏻‍♂\n"
            "مانی محمودی هستم نویسنده کتاب هوژین حرمان.\n"
            # متن کامل مشابه قبل
        )

    elif query.data == "audio_book":
        await query.message.reply_text("این بخش به زودی فعال میشود")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not get_user(user_id)[2]:
        await update.message.reply_text("لطفاً ابتدا در کانال @fromheartsoul عضو شوید.")
        return

    if context.user_data.get('awaiting_receipt'):
        if update.message.photo or update.message.document or update.message.text:
            receipt_id = str(update.message.message_id)
            add_receipt(user_id, receipt_id)
            keyboard = [
                [InlineKeyboardButton("تأیید ✅", callback_data=f"approve_{receipt_id}")],
                [InlineKeyboardButton("رد ❌", callback_data=f"reject_{receipt_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.message.photo:
                await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id,
                                           caption=f"فیش از کاربر {user_id}", reply_markup=reply_markup)
            elif update.message.document:
                await context.bot.send_document(ADMIN_ID, update.message.document.file_id,
                                              caption=f"فیش از کاربر {user_id}", reply_markup=reply_markup)
            elif update.message.text:
                await context.bot.send_message(ADMIN_ID, f"فیش متنی از کاربر {user_id}:\n{update.message.text}",
                                              reply_markup=reply_markup)
            await update.message.reply_text("فیش شما ارسال شد. لطفاً منتظر تأیید باشید.")
            context.user_data['awaiting_receipt'] = False

    elif context.user_data.get('awaiting_feedback'):
        feedback = update.message.textස

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    await query.answer()

    if data.startswith("approve_"):
        receipt_id = data.split("_")[1]
        receipt = get_receipt(receipt_id)
        if receipt:
            update_receipt_status(receipt_id, "approved")
            await context.bot.send_message(receipt[1], "فیش شما تأیید شد. لطفاً فایل PDF کتاب را از ادمین دریافت کنید.")
            await context.bot.send_message(ADMIN_ID, f"لطفاً فایل PDF کتاب را برای کاربر {receipt[1]} ارسال کنید.")
            await query.message.reply_text("فیش تأیید شد و به کاربر اطلاع داده شد.")

    elif data.startswith("reject_"):
        receipt_id = data.split("_")[1]
        receipt = get_receipt(receipt_id)
        if receipt:
            update_receipt_status(receipt_id, "rejected")
            await context.bot.send_message(receipt[1], "فیش شما رد شد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.")
            await query.message.reply_text("فیش رد شد و به کاربر اطلاع داده شد.")

    elif data.startswith("reply_"):
        user_id = data.split("_")[1]
        context.user_data['reply_to'] = user_id
        await query.message.reply_text(f"لطفاً پاسخ خود را برای کاربر {user_id} بنویسید.")

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and context.user_data.get('reply_to'):
        user_id = context.user_data['reply_to']
        await context.bot.send_message(user_id, f"پاسخ ادمین:\n{update.message.text}")
        await update.message.reply_text("پاسخ شما ارسال شد.")
        context.user_data['reply_to'] = None

async def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
