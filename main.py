import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import os

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("سلام! به ربات خوش آمدید.")

# پیام‌های معمولی
@dp.message(F.content_type.in_({'text', 'photo', 'document'}))
async def handle_messages(message: Message):
    await message.answer("پیام شما دریافت شد.")

# راه‌اندازی سرور وب برای webhook
async def on_startup(app):
    webhook_url = "https://hozhin.onrender.com/webhook"
    await bot.set_webhook(webhook_url)

app = web.Application()
app.on_startup.append(on_startup)

SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")

if __name__ == "__main__":
    web.run_app(app, port=int(os.environ.get("PORT", 10000)))
