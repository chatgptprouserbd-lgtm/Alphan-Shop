from flask import Flask
import threading
import os
import telebot
import sqlite3
import uuid
import time
from telebot.types import *

# ---------------- KEEP ALIVE ----------------

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot running"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run).start()

# ---------------- CONFIG ----------------

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# ---------------- DATABASE ----------------

conn = sqlite3.connect("shop.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS items(
name TEXT,
price TEXT
)
""")

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

# ---------------- MENU ----------------

def main_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🛒 Shop Items", "📦 My Orders")
    kb.add("📞 Customer Support", "📜 Order Rules")
    kb.add("ℹ️ About Shop", "🔄 Restart Bot")

    return kb

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        "👑 Welcome to ALPHAN GAMING SHOP\n\nGlory Bot Sale",
        reply_markup=main_menu()
    )

# ---------------- SHOP ----------------

@bot.message_handler(func=lambda m: m.text=="🛒 Shop Items")
def shop(message):

    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()

    if not items:

        bot.send_message(message.chat.id,"❌ No items available")
        return

    text="👑 ALPHAN SPECIAL OFFERS 👑\n\n"

    kb = InlineKeyboardMarkup()

    for item in items:

        name=item[0]
        price=item[1]

        text += f"⚡ {name} – ৳{price}\n"

        kb.add(InlineKeyboardButton(name,callback_data=name))

    bot.send_message(message.chat.id,text,reply_markup=kb)

# ---------------- PACKAGE SELECT ----------------

@bot.callback_query_handler(func=lambda c: True)
def package(c):

    user_step[c.from_user.id]={}
    user_step[c.from_user.id]["package"]=c.data

    bot.send_message(c.message.chat.id,"Send Clan UID")

# ---------------- UID ----------------

@bot.message_handler(func=lambda m: m.from_user.id in user_step and "uid" not in user_step[m.from_user.id])
def uid(message):

    user_step[message.from_user.id]["uid"]=message.text

    bot.send_message(message.chat.id,"Send WhatsApp number")

# ---------------- WHATSAPP ----------------

@bot.message_handler(func=lambda m: m.from_user.id in user_step and "whatsapp" not in user_step[m.from_user.id])
def whatsapp(message):

    user_step[message.from_user.id]["whatsapp"]=message.text

    bot.send_message(
        message.chat.id,
"""
💳 PAYMENT METHOD

bKash: 01861316505
Nagad: 01861316505

⚠️ Only Send Money

Send payment screenshot
"""
)

# ---------------- SCREENSHOT ----------------

@bot.message_handler(content_types=['photo'])
def screenshot(message):

    uid=message.from_user.id

    if uid not in user_step:
        return

    data=user_step[uid]

    order_id=str(uuid.uuid4())[:8]

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

    caption=f"""
🆕 NEW ORDER

Order ID: {order_id}

Package: {data['package']}
Clan UID: {data['uid']}
WhatsApp: {data['whatsapp']}
"""

    kb=InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("✅ Approve",callback_data=f"approve_{order_id}_{uid}"),
        InlineKeyboardButton("❌ Reject",callback_data=f"reject_{order_id}_{uid}")
    )

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=caption,
        reply_markup=kb
    )

    bot.send_message(
        message.chat.id,
"""
✅ Order Submitted Successfully

অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।
"""
)

    del user_step[uid]

# ---------------- ADMIN ACTION ----------------

@bot.callback_query_handler(func=lambda c: c.data.startswith(("approve","reject")))
def admin_action(c):

    data=c.data.split("_")

    action=data[0]
    order=data[1]
    user=int(data[2])

    if action=="approve":

        bot.send_message(user,"✅ Order Approved")

    else:

        bot.send_message(user,"❌ Order Rejected")

# ---------------- ADMIN PANEL ----------------

@bot.message_handler(commands=['admin'])
def admin(message):

    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("📦 View Orders")
    kb.add("➕ Add Item")
    kb.add("✏️ Edit Item")
    kb.add("❌ Delete Item")

    bot.send_message(message.chat.id,"🛠 ADMIN PANEL",reply_markup=kb)

# ---------------- VIEW ORDERS ----------------

@bot.message_handler(func=lambda m: m.text=="📦 View Orders")
def view_orders(message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()

    if not orders:

        bot.send_message(message.chat.id,"No orders")
        return

    for order in orders:

        text=f"""
Order ID: {order[0]}
Package: {order[2]}
UID: {order[3]}
WhatsApp: {order[4]}
Status: {order[5]}
"""

        bot.send_message(message.chat.id,text)

# ---------------- ADD ITEM ----------------

@bot.message_handler(func=lambda m: m.text=="➕ Add Item")
def add_item(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg=bot.send_message(message.chat.id,"Send item name,price")

    bot.register_next_step_handler(msg,save_item)

def save_item(message):

    name,price=message.text.split(",")

    cursor.execute("INSERT INTO items VALUES(?,?)",(name,price))

    conn.commit()

    bot.send_message(message.chat.id,"✅ Item added")

# ---------------- EDIT ITEM ----------------

@bot.message_handler(func=lambda m: m.text=="✏️ Edit Item")
def edit_item(message):

    msg=bot.send_message(message.chat.id,"Send item name,newprice")

    bot.register_next_step_handler(msg,update_item)

def update_item(message):

    name,price=message.text.split(",")

    cursor.execute(
        "UPDATE items SET price=? WHERE name=?",
        (price,name)
    )

    conn.commit()

    bot.send_message(message.chat.id,"✅ Item updated")

# ---------------- DELETE ITEM ----------------

@bot.message_handler(func=lambda m: m.text=="❌ Delete Item")
def delete_item(message):

    msg=bot.send_message(message.chat.id,"Send item name")

    bot.register_next_step_handler(msg,remove_item)

def remove_item(message):

    cursor.execute(
        "DELETE FROM items WHERE name=?",
        (message.text,)
    )

    conn.commit()

    bot.send_message(message.chat.id,"❌ Item deleted")

# ---------------- STABLE POLLING ----------------

while True:

    try:

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=30,
            skip_pending=True
        )

    except Exception as e:

        print(e)

        time.sleep(10)
