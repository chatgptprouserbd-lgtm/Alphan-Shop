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
    return "Bot is running"

def run():
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)

threading.Thread(target=run).start()

# ---------------- CONFIG ----------------

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# ---------------- DATABASE ----------------

conn = sqlite3.connect("shop.db",check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS items(name TEXT,price TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS orders(order_id TEXT,user_id INTEGER,package TEXT,uid TEXT,whatsapp TEXT,status TEXT)")

conn.commit()

user_data = {}

# ---------------- MENU ----------------

def main_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🛒 Shop Items","📦 My Orders")
    kb.add("📞 Customer Support","📜 Order Rules")
    kb.add("ℹ️ About Shop","🔄 Restart Bot")

    return kb

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(m):

    bot.send_message(
        m.chat.id,
        "👑 Welcome to ALPHAN GAMING SHOP\n\nGlory Bot Sale",
        reply_markup=main_menu()
    )

# ---------------- SHOP ----------------

@bot.message_handler(func=lambda m: m.text=="🛒 Shop Items")
def shop(m):

    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()

    if not items:
        bot.send_message(m.chat.id,"❌ No items available")
        return

    text="👑 ALPHAN SPECIAL OFFERS 👑\n\n"

    kb = InlineKeyboardMarkup()

    for i in items:

        name=i[0]
        price=i[1]

        text += f"⚡ {name} – ৳{price}\n"

        kb.add(InlineKeyboardButton(name,callback_data=name))

    bot.send_message(m.chat.id,text,reply_markup=kb)

# ---------------- PACKAGE SELECT ----------------

@bot.callback_query_handler(func=lambda c: not c.data.startswith(("approve","reject")))
def package(c):

    user_data[c.from_user.id]={}
    user_data[c.from_user.id]["package"]=c.data

    bot.send_message(c.message.chat.id,"Send Clan UID")

# ---------------- UID ----------------

@bot.message_handler(func=lambda m: m.from_user.id in user_data and "uid" not in user_data[m.from_user.id])
def uid(m):

    user_data[m.from_user.id]["uid"]=m.text

    bot.send_message(m.chat.id,"Send WhatsApp number")

# ---------------- WHATSAPP ----------------

@bot.message_handler(func=lambda m: m.from_user.id in user_data and "whatsapp" not in user_data[m.from_user.id])
def whatsapp(m):

    user_data[m.from_user.id]["whatsapp"]=m.text

    bot.send_message(
        m.chat.id,
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
def screenshot(m):

    uid=m.from_user.id

    if uid not in user_data:
        return

    data=user_data[uid]

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
        m.photo[-1].file_id,
        caption=caption,
        reply_markup=kb
    )

    bot.send_message(
        m.chat.id,
"""
✅ Order Submitted Successfully

অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।
"""
)

    del user_data[uid]

# ---------------- ADMIN APPROVE / REJECT ----------------

@bot.callback_query_handler(func=lambda c: c.data.startswith(("approve","reject")))
def admin_action(c):

    data=c.data.split("_")

    action=data[0]
    user=int(data[2])

    if action=="approve":

        bot.send_message(
            user,
            "✅ Order Approved\n\nআপনার অর্ডার গ্রহণ করা হয়েছে।"
        )

    else:

        bot.send_message(
            user,
            "❌ Order Rejected\n\nSupport এ যোগাযোগ করুন।"
        )

# ---------------- ADMIN PANEL ----------------

@bot.message_handler(commands=['admin'])
def admin_panel(m):

    if m.from_user.id != ADMIN_ID:
        return

    kb=ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("📦 View Orders")
    kb.add("➕ Add Item","✏️ Edit Item","❌ Delete Item")

    bot.send_message(m.chat.id,"🛠 ADMIN PANEL",reply_markup=kb)

# ---------------- VIEW ORDERS ----------------

@bot.message_handler(func=lambda m:m.text=="📦 View Orders")
def view_orders(m):

    if m.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT * FROM orders")
    orders=cursor.fetchall()

    if not orders:
        bot.send_message(m.chat.id,"No orders")
        return

    for o in orders:

        bot.send_message(
            m.chat.id,
f"""
Order ID: {o[0]}
Package: {o[2]}
UID: {o[3]}
WhatsApp: {o[4]}
Status: {o[5]}
"""
)

# ---------------- ADD ITEM ----------------

@bot.message_handler(func=lambda m:m.text=="➕ Add Item")
def add_item(m):

    msg=bot.send_message(m.chat.id,"Send item name,price")

    bot.register_next_step_handler(msg,save_item)

def save_item(m):

    name,price=m.text.split(",")

    cursor.execute("INSERT INTO items VALUES(?,?)",(name,price))

    conn.commit()

    bot.send_message(m.chat.id,"✅ Item added")

# ---------------- EDIT ITEM ----------------

@bot.message_handler(func=lambda m:m.text=="✏️ Edit Item")
def edit_item(m):

    msg=bot.send_message(m.chat.id,"Send item name,newprice")

    bot.register_next_step_handler(msg,update_item)

def update_item(m):

    name,price=m.text.split(",")

    cursor.execute("UPDATE items SET price=? WHERE name=?",(price,name))

    conn.commit()

    bot.send_message(m.chat.id,"✅ Item updated")

# ---------------- DELETE ITEM ----------------

@bot.message_handler(func=lambda m:m.text=="❌ Delete Item")
def delete_item(m):

    msg=bot.send_message(m.chat.id,"Send item name")

    bot.register_next_step_handler(msg,remove_item)

def remove_item(m):

    cursor.execute("DELETE FROM items WHERE name=?",(m.text,))

    conn.commit()

    bot.send_message(m.chat.id,"❌ Item deleted")

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
