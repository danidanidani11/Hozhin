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

# تنظیم لاگ‌گیری
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# تنظیمات اولیه
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@fromheartsoul"
PDF_FILE_PATH = "hozhin_harman.pdf"

# ایجاد اپلیکیشن Flask
app = Flask(__name__)

# ایجاد اپلیکیشن تلگرام
bot_app = Application.builder().token(TOKEN).build()

# متن‌های بخش‌های مختلف
BUY_BOOK_TEXT = """لطفا فیش پرداخت را همینجا ارسال کنید تا مورد تأیید قرار بگیرد.
هزینه کتاب ۱۱۰ هزارتومان است.
شماره کارت: **5859 8311 3314 0268**
ممکن است تأیید فیش کمی زمان‌بر باشد، پس لطفا صبور باشید.
در صورت تأیید، فایل PDF کتاب برایتان ارسال می‌شود.
اگر مشکلی پیش آمد، در بخش انتقادات و پیشنهادات برای ما ارسال کنید."""

SUGGESTION_TEXT = """اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند، حتما در این بخش بنویسید تا بررسی شود.
مطمئن باشید نظرات شما خوانده می‌شود و باارزش خواهد بود. ☺️"""

ABOUT_BOOK_TEXT = """رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد. نام هوژین واژه‌ای کردی است که تعبیر آن کسی است که با آمدنش نور زندگی شما می‌شود و زندگی را تازه می‌کند؛ در معنای کلی امید را به شما برمی‌گرداند. حرمان نیز واژه‌ای کردی-عربی است که معنای آن در وصف کسی است که بالاترین حد اندوه و افسردگی را تجربه کرده و با این حال آن را رها کرده است. در تعبیری مناسب‌تر؛ هوژین در کتاب برای حرمان روزنه نور و امیدی بوده است که باعث رهایی حرمان از غم و اندوه می‌شود و دلیل اصلی رهایی برای حرمان تلقی می‌شود. کاژه هم به معنای کسی است که در کنار او احساس امنیت دارید.
کتاب از نگاه اول شخص روایت می‌شود و پیشنهاد من این است که ابتدا کتاب را به ترتیب از بخش اول تا سوم بخوانید؛ اما اگر علاقه داشتید مجدداً آن را مطالعه کنید، برای بار دوم، ابتدا بخش دوم و سپس بخش اول و در آخر بخش سوم را بخوانید. در این صورت دو برداشت متفاوت از کتاب خواهید داشت که هر کدام زاویه نگاه متفاوتی در شما به وجود می‌آورد.
برخی بخش‌ها و تجربه‌های کتاب بر اساس داستان واقعی روایت شده و برخی هم سناریوهای خیالی و خاص همراه بوده است که دانستن آن برای شما خالی از لطف نیست. یک سری نکات شایان ذکر است که به عنوان خواننده کتاب حق دارید بدانید. اگر در میان بندهای کتاب شعری را مشاهده کردید؛ آن ابیات توسط شاعران فرهیخته کشور عزیزمان ایران نوشته شده است و با تحقیق و جست‌وجو می‌توانید متن کامل و نام نویسنده را دریابید. اگر مطلبی را داخل "این کادر" دیدید به معنای این است که آن مطلب احتمالا برگرفته از نامه‌ها یا بیت‌های کوتاه است. در آخر هم اگر جملاتی را مشاهده کردید که از قول فلانی روایت شده است و مانند آن را قبلا شنیده‌اید؛ احتمالا برگرفته از مطالبی است که ملکه ذهن من بوده و آنها را در طول کتاب استفاده کرده‌ام.
در صورت خرید، امیدوارم لذت ببرید."""

ABOUT_AUTHOR_TEXT = """سلام رفقا 🙋🏻‍♂
مانی محمودی هستم، نویسنده کتاب هوژین حرمان.
نویسنده‌ای جوان هستم که با کنار هم گذاشتن نامه‌های متعدد موفق به نوشتن این کتاب شدم. کار نویسندگی را از سن ۱۳ سالگی با کمک معلم ادبیاتم شروع کردم و تا امروز به این کار ادامه می‌دهم. این کتاب اولین اثر بنده است و در تلاش هستم تا در طی سالیان آینده کتاب‌های بیشتری خلق کنم.
بیشتر از این وقتتون رو نمی‌گیرم. امیدوارم لذت ببرید 😄❤️"""

