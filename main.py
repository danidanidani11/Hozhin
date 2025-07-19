import os
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, InputFile, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.webhook import WebhookRequestHandler
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
import asyncio

# ===== تنظیمات شما =====
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
WEBHOOK_URL = "https://hozhin.onrender.com"
PDF_FILE_PATH = "books/hozhin_harman.pdf"
CHANNEL_USERNAME = "fromheartsoul"

# ===== Flask برای Webhook =====
app = Flask(__name__)

# ===== Aiogram bot =====
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# ===== منوی اصلی =====
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(
    KeyboardButton("📖 خرید کتاب"),
    KeyboardButton("🗣️ انتقادات و پیشنهادات")
)
main_menu.add(
    KeyboardButton("✍️ درباره نویسنده"),
    KeyboardButton("ℹ️ درباره کتاب"),
    KeyboardButton("🔊 کتاب صوتی (بزودی)")
)

# ===== حالت‌ها برای خرید کتاب =====
class BuyBook(StatesGroup):
    waiting_for_payment = State()

# ===== استارت =====
@dp.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer(
        "📚 به ربات فروش کتاب «هوژین حرمان» خوش آمدید.\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_menu
    )

# ===== خرید کتاب =====
@dp.message(F.text == "📖 خرید کتاب")
async def buy_book(message: Message, state: FSMContext):
    await state.set_state(BuyBook.waiting_for_payment)
    await message.answer("💳 لطفاً رسید پرداخت خود را به صورت عکس یا متن ارسال کنید:")

@dp.message(BuyBook.waiting_for_payment, F.photo | F.text | F.document)
async def handle_payment(message: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تأیید", callback_data=f"approve_{message.from_user.id}"),
            InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{message.from_user.id}")
        ]
    ])

    caption = f"💰 رسید پرداخت از کاربر @{message.from_user.username or '---'} (ID: {message.from_user.id})"
    
    if message.photo:
        file_id = message.photo[-1].file_id
        await bot.send_photo(ADMIN_ID, file_id, caption=caption, reply_markup=kb)
    elif message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=kb)
    else:
        await bot.send_message(ADMIN_ID, f"{caption}\n\n📝 متن:\n{message.text}", reply_markup=kb)

    await message.answer("⏳ رسید شما برای ادمین ارسال شد. پس از بررسی، فایل برای شما ارسال خواهد شد.")
    await state.clear()

# ===== بررسی تأیید یا رد توسط ادمین =====
@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    pdf = InputFile(PDF_FILE_PATH)
    await bot.send_document(user_id, pdf, caption="📘 این هم فایل PDF کتاب «هوژین حرمان». مطالعه لذت‌بخشی داشته باشید.")
    await callback.answer("✅ ارسال شد.")
    await callback.message.edit_text("✅ رسید تأیید شد و فایل برای کاربر ارسال شد.")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(user_id, "❌ پرداخت شما تأیید نشد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.")
    await callback.answer("❌ رد شد.")
    await callback.message.edit_text("❌ رسید رد شد و به کاربر اطلاع داده شد.")

# ===== انتقادات و پیشنهادات =====
feedback_waiting_users = set()

@dp.message(F.text == "🗣️ انتقادات و پیشنهادات")
async def feedback_start(message: Message):
    feedback_waiting_users.add(message.chat.id)
    await message.answer("✍️ لطفاً نظر یا پیشنهاد خود را بنویسید:")

@dp.message(F.text & (lambda msg: msg.chat.id in feedback_waiting_users))
async def feedback_receive(message: Message):
    feedback_waiting_users.remove(message.chat.id)
    admin_text = f"📩 پیام جدید از @{message.from_user.username or '---'}:\n\n{message.text}"
    await bot.send_message(ADMIN_ID, admin_text)
    await message.answer("✅ پیام شما برای ادمین ارسال شد. ممنون از همراهی شما.")

# ===== درباره نویسنده =====
@dp.message(F.text == "✍️ درباره نویسنده")
async def about_author(message: Message):
    await message.answer(
        "👤 <b>درباره نویسنده:</b>\n\n"
        "نویسنده‌ی کتاب «هوژین حرمان» با قلمی صمیمی، زندگی، عشق و رنج را در قالب داستانی عمیق به تصویر می‌کشد.\n"
        f"📌 کانال رسمی: @{CHANNEL_USERNAME}"
    )

# ===== درباره کتاب =====
@dp.message(F.text == "ℹ️ درباره کتاب")
async def about_book(message: Message):
    await message.answer(
        "📖 <b>درباره کتاب:</b>\n\n"
        "«هوژین حرمان» داستانی است از دل تاریکی، از میان رنج‌ها و امیدها. "
        "این کتاب به زبان دل نوشته شده است و سفری درونی را روایت می‌کند.\n\n"
        "📥 لینک فایل PDF:\n"
        f"https://hozhin.onrender.com/books/hozhin_harman.pdf"
    )

# ===== کتاب صوتی =====
@dp.message(F.text == "🔊 کتاب صوتی (بزودی)")
async def audio_book_soon(message: Message):
    await message.answer("🔊 نسخه صوتی کتاب «هوژین حرمان» به‌زودی در همین ربات منتشر خواهد شد. 🎧")

# ===== اجرای Webhook =====
@app.route("/", methods=["POST"])
async def webhook():
    return await WebhookRequestHandler(dp).handle(request)

@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است."

async def main():
    await bot.set_webhook(WEBHOOK_URL)
    print("📡 Webhook set!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    config = Config()
    config.bind = ["0.0.0.0:10000"]
    loop.run_until_complete(serve(app, config))
