from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# توکن بات شما
TOKEN = "AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"

def start(update: Update, context: CallbackContext) -> None:
    """ارسال پیام خوش‌آمدگویی هنگام استارت بات"""
    user = update.effective_user
    update.message.reply_text(f"سلام {user.first_name}! به بات خوش آمدید. 😊")

def main() -> None:
    """شروع بات"""
    # ایجاد آپدیتور و دیسپچر
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # اضافه کردن هندلر برای کامند /start
    dispatcher.add_handler(CommandHandler("start", start))

    # شروع بات
    updater.start_polling()
    print("Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
