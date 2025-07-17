from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from flask import Flask, request
import os
import json
import asyncio

# تنظیمات Flask
app = Flask(__name__)

# توکن بات و آیدی ادمین
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@fromheartsoul"

# متغیر برای ذخیره فیش‌های ارسالی
pending_receipts = {}

# متغیر سراسری برای Application
application = None

# بررسی عضویت در کانال
async def check_channel_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# منوی اصلی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_channel_membership(context, user_id):
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "لطفاً ابتدا در کانال @fromheartsoul عضو شوید و سپس دوباره /start را بزنید.",
            reply_markup=reply_markup
        )
        return

    keyboard = [
        [InlineKeyboardButton("📚 خرید کتاب", callback_data="buy_book")],
        [InlineKeyboardButton("💬 انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("ℹ️ درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🎙️ کتاب صوتی", callback_data="audio_book")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("به بات کتاب هوژین و حرمان خوش آمدید! لطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)

# مدیریت دکمه‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not await check_channel_membership(context, user_id):
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "لطفاً ابتدا در کانال @fromheartsoul عضو شوید و سپس دوباره تلاش کنید.",
            reply_markup=reply_markup
        )
        return

    if query.data == "buy_book":
        await query.message.reply_text(
            "شماره کارت:\n5859 8311 3314 0268\n\n"
            "لطفاً فیش را همینجا ارسال کنید تا مورد تأیید قرار بگیرد. هزینه کتاب ۱۱۰ هزار تومان می‌باشد.\n"
            "ممکن است تأیید فیش کمی زمان‌بر باشد، پس لطفاً صبور باشید.\n"
            "در صورت تأیید، فایل PDF برایتان در همینجا ارسال می‌شود.\n"
            "اگر هرگونه مشکلی پیش آمد، در بخش انتقادات و پیشنهادات برای ما ارسال کنید تا بررسی شود."
        )
        context.user_data["waiting_for_receipt"] = True

    elif query.data == "feedback":
        await query.message.reply_text(
            "اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند، حتماً در این بخش بنویسید تا بررسی شود.\n"
            "مطمئن باشید نظرات شما خوانده می‌شود و باارزش خواهد بود. ☺️"
        )
        context.user_data["waiting_for_feedback"] = True

    elif query.data == "about_book":
        await query.message.reply_text(
            "رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد. نام هوژین واژه‌ای کردی است که تعبیر آن کسی است که با آمدنش نور زندگی شما می‌شود و زندگی را تازه می‌کند؛ در معنای کلی امید را به شما برمی‌گرداند. حرمان نیز واژه‌ای کردی_عربی است که معنای آن در وصف کسی است که بالاترین حد اندوه و افسردگی را تجربه کرده و با این حال آن را رها کرده است. در تعبیری مناسب‌تر؛ هوژین در کتاب برای حرمان روزنه نور و امیدی بوده است که باعث رهایی حرمان از غم و اندوه می‌شود و دلیل اصلی رهایی برای حرمان تلقی می‌شود. کاژه هم به معنای کسی است که در کنار او احساس امنیت دارید.\n"
            "کتاب از نگاه اول شخص روایت می‌شود و پیشنهاد من این است که ابتدا کتاب را به ترتیب از بخش اول تا سوم بخوانید؛ اما اگر علاقه داشتید مجدداً آن را مطالعه کنید، برای بار دوم، ابتدا بخش دوم و سپس بخش اول و در آخر بخش سوم را بخوانید. در این صورت دو برداشت متفاوت از کتاب خواهید داشت که هر کدام زاویه نگاه متفاوتی در شما به وجود می‌آورد.\n"
            "برخی بخش‌ها و تجربه‌های کتاب بر اساس داستان واقعی روایت شده و برخی هم سناریوهای خیالی و خاص همراه بوده است که دانستن آن برای شما خالی از لطف نیست. یک سری نکات شایان ذکر است که به عنوان خواننده کتاب حق دارید بدانید. اگر در میان بندهای کتاب شعری را مشاهده کردید؛ آن ابیات توسط شاعران فرهیخته کشور عزیزمان ایران نوشته شده است و با تحقیق و جست‌وجو می‌توانید متن کامل و نام نویسنده را دریابید. اگر مطلبی را داخل \"این کادر\" دیدید به معنای این است که آن مطلب احتمالاً برگرفته از نامه‌ها یا بیت‌های کوتاه است. در آخر هم اگر جملاتی را مشاهده کردید که از قول فلانی روایت شده است و مانند آن را قبلاً شنیده‌اید؛ احتمالاً برگرفته از مطالبی است که ملکه ذهن من بوده و آنها را در طول کتاب استفاده کرده‌ام.\n"
            "در صورت خرید امیدوارم لذت ببرید."
        )

    elif query.data == "about_author":
        await query.message.reply_text(
            "سلام رفقا 🙋🏻‍♂\n"
            "مانی محمودی هستم، نویسنده کتاب هوژین و حرمان.\n"
            "نویسنده‌ای جوان هستم که با کنار هم گذاشتن نامه‌های متعدد موفق به نوشتن این کتاب شدم. کار نویسندگی را از سن ۱۳ سالگی با کمک معلم ادبیاتم شروع کردم و تا امروز به این کار ادامه می‌دهم. این کتاب اولین اثر بنده هستش و در تلاش هستم تا در طی سالیان آینده کتاب‌های بیشتری خلق کنم.\n"
            "بیشتر از این وقتتون رو نمی‌گیرم. امیدوارم لذت ببرید 😄❤️"
        )

    elif query.data == "audio_book":
        await query.message.reply_text("این بخش به زودی فعال می‌شود.")

# مدیریت فیش ارسالی
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_receipt"):
        user_id = update.effective_user.id
        message_id = update.message.message_id

        # ارسال فیش به ادمین
        keyboard = [
            [InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{user_id}_{message_id}"),
             InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}_{message_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.forward_message(ADMIN_ID, user_id, message_id)
        await context.bot.send_message(
            ADMIN_ID,
            f"فیش جدید از کاربر {user_id} دریافت شد. لطفاً بررسی کنید:",
            reply_markup=reply_markup
        )
        pending_receipts[(user_id, message_id)] = update.message
        context.user_data["waiting_for_receipt"] = False
        await update.message.reply_text("فیش شما برای ادمین ارسال شد. لطفاً منتظر تأیید باشید.")

# مدیریت انتقادات و پیشنهادات
async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_feedback"):
        user_id = update.effective_user.id
        message_id = update.message.message_id
        feedback_text = update.message.text

        # ارسال پیام به ادمین با امکان پاسخ
        keyboard = [[InlineKeyboardButton("پاسخ", callback_data=f"reply_{user_id}_{message_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.forward_message(ADMIN_ID, user_id, message_id)
        await context.bot.send_message(
            ADMIN_ID,
            f"پیام جدید از کاربر {user_id} در بخش انتقادات و پیشنهادات:",
            reply_markup=reply_markup
        )
        context.user_data["waiting_for_feedback"] = False
        await update.message.reply_text("پیام شما برای ادمین ارسال شد. در صورت نیاز پاسخ داده خواهد شد.")

# مدیریت تأیید/رد فیش
async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action, user_id, message_id = data[0], int(data[1]), int(data[2])

    if action == "approve":
        await context.bot.send_message(
            user_id,
            "فیش شما تأیید شد! لطفاً منتظر دریافت فایل PDF باشید."
        )
        await context.bot.send_message(
            ADMIN_ID,
            f"لطفاً فایل PDF کتاب را برای کاربر {user_id} ارسال کنید."
        )
        del pending_receipts[(user_id, message_id)]

    elif action == "reject":
        await context.bot.send_message(
            user_id,
            "فیش شما رد شد. لطفاً دوباره فیش معتبر ارسال کنید یا در بخش انتقادات و پیشنهادات با ما در ارتباط باشید."
        )
        del pending_receipts[(user_id, message_id)]

    elif action == "reply":
        context.user_data["reply_to_user"] = user_id
        await query.message.reply_text("لطفاً پاسخ خود را بنویسید:")

# مدیریت پاسخ ادمین
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and context.user_data.get("reply_to_user"):
        user_id = context.user_data["reply_to_user"]
        await context.bot.send_message(user_id, update.message.text)
        await update.message.reply_text("پاسخ شما برای کاربر ارسال شد.")
        context.user_data["reply_to_user"] = None

# ارسال فایل PDF توسط ادمین
async def handle_pdf_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and update.message.document:
        file = await update.message.document.get_file()
        file_name = update.message.document.file_name
        if file_name.endswith(".pdf"):
            for (user_id, _), _ in list(pending_receipts.items()):
                await context.bot.send_document(user_id, file.file_id, caption="فایل PDF کتاب برای شما ارسال شد. از خرید شما متشکریم!")
            await update.message.reply_text("فایل PDF برای کاربران تأییدشده ارسال شد.")

# مسیر Flask برای رندر
@app.route('/')
def home():
    return "بات در حال اجرا است!"

# مسیر وب‌هوک
@app.route('/webhook', methods=['POST'])
def webhook():
    global application
    update = Update.de_json(json.loads(request.get_data(as_text=True)), application.bot)
    # اجرای ناهمزمان برای پردازش آپدیت‌ها
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.process_update(update))
    loop.close()
    return '', 200

async def main():
    global application
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_reply))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf_upload))

    await application.initialize()
    await application.start()

    # تنظیم وب‌هوک
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'hozhin.onrender.com')}/webhook"
    await application.bot.set_webhook(url=webhook_url)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
