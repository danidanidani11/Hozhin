import os
from flask import Flask, request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "fromheartsoul"

app = Flask(__name__)

users_payment = {}  # ذخیره وضعیت پرداخت کاربران
user_waiting_for_receipt = set()

# ... (بقیه متغیرها و توابع مانند قبل بدون تغییر)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    admin_id = update.effective_user.id
    await query.answer()

    if admin_id != ADMIN_ID:
        await query.edit_message_text("شما اجازه انجام این کار را ندارید.")
        return

    if data.startswith(("approve_", "reject_")):
        action, user_id = data.split("_")
        user_id = int(user_id)
        
        if user_id not in users_payment:
            await query.edit_message_text("کاربر یافت نشد یا فیش قبلا بررسی شده.")
            return

        if action == "approve":
            users_payment[user_id]["status"] = "approved"
            await query.edit_message_text(f"✅ پرداخت کاربر {user_id} تایید شد.")

            pdf_path = "books/hozhin_harman.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=InputFile(f, filename="hozhin_harman.pdf"),
                        caption="کتاب هوژین حرمان"
                    )
                await context.bot.send_message(
                    chat_id=user_id,
                    text="پرداخت شما تایید شد. کتاب برای شما ارسال گردید. از خریدتان متشکریم! ❤️"
                )
            else:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text="فایل کتاب در سرور موجود نیست!"
                )
        else:
            users_payment[user_id]["status"] = "rejected"
            await query.edit_message_text(f"❌ پرداخت کاربر {user_id} رد شد.")
            await context.bot.send_message(
                chat_id=user_id,
                text="پرداخت شما تایید نشد. لطفا دوباره فیش را ارسال کنید یا با پشتیبانی تماس بگیرید."
            )

def run_app():
    application = ApplicationBuilder().token(TOKEN).build()
    app.application = application
    app.bot = application.bot

    # تغییر اصلی اینجا است - حذف pattern از CallbackQueryHandler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), message_handler))
    application.add_handler(CallbackQueryHandler(admin_callback_handler))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    application.run_polling()

if __name__ == "__main__":
    run_app()
