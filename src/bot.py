import os
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters

from telegram.constants import ParseMode
from telegram.error import BadRequest

from crypto import get_data, get_prices
from chart import get_chart
from database import Favorites

MENU_KEYBOARD = [
    [InlineKeyboardButton("💰 Price", callback_data="price#0-11"),
     InlineKeyboardButton("📈 Chart", callback_data="chart#0-11"),
     InlineKeyboardButton("📝 Review", callback_data="review"),
     InlineKeyboardButton("🔔 Notify", callback_data="alarm")],
    [InlineKeyboardButton("⭐ Favorites", callback_data="favorites"),
     InlineKeyboardButton("🔍 Search", callback_data="search"),
     InlineKeyboardButton("ℹ Info", callback_data="info")]
]


async def reply_update(update: Update, text: str, keyboard: list):
    await update.message.reply_text(text=text,
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=InlineKeyboardMarkup(keyboard))


async def reply_query(query, text: str, keyboard: list):
    await query.answer()
    await delete_query(query)
    await query.message.reply_text(text=text,
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=InlineKeyboardMarkup(keyboard))


async def reply_alarm(context: ContextTypes.DEFAULT_TYPE, text: str, keyboard: list):
    await context.bot.reply_text(text=text,
                                 parse_mode=ParseMode.HTML,
                                 reply_markup=InlineKeyboardMarkup(keyboard))


async def reply_photo(query, path: str, caption: str, keyboard: list):
    await query.answer()
    await delete_query(query)
    await query.message.reply_photo(photo=open(path, "rb"),
                                    caption=caption,
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=InlineKeyboardMarkup(keyboard))


async def delete_query(query):
    try:
        await query.delete_message()
    except BadRequest:
        pass


async def reply_select_cryptocurrency(query, data: list):
    option = query.data.split('#')[0]
    start, end = query.data.split('#')[-1].split("-")

    keyboard = get_keyboard(data[int(start):int(end)], option)

    if len(data) <= int(end) and not int(start):
        keyboard.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    elif len(data) <= int(end):
        keyboard.append(
            [InlineKeyboardButton("◀ Back", callback_data=f"{option}#{int(start) - 11}-{int(start)}"),
             InlineKeyboardButton("🔍 Search", callback_data="search"),
             InlineKeyboardButton("🏠 Home", callback_data="home")]
        )
    elif int(start) > 0:
        keyboard.append(
            [InlineKeyboardButton("◀ Back", callback_data=f"{option}#{int(start) - 11}-{int(start)}"),
             InlineKeyboardButton("🔍 Search", callback_data="search"),
             InlineKeyboardButton("🏠 Home", callback_data="home"),
             InlineKeyboardButton("▶ Next", callback_data=f"{option}#{int(end)}-{int(end) + 11}")]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton("🔍 Search", callback_data="search"),
             InlineKeyboardButton("🏠 Home", callback_data="home"),
             InlineKeyboardButton("▶ Next", callback_data=f"{option}#{int(end)}-{int(end) + 11}")])

    await reply_query(
        query=query, text="Select cryptocurrency 💬", keyboard=keyboard
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_update(update=update,
                       text="Welcome to <b>Cryptifica</b> 👋🏻\n<i>Your personal cryptocurrency checker bot</i> "
                            "🤖💰\n\nSelect option 💬",
                       keyboard=MENU_KEYBOARD)


async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_query(
        query=update.callback_query,
        text="Select option 💬",
        keyboard=MENU_KEYBOARD,
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    context.user_data["command"] = query.data
    if query.data.split("#")[0] in ["price", "chart", "favorites-add"]:
        await select_cryptocurrency(update, context)
    elif query.data.split("_")[0] == "price":
        await price(update, context)
    elif query.data.split("_")[0] == "chart":
        await chart(update, context)
    elif query.data == "favorites":
        await favorites(update, context)
    elif query.data.split("_")[0] == "favorites-add":
        await favorites_add(update, context)
    elif query.data.split("#")[0] == "favorites-remove":
        await select_favorites_remove(update, context)
    elif query.data.split("_")[0] == "favorites-remove":
        await favorites_remove(update, context)
    elif query.data == "review":
        await review(update, context)
    elif query.data == "alarm":
        await alarm(update, context)
    elif query.data == "alarm-on":
        await alarm_time(update, context)
    elif query.data.split("_")[0] == "alarm-on":
        await alarm_on(update, context)
    elif query.data == "alarm-off":
        await alarm_off(update, context)
    elif query.data == "home":
        await home(update, context)
    elif query.data == "search":
        await search_ask(update, context)
    elif query.data == "info":
        await info(update, context)


async def select_cryptocurrency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_select_cryptocurrency(update.callback_query, [cryptocurrency['id'] for cryptocurrency in get_data()])


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    data = get_data(query.data.split("_")[-1])
    name, symbol = data['name'], data['symbol']
    price, percent = data['priceUsd'], '{0:.{1}f}'.format(float(data['changePercent24Hr']), 4)

    keyboard = [[InlineKeyboardButton("◀ Back", callback_data="price#0-11"),
                 InlineKeyboardButton("🏠 Home", callback_data="home")]]

    await reply_query(query=query,
                      text=f"<b>{name} ({symbol})</b> 💰\n\nPrice of <b>{symbol}</b> is <b>${price}</b> (changed on "
                           f"<b>{percent}%</b> in 24 hrs) 💸{'📉' if percent[0] == '-' else '📈'}\n",
                      keyboard=keyboard)


async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    create_images_folder()

    data = get_data(query.data.split("_")[-1])
    datas, prices = get_prices(query.data.split("_")[-1])

    chart = get_chart(datas, prices)

    name, symbol = data['name'], data['symbol']

    keyboard = [
        [InlineKeyboardButton("◀ Back", callback_data="chart#0-11"),
         InlineKeyboardButton("🏠 Home", callback_data="home")],
    ]

    await reply_photo(query=query, path=f"images/{chart}.webp",
                      caption=f"<b>{name} ({symbol})</b> {'📉' if prices[0] > prices[-1] else '📈'}",
                      keyboard=keyboard)
    delete_image(chart)


def create_images_folder():
    if not os.path.exists("images"):
        os.makedirs("images")


def delete_image(file_name: str):
    if os.path.isfile(f"images/{file_name}.webp"):
        os.remove(f"images/{file_name}.webp")


async def favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌟 Add", callback_data="favorites-add#0-11"),
         InlineKeyboardButton("🗑 Remove", callback_data="favorites-remove#0-11"),
         InlineKeyboardButton("🏠 Home", callback_data="home")],
    ]

    await reply_query(
        query=update.callback_query, text="Select option 💬", keyboard=keyboard
    )


