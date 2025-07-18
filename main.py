from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
import asyncio

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://hozhin.onrender.com/{TOKEN}"  # همین URL پروژه‌ت در Render

app = Flask(__name__)
application: Application = ApplicationBuilder().token(TOKEN).build()

@app.route("/", methods=["GET"])
def home():
    return "ربات فعاله ✅"

@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return "ok"

# 📌 دستور start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! به ربات خرید کتاب خوش آمدی 📖")

# 📌 هندلر پیام‌های متنی
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("پیامت دریافت شد ✅")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# 📌 تنظیم webhook فقط یکبار
async def set_webhook():
    await application.bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
