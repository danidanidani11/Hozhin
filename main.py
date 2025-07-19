import os
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
WEBHOOK_URL = "https://hozhin.onrender.com/webhook"
BOOK_FILE_PATH = "books/hozhin_harman.pdf"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# دکمه منو
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📘 خرید کتاب", callback_data="buy")
    builder.button(text="🗣 ارسال نظر", callback_data="feedback")
    builder.button(text="📖 درباره کتاب", callback_data="about_book")
    builder.button(text="✍️ درباره نویسنده", callback_data="about_author")
    builder.button(text="🔊 کتاب صوتی (بزودی)", callback_data="audio_book")
    builder.adjust(1)
    return builder.as_markup()

# دستور /start
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 سلام! به ربات رسمی کتاب هوژین حرمان خوش اومدی. یکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=get_main_menu()
    )

# دکمه‌ها
@dp.callback_query()
async def handle_callbacks(callback: types.CallbackQuery):
    data = callback.data
    if data == "buy":
        await callback.message.answer("💳 لطفاً رسید پرداخت خود را ارسال کنید (عکس یا فایل).")
    elif data == "feedback":
        await callback.message.answer("📝 لطفاً نظر یا پیشنهاد خود را بنویسید.")
    elif data == "about_book":
        await callback.message.answer("📖 کتاب هوژین حرمان اثری عمیق از دل کردستان...")
    elif data == "about_author":
        await callback.message.answer("✍️ نویسنده این اثر با نگاهی عاشقانه داستانی ناب را خلق کرده است.")
    elif data == "audio_book":
        await callback.message.answer("🔊 کتاب صوتی بزودی منتشر می‌شود.")
    await callback.answer()

# رسید پرداخت (عکس یا سند)
@dp.message(F.content_type.in_({"photo", "document"}))
async def handle_receipt(message: types.Message):
    user = message.from_user
    caption = f"🧾 رسید پرداخت از {user.full_name} ({user.id})"
    if message.photo:
        await bot.send_photo(ADMIN_ID, photo=message.photo[-1].file_id, caption=caption)
    elif message.document:
        await bot.send_document(ADMIN_ID, document=message.document.file_id, caption=caption)
    await message.reply("✅ رسید شما ارسال شد. پس از بررسی، کتاب برایتان ارسال می‌شود.")

# پیام متنی - نظرات کاربران
@dp.message(F.text)
async def handle_text(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(ADMIN_ID, f"🗣 پیام از {message.from_user.full_name} ({message.from_user.id}):\n{message.text}")
        await message.reply("✅ پیام شما ثبت شد.")

# ارسال فایل PDF توسط ادمین
@dp.message(F.text.startswith("/sendbook"))
async def send_book(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.strip().split()
        user_id = int(parts[1])
        book = FSInputFile(BOOK_FILE_PATH)
        await bot.send_document(user_id, book, caption="📕 فایل PDF کتاب هوژین حرمان")
        await message.reply("✅ ارسال شد.")
    except Exception as e:
        await message.reply(f"❌ خطا: {e}")

# Flask app برای webhook
app = Flask(__name__)

@app.route("/")
def index():
    return "ربات فعال است."

@app.route("/webhook", methods=["POST"])
async def webhook():
    update = types.Update.model_validate(await request.get_json())
    await dp.feed_update(bot, update)
    return "ok"

async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

def start():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    start()
