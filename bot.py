from flask import Flask
import threading
import os
import time
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import uuid

# ---------- KEEP ALIVE ----------

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot running"

def run():
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()

# ---------- BOT CONFIG ----------

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# ---------- DATABASE ----------

conn = sqlite3.connect("shop.db",check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY)")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
order_id TEXT,
user_id INTEGER,
package TEXT,
uid TEXT,
number TEXT,
status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS prices(
package TEXT PRIMARY KEY,
price INTEGER
)
""")

conn.commit()

# ---------- DEFAULT PRICES ----------

default_prices={
"4l":750,
"6l":950,
"guild":1350,
"trial":180,
"lvl7":1150
}

for k,v in default_prices.items():
    cursor.execute("INSERT OR IGNORE INTO prices VALUES(?,?)",(k,v))

conn.commit()

# ---------- FUNCTIONS ----------

def get_price(key):
    cursor.execute("SELECT price FROM prices WHERE package=?",(key,))
    result=cursor.fetchone()
    return result[0]

packages={
"4l":"🟢 ৪ লাখ গ্লোরি",
"6l":"🟢 ৬ লাখ গ্লোরি",
"guild":"🔶 ফুল গিল্ড ম্যাক্স",
"trial":"⚡ ট্রায়াল প্যাকেজ",
"lvl7":"⚡ ৭ লেভেল ম্যাক্স গিল্ড"
}

user_step={}
order_data={}

# ---------- START ----------

@bot.message_handler(commands=['start'])
def start(message):

    cursor.execute("INSERT OR IGNORE INTO users VALUES(?)",(message.from_user.id,))
    conn.commit()

    kb=ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🛒 Shop Items","📦 My Orders")
    kb.add("📞 Customer Support","📜 Order Rules")
    kb.add("ℹ️ About Shop","🔄 Restart Bot")

    bot.send_message(
        message.chat.id,
        "👑 Welcome to ALPHAN GAMING SHOP\n\nGlory Bot Sale",
        reply_markup=kb
    )

# ---------- RESTART ----------

@bot.message_handler(func=lambda m:m.text=="🔄 Restart Bot")
def restart(message):

    user_step.pop(message.from_user.id,None)
    order_data.pop(message.from_user.id,None)

    bot.send_message(message.chat.id,"🔄 Bot Restarted")

    start(message)

# ---------- CUSTOMER SUPPORT ----------

@bot.message_handler(func=lambda m:m.text=="📞 Customer Support")
def support(message):

    bot.send_message(
        message.chat.id,
        "📞 Customer Support\n\nWhatsApp: 01607254046"
    )

# ---------- ORDER RULES ----------

@bot.message_handler(func=lambda m:m.text=="📜 Order Rules")
def rules(message):

    bot.send_message(
        message.chat.id,
"""📜 ORDER RULES

• Guild auto approval on রাখবেন
• সঠিক Clan UID দিবেন
• Original payment screenshot দিবেন
• Payment send money করবেন

Thank you for choosing ALPHAN GAMING SHOP"""
    )

# ---------- ABOUT SHOP ----------

@bot.message_handler(func=lambda m:m.text=="ℹ️ About Shop")
def about(message):

    bot.send_message(
        message.chat.id,
"""ℹ️ ABOUT SHOP

ALPHAN GAMING SHOP

Glory Bot Sale
Trusted Gaming Service"""
    )

# ---------- MY ORDERS ----------

@bot.message_handler(func=lambda m:m.text=="📦 My Orders")
def my_orders(message):

    cursor.execute(
        "SELECT order_id,package,status FROM orders WHERE user_id=?",
        (message.from_user.id,)
    )

    orders=cursor.fetchall()

    if not orders:
        bot.send_message(message.chat.id,"❌ No orders found")
        return

    text="📦 YOUR ORDERS\n\n"

    for o in orders:

        status="⏳ Pending"

        if o[2]=="approved":
            status="✅ Approved"

        if o[2]=="rejected":
            status="❌ Rejected"

        text+=f"Order ID: {o[0]}\nPackage: {o[1]}\nStatus: {status}\n\n"

    bot.send_message(message.chat.id,text)

# ---------- ADMIN PANEL ----------

@bot.message_handler(commands=['admin'])
def admin_panel(message):

    if message.from_user.id!=ADMIN_ID:
        return

    kb=ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📢 Send Notice","💰 Edit Price")

    bot.send_message(message.chat.id,"🔧 ADMIN PANEL",reply_markup=kb)

# ---------- NOTICE ----------

@bot.message_handler(func=lambda m:m.text=="📢 Send Notice")
def ask_notice(message):

    if message.from_user.id!=ADMIN_ID:
        return

    user_step[message.from_user.id]="notice"

    bot.send_message(message.chat.id,"Write notice message")

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="notice")
def send_notice(message):

    styled=f"""⚠️ IMPORTANT NOTICE

━━━━━━━━━━━━━━

{message.text}

━━━━━━━━━━━━━━

— ALPHAN GAMING SHOP"""

    cursor.execute("SELECT user_id FROM users")
    users=cursor.fetchall()

    for u in users:
        try:
            bot.send_message(u[0],styled)
        except:
            pass

    bot.send_message(message.chat.id,"✅ Notice Sent")

    user_step[message.from_user.id]=None

# ---------- EDIT PRICE ----------

@bot.message_handler(func=lambda m:m.text=="💰 Edit Price")
def edit_price(message):

    if message.from_user.id!=ADMIN_ID:
        return

    kb=ReplyKeyboardMarkup(resize_keyboard=True)

    for v in packages.values():
        kb.add(v)

    user_step[message.from_user.id]="select_price"

    bot.send_message(message.chat.id,"Select package",reply_markup=kb)

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="select_price")
def select_price(message):

    for k,v in packages.items():
        if message.text==v:

            order_data[message.from_user.id]=k
            user_step[message.from_user.id]="new_price"

            bot.send_message(message.chat.id,"Send new price")
            return

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="new_price")
def new_price(message):

    key=order_data.get(message.from_user.id)

    try:
        cursor.execute(
        "UPDATE prices SET price=? WHERE package=?",
        (int(message.text),key)
        )
        conn.commit()

    except:
        bot.send_message(message.chat.id,"Send valid number")
        return

    bot.send_message(message.chat.id,f"✅ Price Updated\n\n{packages[key]} → {message.text} Tk")

    user_step[message.from_user.id]=None

# ---------- RUN BOT ----------

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
    except Exception as e:
        print(e)
        time.sleep(5)
