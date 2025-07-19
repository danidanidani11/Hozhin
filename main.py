import os
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
import asyncio

# تنظیمات
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
WEBHOOK_URL = "https://hozhin.onrender.com/webhook"
PDF_PATH = "books/hozhin_harman.pdf"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
app = Flask(__name__)

# دکمه‌های اصلی
def main_menu():
    keyboard = [
        [InlineKeyboardButton(text="🛒 خرید کتاب", callback_data="buy")],
        [InlineKeyboardButton(text="📖 درباره کتاب", callback_data="about_book")],
        [InlineKeyboardButton(text="👤 درباره نویسنده", callback_data="about_author")],
        [InlineKeyboardButton(text="💬 انتقادات و پیشنهادات", callback_data="feedback")],
        [InlineKeyboardButton(text="🎧 کتاب صوتی (درحال توسعه)", callback_data="audio")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# استارت
@dp.message(F.text == "/start")
async def start(msg: Message):
    await msg.answer("سلام! به ربات رسمی کتاب هوژین حرمان خوش آمدید.", reply_markup=main_menu())

# کالبک‌ها
@dp.callback_query(F.data == "buy")
async def buy(cb: CallbackQuery):
    await cb.message.answer("لطفاً مبلغ را به شماره کارت زیر واریز کرده و رسید را ارسال نمایید:\n\n💳 6037-9917-1234-5678\n\nبعد از ارسال، رسید شما توسط ادمین بررسی خواهد شد.")
    await cb.answer()

@dp.callback_query(F.data == "about_book")
async def about_book(cb: CallbackQuery):
    await cb.message.answer("📘 کتاب هوژین حرمان روایت‌گر داستانی از دل احساس و منطق است...\n(اطلاعات بیشتر قرار دهید)")
    await cb.answer()

@dp.callback_query(F.data == "about_author")
async def about_author(cb: CallbackQuery):
    await cb.message.answer("✍️ نویسنده: فلانی\nمتولد ...، دارای آثار متعدد در حوزه ادبیات معاصر.")
    await cb.answer()

@dp.callback_query(F.data == "feedback")
async def feedback(cb: CallbackQuery):
    await cb.message.answer("لطفاً نظرات، انتقادات یا پیشنهادات خود را همین‌جا ارسال کنید.")
    await cb.answer()

@dp.callback_query(F.data == "audio")
async def audio(cb: CallbackQuery):
    await cb.message.answer("🔊 نسخه صوتی کتاب در حال آماده‌سازی است و به‌زودی در دسترس قرار می‌گیرد.")
    await cb.answer()

# دریافت پیام‌های متنی و فایل (برای رسید خرید یا فیدبک)
@dp.message(F.content_type.in_({'text', 'photo', 'document'}))
async def handle_any(msg: Message):
    if str(msg.from_user.id) == str(ADMIN_ID):
        await msg.answer("ادمین عزیز پیام شما دریافت شد.")
    else:
        await bot.send_message(ADMIN_ID, f"📥 پیام جدید از کاربر:\n\nنام: {msg.from_user.full_name}\nآی‌دی: {msg.from_user.id}")
        if msg.text:
            await bot.send_message(ADMIN_ID, f"📨 پیام:\n{msg.text}")
        elif msg.photo or msg.document:
            file_id = msg.photo[-1].file_id if msg.photo else msg.document.file_id
            await bot.send_message(ADMIN_ID, "🖼 رسید پرداخت:")
            await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=msg.chat.id, message_id=msg.message_id)
        await msg.answer("✅ پیام یا رسید شما ارسال شد و پس از بررسی ادمین، پاسخ داده خواهد شد.")

# Webhook endpoint
@app.post("/webhook")
async def webhook():
    update = types.Update.model_validate(request.json)
    await dp.feed_update(bot, update)
    return "ok"

# راه‌اندازی وب‌هوک هنگام اجرا
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    asyncio.run(on_startup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
