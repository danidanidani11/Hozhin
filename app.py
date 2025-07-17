from flask import Flask, request
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
import logging
import os

# Configuration
BOT_TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@fromheartsoul"
CARD_NUMBER = "5859 8311 3314 0268"
BOOK_PRICE = 110000  # 110,000 Tomans
PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Data storage (in production use a proper database)
user_data = {}
payment_requests = {}

app = Flask(__name__)

@app.route('/')
def index():
    return "Book Store Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# Initialize bot and dispatcher
bot = telegram.Bot(token=BOT_TOKEN)
updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Start command
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id
    
    # Check channel subscription
    try:
        member = context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['left', 'kicked']:
            update.message.reply_text(
                f"سلام {user.first_name}!\n\n"
                "برای استفاده از ربات، لطفا در کانال ما عضو شوید:\n"
                f"{CHANNEL_USERNAME}\n"
                "سپس /start را دوباره بزنید."
            )
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        update.message.reply_text("مشکلی در بررسی عضویت شما پیش آمده. لطفا بعدا تلاش کنید.")
        return
    
    show_main_menu(update, context, user)

def show_main_menu(update, context, user):
    keyboard = [
        [InlineKeyboardButton("خرید کتاب", callback_data='buy_book')],
        [InlineKeyboardButton("انتقادات و پیشنهادات", callback_data='feedback')],
        [InlineKeyboardButton("درباره کتاب", callback_data='about_book')],
        [InlineKeyboardButton("درباره نویسنده", callback_data='about_author')],
        [InlineKeyboardButton("کتاب صوتی", callback_data='audio_book')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        update.message.reply_text(
            f"سلام {user.first_name}!\n\n"
            "به ربات فروش کتاب هوژین و حرمان خوش آمدید.\n"
            "لطفا یکی از گزینه های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        update.callback_query.edit_message_text(
            f"سلام {user.first_name}!\n\n"
            "به ربات فروش کتاب هوژین و حرمان خوش آمدید.\n"
            "لطفا یکی از گزینه های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )
    
    # Reset user state
    if user.id in user_data:
        del user_data[user.id]

# Button handlers
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    if query.data == 'buy_book':
        show_buy_book(query, context)
    elif query.data == 'feedback':
        show_feedback(query, context)
    elif query.data == 'about_book':
        show_about_book(query, context)
    elif query.data == 'about_author':
        show_about_author(query, context)
    elif query.data == 'audio_book':
        show_audio_book(query, context)
    elif query.data == 'back_to_menu':
        show_main_menu(update, context, query.from_user)
    elif query.data.startswith('approve_'):
        handle_approval(query, context, True)
    elif query.data.startswith('reject_'):
        handle_approval(query, context, False)

def show_buy_book(query, context):
    keyboard = [
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        f"شماره کارت برای واریز: {CARD_NUMBER}\n\n"
        "لطفا فیش را همینجا ارسال کنید تا مورد تایید قرار بگیرد. هزینه کتاب ۱۱۰ هزارتومان میباشد.\n"
        "ممکن است تایید فیش کمی زمان‌بر باشد پس لطفا صبور باشید.\n"
        "در صورت تایید فایل پی دی اف برایتان در همینجا ارسال میشود.\n"
        "اگر هرگونه مشکلی برایتان پیش آمد در بخش انتقادات و پیشنهادات برای ما ارسال کنید تا بررسی شود.",
        reply_markup=reply_markup
    )
    
    user_data[query.from_user.id] = {'state': 'waiting_for_receipt'}

def show_feedback(query, context):
    keyboard = [
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "اگر درباره کتاب پیشنهاد یا انتقادی دارید که می‌تواند برای پیشرفت در این مسیر کمک کند حتما در این بخش بنویسید تا بررسی شود.\n"
        "مطمئن باشید نظرات شما خوانده میشود و باارزش خواهد بود.☺️",
        reply_markup=reply_markup
    )
    
    user_data[query.from_user.id] = {'state': 'waiting_for_feedback'}

def show_about_book(query, context):
    keyboard = [
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "رمان هوژین و حرمان روایتی عاشقانه است که تلفیقی از سبک سورئالیسم، رئالیسم و روان است که تفاوت آنها را در طول کتاب درک خواهید کرد.نام هوژین واژه ای کردی است که تعبیر آن کسی است که با آمدنش نور زندگی شما میشود و زندگی را تازه میکند؛در معنای کلی امید را به شما برمیگرداند.حرمان نیز واژه ای کردی_عربی است که معنای آن در وصف کسی است که بالاترین حد اندوه و افسردگی را تجربه کرده و با این حال آن را رها کرده است.در تعبیری مناسب تر؛هوژین در کتاب برای حرمان روزنه نور و امیدی بوده است که باعث رهایی حرمان از غم و اندوه میشود و دلیل اصلی رهایی برای حرمان تلقی میشود.کاژه هم به معنای کسی است که در کنار او احساس امنیت دارید. \n"
        "کتاب از نگاه اول شخص روایت میشود و پیشنهاد من این است که ابتدا کتاب را به ترتیب از بخش اول تا سوم بخوانید؛اما اگر علاقه داشتید مجدداً آن را مطالعه کنید،برای بار دوم، ابتدا بخش دوم و سپس بخش اول و در آخر بخش سوم را بخوانید.در این صورت دو برداشت متفاوت از کتاب خواهید داشت که هر کدام زاویه نگاه متفاوتی در شما به وجود می آورد. \n"
        "برخی بخش ها و تجربه های کتاب بر اساس داستان واقعی روایت شده و برخی هم سناریوهای خیالی و خاص همراه بوده است که دانستن آن برای شما خالی از لطف نیست.یک سری نکات شایان ذکر است که به عنوان  خواننده کتاب حق دارید بدانید.اگر در میان بند های کتاب شعری را مشاهده کردید؛آن ابیات توسط شاعران فرهیخته کشور عزیزمان ایران نوشته شده است و با تحقیق و جست و جو میتوانید متن کامل و نام نویسنده را دریابید.اگر مطلبی را داخل \"این کادر\" دیدید به معنای این است که آن مطلب احتمالا برگرفته از نامه ها یا بیت های کوتاه است.در آخر هم اگر جملاتی را مشاهده کردید که از قول فلانی روایت شده است و مانند آن را قبلا شنیده اید؛احتمالا برگرفته از مطالبی است که ملکه ذهن من بوده و آنها را در طول کتاب استفاده کرده ام.\n\n"
        "درصورت خرید امیدوارم لذت ببرید.",
        reply_markup=reply_markup
    )

def show_about_author(query, context):
    keyboard = [
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "سلام رفقا 🙋🏻‍♂\n"
        "مانی محمودی هستم نویسنده کتاب هوژین حرمان.\n"
        "نویسنده ای جوان هستم که با کنار هم گذاشتن نامه های متعدد موفق به نوشتن این کتاب شدم.کار نویسندگی را از سن ۱۳ سالگی با کمک معلم ادبیاتم شروع کردم و تا امروز به این کار را ادامه می‌دهم.این کتاب اولین اثر بنده هستش و در تلاش هستم تا در طی سالیان آینده کتاب های بیشتری خلق کنم.\n\n"
        "بیشتر از این وقتتون رو نمیگیرم.امیدوار لذت ببرید😄❤️",
        reply_markup=reply_markup
    )

def show_audio_book(query, context):
    keyboard = [
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "این بخش به زودی فعال میشود.",
        reply_markup=reply_markup
    )

def handle_approval(query, context, is_approved):
    payment_id = query.data.split('_')[1]
    
    if payment_id not in payment_requests:
        query.edit_message_text("این درخواست پرداخت دیگر وجود ندارد یا قبلاً پردازش شده است.")
        return
    
    payment = payment_requests[payment_id]
    user_id = payment['user_id']
    chat_id = payment['chat_id']
    
    if is_approved:
        # Send book to user
        context.bot.send_message(
            chat_id=chat_id,
            text="پرداخت شما تایید شد! لینک دانلود کتاب:\n[لینک کتاب قرار داده شود]"
        )
        
        # Notify admin
        query.edit_message_text(f"پرداخت کاربر {user_id} تایید شد و کتاب برای او ارسال گردید.")
    else:
        # Notify user
        context.bot.send_message(
            chat_id=chat_id,
            text="متاسفانه پرداخت شما تایید نشد. لطفا با پشتیبانی تماس بگیرید."
        )
        
        # Notify admin
        query.edit_message_text(f"پرداخت کاربر {user_id} رد شد.")
    
    # Update payment status
    payment_requests[payment_id]['status'] = 'approved' if is_approved else 'rejected'

# Handle messages
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    if user_id not in user_data:
        update.message.reply_text("لطفا از منوی اصلی یک گزینه را انتخاب کنید.")
        return
    
    user_state = user_data[user_id].get('state')
    
    if user_state == 'waiting_for_receipt':
        # Payment receipt received
        receipt = update.message
        payment_id = f"{user_id}_{receipt.message_id}"
        
        payment_requests[payment_id] = {
            'user_id': user_id,
            'chat_id': update.message.chat_id,
            'receipt_message_id': receipt.message_id,
            'status': 'pending'
        }
        
        # Forward to admin with approval buttons
        keyboard = [
            [
                InlineKeyboardButton("تایید ✅", callback_data=f'approve_{payment_id}'),
                InlineKeyboardButton("رد ❌", callback_data=f'reject_{payment_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"درخواست پرداخت جدید از کاربر {user_id}:\n"
                 f"مبلغ: {BOOK_PRICE} تومان\n"
                 f"لطفا فیش ارسالی را بررسی کنید:",
            reply_markup=reply_markup
        )
        
        # Forward the receipt to admin
        context.bot.forward_message(
            chat_id=ADMIN_ID,
            from_chat_id=update.message.chat_id,
            message_id=receipt.message_id
        )
        
        update.message.reply_text("فیش پرداخت شما برای تایید به ادمین ارسال شد. لطفا منتظر بمانید.")
        
    elif user_state == 'waiting_for_feedback':
        # Feedback received
        feedback_text = update.message.text
        
        # Forward to admin
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"نظر/انتقاد جدید از کاربر {user_id}:\n\n{feedback_text}"
        )
        
        update.message.reply_text("نظر شما با موفقیت ارسال شد. با تشکر از مشارکت شما!")

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update {update} caused error {context.error}')

# Set up handlers
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_error_handler(error)

# Start the bot
if __name__ == '__main__':
    # For local testing
    # updater.start_polling()
    # updater.idle()
    
    # For production with Flask
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://hozhin.onrender.com/{BOT_TOKEN}"
    )
    app.run(host='0.0.0.0', port=PORT)
