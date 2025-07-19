import os
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode, ContentType
from aiogram.fsm.storage.memory import MemoryStorage
import json

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
WEBHOOK_URL = "https://hozhin.onrender.com/webhook"

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

app = Flask(__name__)

# --------------------- کیبورد اصلی ---------------------
def main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 خرید کتاب", callback_data="buy")
    builder.button(text="📚 درباره کتاب", callback_data="about_book")
    builder.button(text="🖋️ درباره نویسنده", callback_data="about_author")
    builder.button(text="📩 ارسال نظر", callback_data="feedback")
    builder.button(text="🎧 کتاب صوتی", callback_data="audio_book")
    return builder.as_markup()

# --------------------- start ---------------------
@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "به ربات رسمی کتاب «هوژین حرمان» خوش آمدید.\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_keyboard()
    )

# --------------------- دکمه خرید ---------------------
@dp.callback_query(F.data == "buy")
async def buy_book(callback: CallbackQuery):
    await callback.message.answer("لطفاً رسید واریزی خود را به صورت عکس، فایل یا متن ارسال نمایید تا بررسی شود.")
    await callback.answer()

@dp.message(F.content_type.in_({ContentType.TEXT, ContentType.PHOTO, ContentType.DOCUMENT}))
async def handle_payment(message: Message):
    user = message.from_user
    if str(user.id) == str(ADMIN_ID):
        return
    forward_msg = await message.forward(ADMIN_ID)
    await bot.send_message(
        ADMIN_ID,
        f"📥 فیش پرداختی جدید از @{user.username or 'ندارد'}\nبرای تایید یا رد، دکمه‌های زیر را بزن:",
        reply_markup=InlineKeyboardBuilder()
        .button(text="✅ تایید", callback_data=f"approve_{user.id}")
        .button(text="❌ رد", callback_data=f"reject_{user.id}")
        .as_markup()
    )
    await message.reply("فیش شما ارسال شد. پس از تایید، فایل کتاب برایتان ارسال می‌شود.")

# --------------------- ادمین تایید / رد ---------------------
@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_document(user_id, FSInputFile("books/hozhin_harman.pdf"))
    await callback.message.edit_text("✅ فیش تایید شد و کتاب ارسال شد.")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(user_id, "❌ فیش شما رد شد. لطفاً دوباره تلاش کنید.")
    await callback.message.edit_text("❌ فیش رد شد.")

# --------------------- دکمه درباره کتاب ---------------------
@dp.callback_query(F.data == "about_book")
async def about_book(callback: CallbackQuery):
    await callback.message.answer("📖 کتاب «هوژین حرمان» داستانی اجتماعی با محتوایی انسانی و شاعرانه است...")
    await callback.answer()

# --------------------- دکمه درباره نویسنده ---------------------
@dp.callback_query(F.data == "about_author")
async def about_author(callback: CallbackQuery):
    await callback.message.answer("🖋️ نویسنده این اثر با نگاهی ژرف و انسانی به مسائل اجتماعی...")
    await callback.answer()

# --------------------- دکمه ارسال نظر ---------------------
@dp.callback_query(F.data == "feedback")
async def feedback(callback: CallbackQuery):
    await callback.message.answer("✍️ لطفاً نظر، پیشنهاد یا انتقاد خود را ارسال کنید.")
    await callback.answer()

@dp.message(F.text & ~F.from_user.id == ADMIN_ID)
async def receive_feedback(message: Message):
    user = message.from_user
    await bot.send_message(ADMIN_ID, f"🗣️ نظر جدید از @{user.username or 'ندارد'}:\n\n{message.text}")
    await message.reply("✅ نظر شما با موفقیت ارسال شد. ممنونیم.")

# --------------------- دکمه کتاب صوتی ---------------------
@dp.callback_query(F.data == "audio_book")
async def audio_book(callback: CallbackQuery):
    await callback.message.answer("🎧 بخش کتاب صوتی در حال توسعه است. به‌زودی در دسترس قرار می‌گیرد.")
    await callback.answer()

# --------------------- Webhook Endpoint ---------------------
@app.post("/webhook")
async def webhook():
    req = await request.get_data()
    await dp.feed_webhook_update(bot, req)
    return {"ok": True}

# --------------------- Set Webhook ---------------------
@app.get("/")
async def index():
    await bot.set_webhook(WEBHOOK_URL)
    return "وب‌هوک تنظیم شد."

# --------------------- اجرای Flask ---------------------
if __name__ == "__main__":
    import asyncio
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:10000"]

    asyncio.run(serve(app, config))
