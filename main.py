from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import os

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://hozhin.onrender.com/{TOKEN}"  # آدرس دقیق پروژه‌ات در Render

app = Flask(__name__)

# دستور شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! به ربات خرید کتاب خوش آمدی. 📚")

# پیام متنی معمولی
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("پیام شما دریافت شد ✅")

telegram_app = ApplicationBuilder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

@app.route("/", methods=["GET"])
def home():
    return "ربات فعال است ✅"

@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.process_update(update)
        return "ok"

# تنظیم وب‌هوک در اولین اجرا
async def set_webhook():
    await telegram_app.bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    import asyncio
    asyncio.run(set_webhook())  # فقط بار اول وب‌هوک ست شود
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
