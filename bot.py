import telebot
import uuid

from telebot.types import ReplyKeyboardMarkup,KeyboardButton
from telebot.types import InlineKeyboardMarkup,InlineKeyboardButton

from config import TOKEN,ADMIN_ID
from database import *
from shop import shop_menu
from admin import admin_panel

bot = telebot.TeleBot(TOKEN)

user_steps={}


def main_menu():

    menu = ReplyKeyboardMarkup(resize_keyboard=True)

    menu.add(
        KeyboardButton("🛒 Shop Items"),
        KeyboardButton("💳 Payment Method")
    )

    menu.add(
        KeyboardButton("📞 Customer Support"),
        KeyboardButton("📦 My Orders")
    )

    menu.add(
        KeyboardButton("ℹ️ About Shop")
    )

    return menu


@bot.message_handler(commands=['start'])
def start(message):

    text="""
Hey! Welcome to ALPHAN GAMING SHOP

👑 ALPHAN SPECIAL OFFERS 👑
Glory Bot Sale
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m:m.text=="🛒 Shop Items")
def shop(message):

    bot.send_message(
        message.chat.id,
        "Shop Items",
        reply_markup=shop_menu()
    )


@bot.callback_query_handler(func=lambda call:call.data.startswith("order_"))
def order(call):

    item_id=call.data.split("_")[1]

    user_steps[call.from_user.id]={"item":item_id}

    bot.send_message(call.message.chat.id,"Send Clan UID")


@bot.message_handler(func=lambda m:m.from_user.id in user_steps and "uid" not in user_steps[m.from_user.id])
def uid(message):

    user_steps[message.from_user.id]["uid"]=message.text

    bot.send_message(message.chat.id,"Send WhatsApp number")


@bot.message_handler(func=lambda m:m.from_user.id in user_steps and "whatsapp" not in user_steps[m.from_user.id])
def whatsapp(message):

    user_steps[message.from_user.id]["whatsapp"]=message.text

    bot.send_message(message.chat.id,"Send coupon or SKIP")


@bot.message_handler(func=lambda m:m.from_user.id in user_steps and "coupon" not in user_steps[m.from_user.id])
def coupon(message):

    code=message.text

    if code=="SKIP":

        user_steps[message.from_user.id]["coupon"]=None

    else:

        c=get_coupon(code)

        if c:
            user_steps[message.from_user.id]["coupon"]=code
        else:
            bot.send_message(message.chat.id,"Invalid coupon")
            return

    bot.send_message(message.chat.id,"Send payment screenshot")


@bot.message_handler(content_types=['photo'])
def payment(message):

    uid=message.from_user.id

    if uid not in user_steps:
        return

    order_id=str(uuid.uuid4())[:8]

    data=user_steps[uid]

    order=(
        order_id,
        uid,
        data["uid"],
        data["whatsapp"],
        data["item"],
        data["coupon"],
        "pending"
    )

    add_order(order)

    caption=f"""
NEW ORDER

Order ID: {order_id}
Clan UID: {data['uid']}
Whatsapp: {data['whatsapp']}
Item: {data['item']}
Coupon: {data['coupon']}
"""

    markup=InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton("Approve",callback_data=f"approve_{order_id}"),
        InlineKeyboardButton("Reject",callback_data=f"reject_{order_id}")
    )

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=caption,
        reply_markup=markup
    )

    bot.send_message(message.chat.id,f"Order submitted\nID: {order_id}")

    del user_steps[uid]


@bot.message_handler(commands=['admin'])
def admin(message):

    if message.from_user.id!=ADMIN_ID:
        return

    bot.send_message(
        message.chat.id,
        "Admin Panel",
        reply_markup=admin_panel()
    )


bot.infinity_polling()