async def favorites_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    data = get_data(query.data.split("_")[-1])
    favorites = Favorites.get(query.from_user.id).split(",")

    keyboard = [
        [
            InlineKeyboardButton("◀ Back", callback_data="favorites"),
            InlineKeyboardButton("🏠 Home", callback_data="home"),
        ]
    ]

    await query.answer()
    if query.data.split("_")[-1] not in favorites:
        Favorites.add(query.from_user.id, query.data.split("_")[-1])
        await reply_query(query=query, text=f"<b>{data['name']}</b> added to favorites 🌟", keyboard=keyboard)
    else:
        await reply_query(query=query, text=f"<b>{data['name']}</b> already in favorites ⭐", keyboard=keyboard)


def get_keyboard(cryptocurrencies, option):
    keyboard = []
    keyboard_layer = []

    data = get_data()

    for i in range(len(cryptocurrencies[:10])):
        keyboard_layer.append(InlineKeyboardButton(get_cryptocurrency_data_by_id(data, cryptocurrencies[i])['symbol'],
                                                   callback_data=f"{option}_{cryptocurrencies[i]}"))
        if i == 4:
            keyboard.append(keyboard_layer)
            keyboard_layer = []
    keyboard.append(keyboard_layer)

    return keyboard


async def select_favorites_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await reply_select_cryptocurrency(query, Favorites.get(query.from_user.id).split(",")[:-1])


async def favorites_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    data = get_data(query.data.split("_")[-1])

    Favorites.remove(query.from_user.id, query.data.split("_")[-1])

    keyboard = [
        [
            InlineKeyboardButton("◀ Back", callback_data="favorites"),
            InlineKeyboardButton("🏠 Home", callback_data="home"),
        ]
    ]

    await reply_query(query=query, text=f"<b>{data['name']}</b> removed from favorites 🗑", keyboard=keyboard)


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    keyboard = [
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ]

    favorites = Favorites.get(query.from_user.id).split(",")[:-1]
    review = get_favorite_review(get_data(),
                                 favorites) if favorites else ("You don't have any favorite cryptocurrencies yet. Add "
                                                               "to favorites to receive your personalized review 🧾")

    await reply_query(query=query,
                      text=f"Review 📝\n<i>Prices of favorite cryptocurrencies at the current hour 💸</i>\n\n"
                           f"<i>{review}</i>",
                      keyboard=keyboard)


def get_favorite_review(data, favorites):
    reviews = []
    for favorite in favorites:
        d = get_cryptocurrency_data_by_id(data, favorite)
        reviews.append(
            f" • {d['name']} ({d['symbol']}) — ${d['priceUsd']} ({'{0:.{1}f}'.format(float(d['changePercent24Hr']), 4)}%) "
            f"{'📉' if d['changePercent24Hr'][0] == '-' else '📈'}")
    return "\n".join(reviews)


def get_cryptocurrency_data_by_id(data, cryptocurrency):
    for d in data:
        if d['id'] == cryptocurrency:
            return d


def get_cryptocurrency_data_by_symbol(data, symbol):
    for d in data:
        if d['symbol'] == symbol:
            return d


