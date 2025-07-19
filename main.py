import os
import json
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

# تنظیمات اولیه
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
WEBHOOK_URL = "https://hozhin.onrender.com/webhook"
BOOK_FILE_PATH = "books/hozhin_harman.pdf"
CHANNEL_USERNAME = "fromheartsoul"

# راه‌اندازی Bot و Dispatcher
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# ساخت دکمه‌های اصلی
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📘 خرید کتاب", callback_data="buy")
    builder.button(text="🗣 ارسال نظر", callback_data="feedback")
    builder.button(text="📖 درباره کتاب", callback_data="about_book")
    builder.button(text="✍️ درباره نویسنده", callback_data="about_author")
    builder.button(text="🔊 کتاب صوتی (بزودی)", callback_data="audio_book")
    builder.adjust(1)
    return builder.as_markup()

# فرمان /start
@dp.message(F.text == "/start")
async def start_handler(message: types.Message):
    await message.answer(
        "<b>به ربات رسمی کتاب هوژین حرمان خوش آمدید.</b>\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_main_menu()
    )

# مدیریت دکمه‌ها
@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    data = callback.data

    if data == "buy":
        await callback.message.answer("💳 لطفاً رسید پرداخت خود را ارسال کنید (عکس یا PDF).")
    elif data == "feedback":
        await callback.message.answer("📝 لطفاً نظر یا پیشنهاد خود را بنویسید و برای ما ارسال کنید.")
    elif data == "about_book":
        await callback.message.answer("📖 کتاب هوژین حرمان اثری عمیق و احساسی از دل کردستان است...")
    elif data == "about_author":
        await callback.message.answer("✍️ نویسنده این اثر، با نگاهی عاشقانه و درونی، داستانی ناب را خلق کرده است.")
    elif data == "audio_book":
        await callback.message.answer("🔊 کتاب صوتی در حال آماده‌سازی است. بزودی منتشر خواهد شد.")

    await callback.answer()

# فایل پرداخت توسط کاربر
@dp.message(F.content_type.in_({"photo", "document"}))
async def handle_payment_receipt(message: types.Message):
    user = message.from_user
    caption = f"🧾 رسید پرداخت از کاربر:\n\n👤 <b>{user.full_name}</b>\n🆔 <code>{user.id}</code>"

    # فوروارد به ادمین
    if message.photo:
        file_id = message.photo[-1].file_id
        await bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption)
    elif message.document:
        file_id = message.document.file_id
        await bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=caption)

    await message.reply("✅ رسید شما ارسال شد. پس از بررسی، کتاب برای شما ارسال می‌شود.")

# پیام متنی: نظر، پیشنهاد یا پیام عادی
@dp.message(F.content_type == "text")
async def handle_text(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        text = f"🗣 پیام جدید از کاربر:\n\n👤 <b>{message.from_user.full_name}</b>\n🆔 <code>{message.from_user.id}</code>\n\n💬 {message.text}"
        await bot.send_message(chat_id=ADMIN_ID, text=text)
        await message.reply("✅ پیام شما ثبت شد. ممنون از توجه شما.")

# ارسال کتاب PDF توسط ادمین
@dp.message(F.text.startswith("/sendbook") & F.from_user.id == ADMIN_ID)
async def send_book(message: types.Message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            return await message.reply("❌ فرمت صحیح دستور:\n`/sendbook USER_ID`", parse_mode="Markdown")
        user_id = int(parts[1])
        book = FSInputFile(BOOK_FILE_PATH)
        await bot.send_document(chat_id=user_id, document=book, caption="📕 فایل PDF کتاب هوژین حرمان")
        await message.reply("✅ کتاب برای کاربر ارسال شد.")
    except Exception as e:
        await message.reply(f"خطا در ارسال: {e}")

# راه‌اندازی Flask و Webhook
app = Flask(__name__)

@app.route("/")
def home():
    return "ربات هوژین حرمان فعال است."

@app.route("/webhook", methods=["POST"])
async def webhook():
    update = types.Update.model_validate(request.json)
    await dp.feed_update(bot, update)
    return "ok"

# راه‌اندازی Webhook
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    import asyncio
    asyncio.run(on_startup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
