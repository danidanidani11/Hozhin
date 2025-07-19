import os
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from aiogram.filters import Command
import asyncio

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
WEBHOOK_URL = "https://hozhin.onrender.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# کیبورد اصلی
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📕 خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton("✉️ انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton("📖 درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton("👤 درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton("🔊 کتاب صوتی (به‌زودی)", callback_data="coming_soon")],
    ])

# /start
@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.answer("سلام! به ربات کتاب هوژین حرمان خوش آمدید 🌹", reply_markup=main_keyboard())

# دکمه‌ها
@dp.callback_query(lambda c: True)
async def handle_buttons(cb: types.CallbackQuery):
    data = cb.data
    if data == "buy":
        text = "💳 کارت: 5859 8311 3314 0268\nلطفاً فیش را ارسال کنید."
    elif data == "feedback":
        text = "📝 لطفاً انتقادات و پیشنهادات خود را ارسال کنید."
    elif data == "about_book":
        text = "📖 درباره کتاب: رمان هوژین و حرمان...\n(متن کامل شما)"
    elif data == "about_author":
        text = "👤 درباره نویسنده: مانی محمودی...\n(متن کامل شما)"
    else:
        text = "🔊 این بخش به‌زودی فعال می‌شود."
    await cb.message.answer(text)
    await cb.answer()

# دریافت فیش یا نظر
@dp.message(types.ContentType.TEXT | types.ContentType.PHOTO | types.ContentType.DOCUMENT)
async def handle_user_msg(message: types.Message):
    await bot.forward_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"accept_{message.chat.id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{message.chat.id}")
        ]
    ])
    await bot.send_message(chat_id=ADMIN_ID, text=f"بررسی فیش برای {message.from_user.full_name}", reply_markup=kb)

# تایید یا رد توسط ادمین
@dp.callback_query(lambda c: c.data and (c.data.startswith("accept_") or c.data.startswith("reject_")))
async def admin_decision(cb: types.CallbackQuery):
    data = cb.data
    user_id = int(data.split("_")[1])
    if data.startswith("accept_"):
        await bot.send_message(user_id, "✅ فیش تایید شد. در ادامه فایل ارسال می‌شود.")
        await bot.send_document(user_id, InputFile("books/hozhin_harman.pdf"))
        await cb.message.edit_text("✅ ارسال شد.")
    else:
        await bot.send_message(user_id, "❌ فیش تایید نشد. لطفاً دوباره ارسال کنید.")
        await cb.message.edit_text("❌ رد شد.")
    await cb.answer()

# ==== Flask و Webhook ====
app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = await request.get_data()
    update = types.Update(**types.json.loads(data))
    await dp.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "ربات فعال است!"

async def set_webhook():
    await bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
