import os
from flask import Flask, request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

app = Flask(__name__)

users_payment = {}  # ذخیره وضعیت پرداخت کاربران
user_waiting_for_receipt = set()

ABOUT_BOOK_TEXT = """
رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد.نام هوژین واژه ای کردی است که تعبیر آن کسی است که با آمدنش نور زندگی شما میشود و زندگی را تازه میکند؛در معنای کلی امید را به شما برمیگرداند.حرمان نیز واژه ای کردی_عربی است که معنای آن در وصف کسی است که بالاترین حد اندوه و افسردگی را تجربه کرده و با این حال آن را رها کرده است.در تعبیری مناسب تر؛هوژین در کتاب برای حرمان روزنه نور و امیدی بوده است که باعث رهایی حرمان از غم و اندوه میشود و دلیل اصلی رهایی برای حرمان تلقی میشود.کاژه هم به معنای کسی است که در کنار او احساس امنیت دارید. 
کتاب از نگاه اول شخص روایت میشود و پیشنهاد من این است که ابتدا کتاب را به ترتیب از بخش اول تا سوم بخوانید؛اما اگر علاقه داشتید مجدداً آن را مطالعه کنید،برای بار دوم، ابتدا بخش دوم و سپس بخش اول و در آخر بخش سوم را بخوانید.در این صورت دو برداشت متفاوت از کتاب خواهید داشت که هر کدام زاویه نگاه متفاوتی در شما به وجود می آورد. 
برخی بخش ها و تجربه های کتاب بر اساس داستان واقعی روایت شده و برخی هم سناریوهای خیالی و خاص همراه بوده است که دانستن آن برای شما خالی از لطف نیست.یک سری نکات شایان ذکر است که به عنوان  خواننده کتاب حق دارید بدانید.اگر در میان بند های کتاب شعری را مشاهده کردید؛آن ابیات توسط شاعران فرهیخته کشور عزیزمان ایران نوشته شده است و با تحقیق و جست و جو میتوانید متن کامل و نام نویسنده را دریابید.اگر مطلبی را داخل "این کادر" دیدید به معنای این است که آن مطلب احتمالا برگرفته از نامه ها یا بیت های کوتاه است.در آخر هم اگر جملاتی را مشاهده کردید که از قول فلانی روایت شده است و مانند آن را قبلا شنیده اید؛احتمالا برگرفته از مطالبی است که ملکه ذهن من بوده و آنها را در طول کتاب استفاده کرده ام.

درصورت خرید امیدوارم لذت ببرید.
"""

ABOUT_AUTHOR_TEXT = """
سلام رفقا 🙋🏻‍♂
مانی محمودی هستم نویسنده کتاب هوژین حرمان.
نویسنده ای جوان هستم که با کنار هم گذاشتن نامه های متعدد موفق به نوشتن این کتاب شدم.کار نویسندگی را از سن ۱۳ سالگی با کمک معلم ادبیاتم شروع کردم و تا امروز به این کار را ادامه می‌دهم.این کتاب اولین اثر بنده هستش و در تلاش هستم تا در طی سالیان آینده کتاب های بیشتری خلق کنم.

بیشتر از این وقتتون رو نمیگیرم.امیدوار لذت ببرید😄❤️
"""

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

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = await request.get_json()
    update = Update.de_json(data, app.bot)
    await app.application.process_update(update)
    return "ok"

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
        "به ربات کتاب هوژین حرمان خوش آمدید.",
        reply_markup=main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if query.data == "buy":
        msg = (
            "شماره کارت برای پرداخت:\n"
            "5859 8311 3314 0268\n\n"
            "لطفا فیش واریزی را همینجا ارسال کنید تا مورد تایید قرار بگیرد.\n"
            "هزینه کتاب ۱۱۰ هزارتومان میباشد.\n"
            "ممکن است تایید فیش کمی زمان‌بر باشد پس لطفا صبور باشید.\n"
            "در صورت تایید فایل پی دی اف برایتان در همینجا ارسال میشود.\n"
            "اگر هرگونه مشکلی برایتان پیش آمد در بخش انتقادات و پیشنهادات برای ما ارسال کنید تا بررسی شود."
        )
        user_waiting_for_receipt.add(user.id)
        await query.edit_message_text(msg)

    elif query.data == "feedback":
        msg = (
            "اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند حتما در این بخش بنویسید تا بررسی شود.\n"
            "مطمئن باشید نظرات شما خوانده میشود و باارزش خواهد بود.☺️\n\n"
            "پیام خود را ارسال کنید:"
        )
        await query.edit_message_text(msg)

    elif query.data == "about_book":
        await query.edit_message_text(ABOUT_BOOK_TEXT)

    elif query.data == "about_author":
        await query.edit_message_text(ABOUT_AUTHOR_TEXT)

    elif query.data == "audiobook":
        await query.edit_message_text(AUDIOBOOK_TEXT)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text if update.message.text else ""
    receipt_file_id = None

    if user_id in user_waiting_for_receipt:
        # دریافت فیش (عکس یا سند)
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

        # ارسال فیش به ادمین برای تایید یا رد
        if receipt_file_id:
            if update.message.photo:
                await context.bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=receipt_file_id,
                    caption=f"فیش پرداختی از @{user.username or user.first_name} (ID: {user_id})",
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
                    caption=f"فیش پرداختی از @{user.username or user.first_name} (ID: {user_id})",
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
                text=f"فیش پرداختی متنی از @{user.username or user.first_name} (ID: {user_id}):\n\n{text}",
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton("تایید ✅", callback_data=f"approve_{user_id}"),
                        InlineKeyboardButton("رد ❌", callback_data=f"reject_{user_id}")
                    ]]
                )
            )
        await update.message.reply_text("فیش شما دریافت شد و در حال بررسی است. لطفا شکیبا باشید.")
        return

    # بخش انتقادات و پیشنهادات (پیام‌ها به ادمین ارسال میشه)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"پیام از @{user.username or user.first_name} (ID: {user_id}):\n\n{text}",
    )
    await update.message.reply_text("پیام شما به ادمین ارسال شد. ممنون از نظرتون!")

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
                await context.bot.send_message(chat_id=user_id, text="پرداخت شما تایید شد. کتاب برای شما ارسال گردید. از خریدتان متشکریم! ❤️")
            else:
                await context.bot.send_message(chat_id=ADMIN_ID, text="فایل کتاب در سرور موجود نیست!")

        else:
            users_payment[user_id]["status"] = "rejected"
            await query.edit_message_text(f"❌ پرداخت کاربر {user_id} رد شد.")
            await context.bot.send_message(chat_id=user_id, text="پرداخت شما تایید نشد. لطفا دوباره فیش را ارسال کنید یا با پشتیبانی تماس بگیرید.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستور ناشناخته. لطفا از منوی اصلی استفاده کنید.")

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

‏application.run_polling()


if __name__ == "__main__":
    run_app()