async def alarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("▶ On", callback_data="alarm-on"),
         InlineKeyboardButton("⏹ Off", callback_data="alarm-off"),
         InlineKeyboardButton("🏠 Home", callback_data="home")],
    ]

    await reply_query(
        query=update.callback_query, text="Select option 💬", keyboard=keyboard
    )


async def alarm_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🕛 0:00", callback_data="alarm-on_0"),
         InlineKeyboardButton("🕗 8:00", callback_data="alarm-on_8"),
         InlineKeyboardButton("🕛 12:00", callback_data="alarm-on_12"),
         InlineKeyboardButton("🕗 20:00", callback_data="alarm-on_20")],
        [InlineKeyboardButton("◀ Back", callback_data="alarm"),
         InlineKeyboardButton("🏠 Home", callback_data="home")]
    ]

    await reply_query(
        query=update.callback_query, text="Select time ⏰", keyboard=keyboard
    )


async def alarm_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    keyboard = [
        [InlineKeyboardButton("◀ Back", callback_data="alarm"),
         InlineKeyboardButton("🏠 Home", callback_data="home")]
    ]

    await enable_alarm(update, context)
    await reply_query(query=update.callback_query,
                      text=f"Alarm is enabled on <i>{query.data.split('_')[-1]}:00</i> (UTC) ⏰", keyboard=keyboard)


async def enable_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.job_queue.run_daily(alarmed_review, time=datetime.time(hour=int(query.data.split('_')[-1])),
                                days=(0, 1, 2, 3, 4, 5, 6), name=str(query.message.chat_id),
                                chat_id=query.message.chat_id, data=str(query.from_user.id))


async def alarm_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("◀ Back", callback_data="alarm"),
         InlineKeyboardButton("🏠 Home", callback_data="home")]
    ]

    await disable_alarm(update, context)
    await reply_query(
        query=update.callback_query,
        text="Alarm is disabled ⏰",
        keyboard=keyboard,
    )


async def disable_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.job_queue.get_jobs_by_name(str(update.callback_query.message.chat_id))[0].schedule_removal()


async def alarmed_review(context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ]

    favorites = Favorites.get(int(context.job.data)).split(",")[:-1]
    review = get_favorite_review(get_data(),
                                 favorites) if favorites else ("You don't have any favorite cryptocurrencies yet. Add "
                                                               "to favorites to receive your personalized review 🧾")

    await reply_alarm(context=context,
                      text=f"Daily Review 📝⏰\n<i>Prices of favorite cryptocurrencies at the current hour "
                           f"💸</i>\n\n<i>{review}</i>",
                      keyboard=keyboard)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    keyboard = [
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ]

    await reply_query(query=query,
                      text=f"About <b>Cryptifica</b> ℹ\n\nHey, {query.from_user.first_name} 👋🏻\n<i>I'm your "
                           f"personal cryptocurrency checker bot, made with ❤ on 🐍 by @m3r1v3 🤖💰</i>\n\n"
                           f"What can I do?\n\n"
                           f"<i> 💰 Show the current cryptocurrency prices\n"
                           f" 📈 Show cryptocurrency price chart for the last 30 days\n"
                           f" 📝 Make review for your favorite cryptocurrencies\n ⭐ Save your cryptocurrencies to "
                           f"favorites\n"
                           f" 🔔 Make review for you in specified time\n"
                           f"...and other features that we will make in the future ✨</i>\n\n"
                           f"Check prices, make charts with me. With <b>Cryptifica</b> 🤖",
                      keyboard=keyboard)


async def search_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ]

    await reply_query(query=update.callback_query,
                      text="Send symbol of cryptocurrency (like $BTC or $ETH) to do someting with it 🔍",
                      keyboard=keyboard)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("command", "") != "search": return

    data = get_cryptocurrency_data_by_symbol(get_data(), update.message.text[1:])

    if data is not None:
        id, name, symbol = data['id'], data['name'], data['symbol']
        keyboard = [
            [InlineKeyboardButton("💰 Price", callback_data=f"price_{id}"),
             InlineKeyboardButton("📈 Chart", callback_data=f"chart_{id}"),
             InlineKeyboardButton("🌟 Add", callback_data=f"favorite-add_{id}") if id not in Favorites.get(
                 update.message.from_user.id).split(",")
             else InlineKeyboardButton("🗑 Remove", callback_data=f"favorites-remove_{id}")],
            [InlineKeyboardButton("🏠 Home", callback_data="home")]
        ]

        await reply_update(
            update=update,
            text=f"Select <b>{name} ({symbol})</b> option 💬",
            keyboard=keyboard)
    else:
        keyboard = [[InlineKeyboardButton("🏠 Home", callback_data="home")]]
        await reply_update(
            update=update,
            text=f"Sorry, I can't find <b>{update.message.text[1:]}</b> 🔍\nTry again",
            keyboard=keyboard,
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(os.environ.get("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.Regex('[$][A-Z]{1,}'), search))

    app.run_polling()
