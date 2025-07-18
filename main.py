from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from config import TOKEN

def start(update: Update, context: CallbackContext) -> None:
    """ارسال پیام خوش‌آمدگویی"""
    user = update.effective_user
    update.message.reply_text(f"سلام {user.first_name}! به بات من خوش آمدید. ✨")

def main() -> None:
    """شروع بات"""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    
    updater.start_polling()
    print("🤖 Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
