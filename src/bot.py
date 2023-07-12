import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("💲", callback_data="value"), InlineKeyboardButton("🔔", callback_data="alarm"), InlineKeyboardButton("⭐", callback_data="favorites")],
        [InlineKeyboardButton("📈", callback_data="chart"), InlineKeyboardButton("📝", callback_data="review"), InlineKeyboardButton("ℹ", callback_data="info")],
    ]
    
    await update.message.reply_text(
        f'Welcome to Cryptifica 👋🏻\n\nYour personal cryptocurrency checker bot 🤖💰\n\nSelect option 💬\n\n💲 Show current price\n🔔 Notify about the cost⭐ Favorite cryptocurrencies\n📈 Show price chart\n📝 Daily reviews\nℹ About Cryptifica',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query.data == "value": await value_option(query)
    elif query.data == "alarm": await alarm_option(query)
    elif query.data == "chart": await chart_option(query)
    elif query.data == "review": await review_option(query)
    elif query.data == "home": await home(query)
    elif query.data == "info": await info(query)

async def value_option(query):
    keyboard = [
        [InlineKeyboardButton("🏠", callback_data="home")],
    ]
    await query.answer()
    await query.edit_message_text(text=f"💲 Current price", reply_markup=InlineKeyboardMarkup(keyboard))
    
async def alarm_option(query):
    keyboard = [
        [InlineKeyboardButton("🏠", callback_data="home")],
    ]
    await query.answer()
    await query.edit_message_text(text=f"🔔 Notify", reply_markup=InlineKeyboardMarkup(keyboard))

async def chart_option(query):
    keyboard = [
        [InlineKeyboardButton("🏠", callback_data="home")],
    ]
    await query.answer()
    await query.edit_message_text(text=f"📈 Price chart", reply_markup=InlineKeyboardMarkup(keyboard))

async def review_option(query):
    keyboard = [
        [InlineKeyboardButton("🏠", callback_data="home")],
    ]
    await query.answer()
    await query.edit_message_text(text=f"📝 Daily review", reply_markup=InlineKeyboardMarkup(keyboard))

async def home(query):
    keyboard = [
        [InlineKeyboardButton("💲", callback_data="value"), InlineKeyboardButton("🔔", callback_data="alarm"), InlineKeyboardButton("⭐", callback_data="favorites")],
        [InlineKeyboardButton("📈", callback_data="chart"), InlineKeyboardButton("📝", callback_data="review"), InlineKeyboardButton("ℹ", callback_data="info")],
    ]
    
    await query.answer()
    await query.edit_message_text(
        text=f'Welcome to Cryptifica 👋🏻\n\nYour personal cryptocurrency checker bot 🤖💰\n\nSelect option 💬\n\n💲 Show current price\n🔔 Notify about the cost\n📈 Show price chart\n📝 Daily reviews',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def info(query):
    keyboard = [
        [InlineKeyboardButton("🏠", callback_data="home")],
    ]
    await query.answer()
    await query.edit_message_text(text=f"ℹ About Cryptifica", reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.environ.get('BOT_TOKEN')).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    
    app.run_polling()