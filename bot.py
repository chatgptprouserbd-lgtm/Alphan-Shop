from flask import Flask
import threading
import os
import telebot
import sqlite3
import uuid
import time
from telebot.types import *

# ---------- KEEP ALIVE ----------

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot running"

def run():
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)

threading.Thread(target=run).start()

# ---------- CONFIG ----------

TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=int(os.getenv("ADMIN_ID"))

bot=telebot.TeleBot(TOKEN)

# ---------- DATABASE ----------

conn=sqlite3.connect("shop.db",check_same_thread=False)
cursor=conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS items(
name TEXT,
price TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
id TEXT,
user_id INTEGER,
package TEXT,
uid TEXT,
whatsapp TEXT,
status TEXT
)
""")

conn.commit()

user_data={}

# ---------- MAIN MENU ----------

def main_menu():

    kb=ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🛒 Shop Items","📦 My Orders")
    kb.add("📞 Customer Support","📜 Order Rules")
    kb.add("ℹ️ About Shop","🔄 Restart Bot")

    return kb

# ---------- START ----------

@bot.message_handler(commands=['start'])
def start(m):

    bot.send_message(
        m.chat.id,
        "👑 Welcome to ALPHAN GAMING SHOP\n\nGlory Bot Sale",
        reply_markup=main_menu()
    )

# ---------- RESTART ----------

@bot.message_handler(func=lambda m:m.text=="🔄 Restart Bot")
def restart(m):
    start(m)

# ---------- ABOUT ----------

@bot.message_handler(func=lambda m:m.text=="ℹ️ About Shop")
def about(m):

    bot.send_message(
        m.chat.id,
"""
👑 ALPHAN GAMING SHOP

🎮 Professional Glory Bot Service

⚡ Fast Delivery
⚡ Trusted Service
⚡ 24/7 Support

WhatsApp:
01607254046
"""
)

# ---------- RULES ----------

@bot.message_handler(func=lambda m:m.text=="📜 Order Rules")
def rules(m):

    bot.send_message(
        m.chat.id,
"""
📜 ORDER RULES

• Guild অবশ্যই Auto Approval ON রাখবেন
• অবশ্যই সঠিক Guild / Clan UID দিবেন
• Payment করার পরে Original Screenshot দিবেন
• Payment করার সময় Only Send Money ব্যবহার করবেন
"""
)

# ---------- SUPPORT ----------

@bot.message_handler(func=lambda m:m.text=="📞 Customer Support")
def support(m):

    bot.send_message(
        m.chat.id,
        "WhatsApp Support\n01607254046"
    )

# ---------- SHOP ----------

@bot.message_handler(func=lambda m:m.text=="🛒 Shop Items")
def shop(m):

    cursor.execute("SELECT * FROM items")
    items=cursor.fetchall()

    if not items:

        bot.send_message(m.chat.id,"❌ No items available")
        return

    text="👑 ALPHAN SPECIAL OFFERS 👑\n\n"

    kb=InlineKeyboardMarkup()

    for i in items:

        text+=f"{i[0]} – ৳{i[1]}\n"

        kb.add(
            InlineKeyboardButton(
                i[0],
                callback_data=f"buy_{i[0]}"
            )
        )

    bot.send_message(m.chat.id,text,reply_markup=kb)

# ---------- SELECT PACKAGE ----------

@bot.callback_query_handler(func=lambda c:c.data.startswith("buy_"))
def buy(c):

    package=c.data.replace("buy_","")

    user_data[c.from_user.id]={"package":package}

    bot.send_message(
        c.message.chat.id,
        "Send Clan UID"
    )

# ---------- UID ----------

@bot.message_handler(func=lambda m:m.from_user.id in user_data and "uid" not in user_data[m.from_user.id])
def uid(m):

    user_data[m.from_user.id]["uid"]=m.text

    bot.send_message(
        m.chat.id,
        "Send WhatsApp number"
    )

# ---------- WHATSAPP ----------

@bot.message_handler(func=lambda m:m.from_user.id in user_data and "whatsapp" not in user_data[m.from_user.id])
def whatsapp(m):

    user_data[m.from_user.id]["whatsapp"]=m.text

    bot.send_message(
        m.chat.id,
"""
💳 PAYMENT METHOD