AUDIO_BOOK_TEXT = "این بخش به زودی فعال می‌شود."

# منوی اصلی
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 خرید کتاب", callback_data="buy_book")],
        [InlineKeyboardButton("💬 انتقادات و پیشنهادات", callback_data="suggestion")],
        [InlineKeyboardButton("ℹ️ درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🎧 کتاب صوتی", callback_data="audio_book")],
    ]
    return InlineKeyboardMarkup(keyboard)

# هندلر شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"سلام {user.first_name}!\nبه بات هوژین و حرمان خوش آمدید. 😊\nلطفاً از منوی زیر یکی از گزینه‌ها را انتخاب کنید:"
    await update.message.reply_text(welcome_text, reply_markup=main_menu())

# هندلر دکمه‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

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

# هندلر پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    state = context.user_data.get("state")

    if state == "waiting_for_receipt":
        if update.message.photo:
            await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=chat_id,
                message_id=update.message.message_id
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"فیش پرداخت از کاربر {user_id}. برای تأیید، دستور /approve_{user_id} و برای رد، دستور /reject_{user_id} را ارسال کنید."
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

# هندلر تأیید فیش
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی به این دستور ندارید.")
        return

    try:
        user_id = int(context.args[0].split("_")[1])
        if os.path.exists(PDF_FILE_PATH):
            with open(PDF_FILE_PATH, "rb") as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    caption="فیش شما تأیید شد! فایل PDF کتاب برای شما ارسال شد. امیدوارم لذت ببرید! 😊"
                )
            await update.message.reply_text(f"فایل PDF برای کاربر {user_id} ارسال شد.")
        else:
            await update.message.reply_text("فایل PDF یافت نشد. لطفاً بررسی کنید.")
    except (IndexError, ValueError):
        await update.message.reply_text("لطفاً دستور را به درستی وارد کنید. مثال: /approve_123456")

# هندلر رد فیش
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی به این دستور ندارید.")
        return

    try:
        user_id = int(context.args[0].split("_")[1])
        await context.bot.send_message(
            chat_id=user_id,
            text="متأسفانه فیش شما تأیید نشد. لطفاً دوباره تلاش کنید یا با ادمین تماس بگیرید.",
            reply_markup=main_menu()
        )
        await update.message.reply_text(f"فیش کاربر {user_id} رد شد.")
    except (IndexError, ValueError):
        await update.message.reply_text("لطفاً دستور را به درستی وارد کنید. مثال: /reject_123456")

# افزودن هندلرها
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(button))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
bot_app.add_handler(MessageHandler(filters.PHOTO, handle_message))
bot_app.add_handler(CommandHandler("approve", approve))
bot_app.add_handler(CommandHandler("reject", reject))

# مسیر وب‌هوک
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in webhook")
            return {"status": "error", "message": "No JSON data"}, 400
        update = Update.de_json(data, bot_app.bot)
        if update:
            asyncio.run(bot_app.process_update(update))
            logger.info("Webhook processed successfully")
            return {"status": "ok"}
        else:
            logger.error("Invalid update received")
            return {"status": "error", "message": "Invalid update"}, 400
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

# مسیر اصلی برای بررسی سرور
@app.route("/")
def index():
    return "Telegram Bot is running!"

# تنظیم وب‌هوک
async def set_webhook():
    webhook_url = f"https://hozhin.onrender.com/{TOKEN}"
    try:
        await bot_app.bot.set_webhook(url=webhook_url)
        logger.info("Webhook set successfully")
    except Exception as e:
        logger.error(f"Failed to set webhook: {str(e)}")

# اجرای وب‌هوک هنگام شروع
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(set_webhook())
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
