import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Define states for conversation
BOOK_PURCHASE, FEEDBACK, BOOK_INFO, AUTHOR_INFO = range(4)

# Bot token
TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
CHANNEL_USERNAME = "@fromheartsoul"
ADMIN_ID = YOUR_ADMIN_ID  # Replace with your Telegram user ID (integer)

# Check if user is subscribed to the channel
def check_subscription(context, user_id):
    try:
        chat_member = context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except:
        return False

# Start command
def start(update, context):
    user_id = update.message.from_user.id
    if not check_subscription(context, user_id):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"Please join our channel {CHANNEL_USERNAME} to use this bot.",
            reply_markup=reply_markup
        )
        return
    keyboard = [
        [InlineKeyboardButton("خرید کتاب", callback_data='purchase')],
        [InlineKeyboardButton("انتقادات و پیشنهادات", callback_data='feedback')],
        [InlineKeyboardButton("درباره کتاب", callback_data='book_info')],
        [InlineKeyboardButton("درباره نویسنده", callback_data='author_info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Welcome! Please select an option:", reply_markup=reply_markup)

# Button handler
def button(update, context):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    if not check_subscription(context, user_id):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text(
            f"Please join our channel {CHANNEL_USERNAME} to use this bot.",
            reply_markup=reply_markup
        )
        return

    if query.data == 'purchase':
        query.message.reply_text("Please enter your book purchase details (e.g., book title, quantity):")
        return BOOK_PURCHASE
    elif query.data == 'feedback':
        query.message.reply_text("Please share your feedback or suggestions:")
        return FEEDBACK
    elif query.data == 'book_info':
        query.message.reply_text("Here is information about the book:\n[Insert book details here]")
        return BOOK_INFO
    elif query.data == 'author_info':
        query.message.reply_text("Here is information about the author:\n[Insert author details here]")
        return AUTHOR_INFO

# Handle book purchase
def purchase(update, context):
    user_id = update.message.from_user.id
    purchase_details = update.message.text
    context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"New book purchase request:\nUser ID: {user_id}\nDetails: {purchase_details}\n\nPlease review and approve."
    )
    update.message.reply_text("Your purchase request has been sent for approval. We'll notify you soon.")
    return ConversationHandler.END

# Handle feedback
def feedback(update, context):
    user_id = update.message.from_user.id
    feedback_text = update.message.text
    context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"New feedback received:\nUser ID: {user_id}\nFeedback: {feedback_text}"
    )
    update.message.reply_text("Thank you for your feedback! It has been forwarded to our team.")
    return ConversationHandler.END

# Handle book info (placeholder response)
def book_info(update, context):
    update.message.reply_text("Book info section. You can add more details here.")
    return ConversationHandler.END

# Handle author info (placeholder response)
def author_info(update, context):
    update.message.reply_text("Author info section. You can add more details here.")
    return ConversationHandler.END

# Cancel conversation
def cancel(update, context):
    update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      MessageHandler(Filters.regex('^(خرید کتاب|انتقادات و پیشنهادات|درباره کتاب|درباره نویسنده)$'), start),
                      CallbackQueryHandler(button)],
        states={
            BOOK_PURCHASE: [MessageHandler(Filters.text & ~Filters.command, purchase)],
            FEEDBACK: [MessageHandler(Filters.text & ~Filters.command, feedback)],
            BOOK_INFO: [MessageHandler(Filters.text & ~Filters.command, book_info)],
            AUTHOR_INFO: [MessageHandler(Filters.text & ~Filters.command, author_info)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