bKash: 01861316505
Nagad: 01861316505

⚠️ Only Send Money

Payment করার পরে screenshot পাঠান।
"""
)

# ---------- SCREENSHOT ----------

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
        InlineKeyboardButton(
            "✅ Approve",
            callback_data=f"approve_{order_id}_{uid}"
        ),
        InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject_{order_id}_{uid}"
        )
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
Admin খুব শীঘ্রই আপনার অর্ডার যাচাই করবে।
"""
)

    del user_data[uid]

# ---------- ADMIN ACTION ----------

@bot.callback_query_handler(func=lambda c:c.data.startswith("approve_") or c.data.startswith("reject_"))
def admin_action(c):

    data=c.data.split("_")

    action=data[0]
    order=data[1]
    user=int(data[2])

    if action=="approve":

        bot.send_message(
            user,
            "✅ Order Approved\n\nআপনার অর্ডার গ্রহণ করা হয়েছে।"
        )

        bot.edit_message_caption(
            "✅ APPROVED",
            c.message.chat.id,
            c.message.message_id
        )

    else:

        bot.send_message(
            user,
            "❌ Order Rejected\n\nSupport এ যোগাযোগ করুন।"
        )

        bot.edit_message_caption(
            "❌ REJECTED",
            c.message.chat.id,
            c.message.message_id
        )

# ---------- ADMIN PANEL ----------

@bot.message_handler(commands=['admin'])
def admin_panel(m):

    if m.from_user.id!=ADMIN_ID:
        return

    kb=InlineKeyboardMarkup()

    kb.add(InlineKeyboardButton("📦 View Orders",callback_data="orders"))
    kb.add(InlineKeyboardButton("➕ Add Item",callback_data="add"))
    kb.add(InlineKeyboardButton("❌ Delete Item",callback_data="delete"))

    bot.send_message(
        m.chat.id,
        "🛠 ADMIN PANEL",
        reply_markup=kb
    )

# ---------- VIEW ORDERS ----------

@bot.callback_query_handler(func=lambda c:c.data=="orders")
def orders(c):

    cursor.execute("SELECT * FROM orders")
    data=cursor.fetchall()

    if not data:

        bot.send_message(c.message.chat.id,"❌ No orders")
        return

    text="📦 ORDER LIST\n\n"

    for o in data:

        text+=f"{o[0]} | {o[2]} | {o[5]}\n"

    bot.send_message(c.message.chat.id,text)

# ---------- ADD ITEM ----------

@bot.callback_query_handler(func=lambda c:c.data=="add")
def add(c):

    bot.send_message(
        c.message.chat.id,
        "Send item name and price\nExample:\n4L Glory,750"
    )

    bot.register_next_step_handler(
        c.message,
        save_item
    )

def save_item(m):

    name,price=m.text.split(",")

    cursor.execute(
        "INSERT INTO items VALUES(?,?)",
        (name,price)
    )

    conn.commit()

    bot.send_message(
        m.chat.id,
        "✅ Item Added"
    )

# ---------- DELETE ITEM ----------

@bot.callback_query_handler(func=lambda c:c.data=="delete")
def delete(c):

    bot.send_message(
        c.message.chat.id,
        "Send item name to delete"
    )

    bot.register_next_step_handler(
        c.message,
        remove_item
    )

def remove_item(m):

    cursor.execute(
        "DELETE FROM items WHERE name=?",
        (m.text,)
    )

    conn.commit()

    bot.send_message(
        m.chat.id,
        "❌ Item Deleted"
    )

# ---------- STABLE POLLING ----------

while True:

    try:

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=30,
            skip_pending=True
        )

    except Exception as e:

        print("Error:",e)

        time.sleep(10)
