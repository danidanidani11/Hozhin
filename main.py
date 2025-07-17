from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import os

# Bot configuration
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_ID = "@fromheartsoul"
PDF_FILE_PATH = "hozhin_harman.pdf"  # Update with the actual path to your PDF file

# Store pending receipts and feedback
pending_receipts = {}  # {user_id: {'chat_id': int, 'message_id': int}}
pending_feedback = {}  # {user_id: {'chat_id': int, 'message_id': int}}

def check_membership(context: CallbackContext, user_id: int) -> bool:
    try:
        member_status = context.bot.get_chat_member(CHANNEL_ID, user_id).status
        return member_status in ['member', 'administrator', 'creator']
    except:
        return False

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not check_membership(context, user_id):
        update.message.reply_text(
            "لطفاً ابتدا در کانال @fromheartsoul عضو شوید و سپس دوباره /start را بزنید."
        )
        return

    keyboard = [
        [InlineKeyboardButton("📚 خرید کتاب", callback_data='buy_book')],
        [InlineKeyboardButton("💬 انتقادات و پیشنهادات", callback_data='feedback')],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data='about_book')],
        [InlineKeyboardButton("✍️ درباره نویسنده", callback_data='about_author')],
        [InlineKeyboardButton("🎧 کتاب صوتی", callback_data='audio_book')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("به ربات هوژین و حرمان خوش آمدید! لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup)

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if not check_membership(context, user_id):
        query.answer()
        query.message.reply_text("لطفاً ابتدا در کانال @fromheartsoul عضو شوید.")
        return

    query.answer()
    data = query.data

    if data == 'buy_book':
        query.message.reply_text(
            "شماره کارت: 5859 8311 3314 0268\n\n"
            "لطفاً فیش واریزی را همینجا ارسال کنید تا مورد تأیید قرار بگیرد. هزینه کتاب ۱۱۰ هزارتومان می‌باشد.\n"
            "ممکن است تأیید فیش کمی زمان‌بر باشد، پس لطفاً صبور باشید.\n"
            "در صورت تأیید، فایل PDF برایتان در همینجا ارسال می‌شود.\n"
            "اگر هرگونه مشکلی پیش آمد، در بخش انتقادات و پیشنهادات برای ما ارسال کنید تا بررسی شود."
        )
        context.user_data['state'] = 'awaiting_receipt'

    elif data == 'feedback':
        query.message.reply_text(
            "اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند، حتماً در این بخش بنویسید تا بررسی شود.\n"
            "مطمئن باشید نظرات شما خوانده می‌شود و باارزش خواهد بود. ☺️"
        )
        context.user_data['state'] = 'awaiting_feedback'

    elif data == 'about_book':
        query.message.reply_text(
            "رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد. "
            "نام هوژین واژه‌ای کردی است که تعبیر آن کسی است که با آمدنش نور زندگی شما می‌شود و زندگی را تازه می‌کند؛ در معنای کلی امید را به شما برمی‌گرداند. "
            "حرمان نیز واژه‌ای کردی_عربی است که معنای آن در وصف کسی است که بالاترین حد اندوه و افسردگی را تجربه کرده و با این حال آن را رها کرده است. "
            "در تعبیری مناسب‌تر؛ هوژین در کتاب برای حرمان روزنه نور و امیدی بوده است که باعث رهایی حرمان از غم و اندوه می‌شود و دلیل اصلی رهایی برای حرمان تلقی می‌شود. "
            "کاژه هم به معنای کسی است که در کنار او احساس امنیت دارید.\n\n"
            "کتاب از نگاه اول شخص روایت می‌شود و پیشنهاد من این است که ابتدا کتاب را به ترتیب از بخش اول تا سوم بخوانید؛ اما اگر علاقه داشتید مجدداً آن را مطالعه کنید، "
            "برای بار دوم، ابتدا بخش دوم و سپس بخش اول و در آخر بخش سوم را بخوانید. در این صورت دو برداشت متفاوت از کتاب خواهید داشت که هر کدام زاویه نگاه متفاوتی در شما به وجود می‌آورد.\n\n"
            "برخی بخش‌ها و تجربه‌های کتاب بر اساس داستان واقعی روایت شده و برخی هم سناریوهای خیالی و خاص همراه بوده است که دانستن آن برای شما خالی از لطف نیست. "
            "یک سری نکات شایان ذکر است که به عنوان خواننده کتاب حق دارید بدانید. اگر در میان بندهای کتاب شعری را مشاهده کردید؛ آن ابیات توسط شاعران فرهیخته کشور عزیزمان ایران نوشته شده است "
            "و با تحقیق و جست‌وجو می‌توانید متن کامل و نام نویسنده را دریابید. اگر مطلبی را داخل \"این کادر\" دیدید به معنای این است که آن مطلب احتمالاً برگرفته از نامه‌ها یا بیت‌های کوتاه است. "
            "در آخر هم اگر جملاتی را مشاهده کردید که از قول فلانی روایت شده است و مانند آن را قبلاً شنیده‌اید؛ احتمالاً برگرفته از مطالبی است که ملکه ذهن من بوده و آنها را در طول کتاب استفاده کرده‌ام.\n\n"
            "در صورت خرید امیدوارم لذت ببرید."
        )

    elif data == 'about_author':
        query.message.reply_text(
            "سلام رفقا 🙋🏻‍♂\n"
            "مانی محمودی هستم، نویسنده کتاب هوژین و حرمان.\n"
            "نویسنده‌ای جوان هستم که با کنار هم گذاشتن نامه‌های متعدد موفق به نوشتن این کتاب شدم. "
            "کار نویسندگی را از سن ۱۳ سالگی با کمک معلم ادبیاتم شروع کردم و تا امروز به این کار ادامه می‌دهم. "
            "این کتاب اولین اثر بنده هست و در تلاش هستم تا در طی سالیان آینده کتاب‌های بیشتری خلق کنم.\n\n"
            "بیشتر از این وقتتون رو نمی‌گیرم. امیدوارم لذت ببرید 😄❤️"
        )

    elif data == 'audio_book':
        query.message.reply_text("این بخش به زودی فعال می‌شود.")

    elif data.startswith('approve_receipt_') or data.startswith('reject_receipt_'):
        receipt_id = int(data.split('_')[-1])
        user_id = None
        for uid, info in pending_receipts.items():
            if info['message_id'] == receipt_id:
                user_id = uid
                break

        if user_id is None:
            query.message.reply_text("این فیش دیگر معتبر نیست.")
            return

        if data.startswith('approve_receipt_'):
            query.message.reply_text("فیش تأیید شد. لطفاً فایل PDF کتاب را ارسال کنید.")
            context.user_data['state'] = 'awaiting_pdf'
            context.user_data['recipient_user_id'] = user_id
        else:
            context.bot.send_message(user_id, "فیش واریزی شما تأیید نشد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.")
            del pending_receipts[user_id]
            query.message.reply_text("فیش رد شد.")

    elif data.startswith('reply_feedback_'):
        feedback_id = int(data.split('_')[-1])
        user_id = None
        for uid, info in pending_feedback.items():
            if info['message_id'] == feedback_id:
                user_id = uid
                break

        if user_id is None:
            query.message.reply_text("این پیام دیگر معتبر نیست.")
            return

        query.message.reply_text("لطفاً پاسخ خود به کاربر را ارسال کنید.")
        context.user_data['state'] = 'awaiting_reply'
        context.user_data['recipient_user_id'] = user_id

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not check_membership(context, user_id):
        update.message.reply_text("لطفاً ابتدا در کانال @fromheartsoul عضو شوید.")
        return

    state = context.user_data.get('state')
    if state == 'awaiting_receipt':
        if update.message.photo or update.message.text:
            # Forward receipt to admin
            forwarded = context.bot.forward_message(ADMIN_ID, update.message.chat_id, update.message.message_id)
            keyboard = [
                [InlineKeyboardButton("✅ تأیید", callback_data=f'approve_receipt_{forwarded.message_id}'),
                 InlineKeyboardButton("❌ رد", callback_data=f'reject_receipt_{forwarded.message_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(ADMIN_ID, "فیش واریزی جدید:", reply_markup=reply_markup)
            pending_receipts[user_id] = {'chat_id': update.message.chat_id, 'message_id': forwarded.message_id}
            update.message.reply_text("فیش شما برای بررسی ارسال شد. لطفاً منتظر تأیید باشید.")
            context.user_data['state'] = None

    elif state == 'awaiting_feedback':
        if update.message.text:
            # Forward feedback to admin
            forwarded = context.bot.forward_message(ADMIN_ID, update.message.chat_id, update.message.message_id)
            keyboard = [[InlineKeyboardButton("پاسخ دادن", callback_data=f'reply_feedback_{forwarded.message_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(ADMIN_ID, "انتقاد یا پیشنهاد جدید:", reply_markup=reply_markup)
            pending_feedback[user_id] = {'chat_id': update.message.chat_id, 'message_id': forwarded.message_id}
            update.message.reply_text("انتقاد یا پیشنهاد شما ارسال شد. در صورت نیاز، پاسخ دریافت خواهید کرد.")
            context.user_data['state'] = None

    elif state == 'awaiting_pdf' and user_id == ADMIN_ID:
        if update.message.document and update.message.document.mime_type == 'application/pdf':
            recipient_user_id = context.user_data.get('recipient_user_id')
            if recipient_user_id:
                # Send PDF to user
                context.bot.send_document(recipient_user_id, update.message.document.file_id, caption="فایل PDF کتاب هوژین و حرمان برای شما ارسال شد. از خرید شما متشکریم!")
                context.bot.send_message(ADMIN_ID, "فایل PDF با موفقیت برای کاربر ارسال شد.")
                if recipient_user_id in pending_receipts:
                    del pending_receipts[recipient_user_id]
                context.user_data['state'] = None
                context.user_data['recipient_user_id'] = None
            else:
                update.message.reply_text("خطا: کاربر مقصد یافت نشد.")
        else:
            update.message.reply_text("لطفاً فایل PDF کتاب را ارسال کنید.")

    elif state == 'awaiting_reply' and user_id == ADMIN_ID:
        if update.message.text:
            recipient_user_id = context.user_data.get('recipient_user_id')
            if recipient_user_id:
                context.bot.send_message(recipient_user_id, f"پاسخ ادمین: {update.message.text}")
                context.bot.send_message(ADMIN_ID, "پاسخ شما برای کاربر ارسال شد.")
                if recipient_user_id in pending_feedback:
                    del pending_feedback[recipient_user_id]
                context.user_data['state'] = None
                context.user_data['recipient_user_id'] = None
            else:
                update.message.reply_text("خطا: کاربر مقصد یافت نشد.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
