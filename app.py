from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from main import start, button_callback, handle_message, admin_reply
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN", "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0")

# تنظیم Application
application = Application.builder().token(TOKEN).build()
dp = application.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CallbackQueryHandler(button_callback))
dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
dp.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_message))
dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply))

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await dp.process_update(update)
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
