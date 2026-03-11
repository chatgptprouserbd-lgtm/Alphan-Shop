from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

keep_alive()
import telebot
import uuid
import sqlite3

from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("orders.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
order_id TEXT,
user_id INTEGER,
package TEXT,
uid TEXT,
whatsapp TEXT,
status TEXT
)
""")

conn.commit()

user_step = {}

# MAIN MENU
def main_menu():

    menu = ReplyKeyboardMarkup(resize_keyboard=True)

    menu.add("🛒 Shop Items", "📦 My Orders")
    menu.add("📞 Customer Support", "📜 Order Rules")
    menu.add("ℹ️ About Shop", "🔄 Restart Bot")

    return menu


# START
@bot.message_handler(commands=['start'])
def start(message):

    text = """
👑 Welcome to ALPHAN GAMING SHOP

Glory Bot Sale

Select an option from the menu.
"""

    bot.send_message(message.chat.id, text, reply_markup=main_menu())


# RESTART
@bot.message_handler(func=lambda m: m.text == "🔄 Restart Bot")
def restart(message):

    start(message)


# ABOUT SHOP
@bot.message_handler(func=lambda m: m.text == "ℹ️ About Shop")
def about(message):

    text = """
👑 ALPHAN GAMING SHOP

🎮 Professional Glory Bot Service

• Glory Bot Packages
• Guild Boost Services
• Trial Packages

⚡ Fast Delivery
⚡ Trusted Service

📞 WhatsApp Support
01607254046
"""

    bot.send_message(message.chat.id, text)


# ORDER RULES
@bot.message_handler(func=lambda m: m.text == "📜 Order Rules")
def rules(message):

    text = """
📜 ORDER RULES

1️⃣ Guild অবশ্যই Auto Approval ON করে রাখবেন

2️⃣ অবশ্যই সঠিক Guild / Clan UID দিবেন

3️⃣ Payment করার পরে Original Screenshot দিবেন

4️⃣ Payment করার সময় Only Send Money ব্যবহার করবেন

⚠️ Fake screenshot দিলে order reject করা হবে
"""

    bot.send_message(message.chat.id, text)


# SUPPORT
@bot.message_handler(func=lambda m: m.text == "📞 Customer Support")
def support(message):

    bot.send_message(
        message.chat.id,
        "📞 WhatsApp Support\n01607254046"
    )


# SHOP
@bot.message_handler(func=lambda m: m.text == "🛒 Shop Items")
def shop(message):

    text = """
👑 ALPHAN SPECIAL OFFERS 👑

🟢 ৪ লাখ গ্লোরি – ৳750
🟢 ৬ লাখ গ্লোরি – ৳950
🔶 ফুল গিল্ড ম্যাক্স ৭ – ৳1350
⚡ ট্রায়াল প্যাকেজ – ৳180
⚡ ৭ লেভেল ম্যাক্স গিল্ড – ৳1150

━━━━━━━━━━━━━━
একটি প্যাকেজ সিলেক্ট করুন:
"""

    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton("৪ লাখ গ্লোরি", callback_data="pkg_4l"),
        InlineKeyboardButton("৬ লাখ গ্লোরি", callback_data="pkg_6l")
    )

    markup.add(
        InlineKeyboardButton("ফুল গিল্ড ম্যাক্স ৭", callback_data="pkg_guild7")
    )

    markup.add(
        InlineKeyboardButton("ট্রায়াল প্যাকেজ", callback_data="pkg_trial")
    )

    markup.add(
        InlineKeyboardButton("৭ লেভেল গিল্ড", callback_data="pkg_guildlvl7")
    )

    bot.send_message(message.chat.id, text, reply_markup=markup)


# PACKAGE SELECT
@bot.callback_query_handler(func=lambda call: call.data.startswith("pkg"))
def select_package(call):

    package = call.data.replace("pkg_", "")

    user_step[call.from_user.id] = {
        "package": package
    }

    bot.send_message(call.message.chat.id, "Send Clan UID")


# UID
@bot.message_handler(func=lambda m: m.from_user.id in user_step and "uid" not in user_step[m.from_user.id])
def get_uid(message):

    user_step[message.from_user.id]["uid"] = message.text

    bot.send_message(message.chat.id, "Send WhatsApp number")


# WHATSAPP
@bot.message_handler(func=lambda m: m.from_user.id in user_step and "whatsapp" not in user_step[m.from_user.id])
def get_whatsapp(message):

    user_step[message.from_user.id]["whatsapp"] = message.text

    payment_text = """
💳 PAYMENT METHOD

bKash: 01861316505
Nagad: 01861316505

⚠️ Only Send Money

Payment করার পরে screenshot পাঠান।
"""

    bot.send_message(message.chat.id, payment_text)


# PAYMENT SCREENSHOT
@bot.message_handler(content_types=['photo'])
def payment(message):

    uid = message.from_user.id

    if uid not in user_step:
        return

    data = user_step[uid]

    order_id = str(uuid.uuid4())[:8]

    cursor.execute(
        "INSERT INTO orders VALUES(?,?,?,?,?,?)",
        (
            order_id,
            uid,
            data["package"],
            data["uid"],
            data["whatsapp"],
            "pending"
        )
    )

    conn.commit()

    caption = f"""
🆕 NEW ORDER

Order ID: {order_id}

Package: {data['package']}
Clan UID: {data['uid']}
WhatsApp: {data['whatsapp']}
"""

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=caption
    )

    bot.send_message(
        message.chat.id,
        f"✅ Order submitted\nOrder ID: {order_id}"
    )

    del user_step[uid]


# MY ORDERS
@bot.message_handler(func=lambda m: m.text == "📦 My Orders")
def my_orders(message):

    cursor.execute(
        "SELECT order_id,status FROM orders WHERE user_id=?",
        (message.from_user.id,)
    )

    data = cursor.fetchall()

    if not data:

        bot.send_message(message.chat.id, "No orders found")

        return

    text = "📦 YOUR ORDERS\n\n"

    for o in data:

        text += f"{o[0]} - {o[1]}\n"

    bot.send_message(message.chat.id, text)


bot.infinity_polling(skip_pending=True
