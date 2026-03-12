from flask import Flask
import threading
import os
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import uuid
import time

# ---------------- KEEP ALIVE ----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running"

def run():
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)

threading.Thread(target=run).start()

# ---------------- BOT ----------------

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# ---------------- DATABASE ----------------

conn = sqlite3.connect("shop.db",check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
cursor.execute("""CREATE TABLE IF NOT EXISTS orders(
order_id TEXT,
user_id INTEGER,
package TEXT,
uid TEXT,
number TEXT,
status TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS prices(
package TEXT PRIMARY KEY,
price INTEGER
)""")

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

def get_price(key):
    cursor.execute("SELECT price FROM prices WHERE package=?",(key,))
    return cursor.fetchone()[0]

packages={
"4l":"🟢 ৪ লাখ গ্লোরি",
"6l":"🟢 ৬ লাখ গ্লোরি",
"guild":"🔶 ফুল গিল্ড ম্যাক্স",
"trial":"⚡ ট্রায়াল প্যাকেজ",
"lvl7":"⚡ ৭ লেভেল ম্যাক্স গিল্ড"
}

step={}
data={}

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(m):

    cursor.execute("INSERT OR IGNORE INTO users VALUES(?)",(m.from_user.id,))
    conn.commit()

    kb=ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Shop Items","📦 My Orders")
    kb.add("📞 Customer Support","🔄 Restart Bot")

    bot.send_message(m.chat.id,
    "👑 Welcome to ALPHAN GAMING SHOP\n\nGlory Bot Sale",
    reply_markup=kb)

# ---------------- SHOP ITEMS ----------------

@bot.message_handler(func=lambda m:m.text=="🛒 Shop Items")
def shop(m):

    text=f"""
👑 ALPHAN SPECIAL OFFERS 👑

🟢 ৪ লাখ গ্লোরি – ৳{get_price('4l')}
🟢 ৬ লাখ গ্লোরি – ৳{get_price('6l')}
🔶 ফুল গিল্ড ম্যাক্স – ৳{get_price('guild')}
⚡ ট্রায়াল প্যাকেজ – ৳{get_price('trial')}
⚡ ৭ লেভেল ম্যাক্স গিল্ড – ৳{get_price('lvl7')}
"""

    kb=InlineKeyboardMarkup()

    for k,v in packages.items():
        kb.add(InlineKeyboardButton(v,callback_data=k))

    bot.send_message(m.chat.id,text,reply_markup=kb)

# ---------------- PACKAGE SELECT ----------------

@bot.callback_query_handler(func=lambda c:c.data in packages)
def package(c):

    data[c.from_user.id]={"package":packages[c.data]}
    step[c.from_user.id]="uid"

    bot.send_message(c.message.chat.id,"Send Clan UID")

# ---------------- UID ----------------

@bot.message_handler(func=lambda m:step.get(m.from_user.id)=="uid")
def uid(m):

    data[m.from_user.id]["uid"]=m.text
    step[m.from_user.id]="number"

    bot.send_message(m.chat.id,"Send WhatsApp Number")

# ---------------- NUMBER ----------------

@bot.message_handler(func=lambda m:step.get(m.from_user.id)=="number")
def number(m):

    data[m.from_user.id]["number"]=m.text
    step[m.from_user.id]="ss"

    bot.send_message(m.chat.id,
"""💳 Payment Number

01861316505

Send Money Only
Then send screenshot""")

# ---------------- SCREENSHOT ----------------

@bot.message_handler(content_types=['photo'])
def screenshot(m):

    if step.get(m.from_user.id)!="ss":
        return

    d=data[m.from_user.id]

    oid=str(uuid.uuid4())[:8]

    cursor.execute(
    "INSERT INTO orders VALUES(?,?,?,?,?,?)",
    (oid,m.from_user.id,d["package"],d["uid"],d["number"],"pending")
    )
    conn.commit()

    kb=InlineKeyboardMarkup()
    kb.add(
    InlineKeyboardButton("✅ Approve",callback_data="a_"+oid),
    InlineKeyboardButton("❌ Reject",callback_data="r_"+oid)
    )

    bot.send_photo(
    ADMIN_ID,
    m.photo[-1].file_id,
    f"NEW ORDER\n\nID: {oid}\n{d['package']}\nUID: {d['uid']}\nWA: {d['number']}",
    reply_markup=kb)

    bot.send_message(m.chat.id,"✅ Order Submitted")

    step.pop(m.from_user.id)
    data.pop(m.from_user.id)

# ---------------- APPROVE ----------------

@bot.callback_query_handler(func=lambda c:c.data.startswith("a_"))
def approve(c):

    oid=c.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='approved' WHERE order_id=?",(oid,))
    conn.commit()

    bot.edit_message_caption(
    f"Order {oid}\n\n✅ APPROVED",
    c.message.chat.id,
    c.message.message_id)

# ---------------- REJECT ----------------

@bot.callback_query_handler(func=lambda c:c.data.startswith("r_"))
def reject(c):

    oid=c.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='rejected' WHERE order_id=?",(oid,))
    conn.commit()

    bot.edit_message_caption(
    f"Order {oid}\n\n❌ REJECTED",
    c.message.chat.id,
    c.message.message_id)

# ---------------- MY ORDERS ----------------

@bot.message_handler(func=lambda m:m.text=="📦 My Orders")
def my_orders(m):

    cursor.execute(
    "SELECT order_id,package,status FROM orders WHERE user_id=?",
    (m.from_user.id,))
    rows=cursor.fetchall()

    if not rows:
        bot.send_message(m.chat.id,"No orders")
        return

    text="📦 Your Orders\n\n"

    for r in rows:
        text+=f"{r[0]} | {r[1]} | {r[2]}\n"

    bot.send_message(m.chat.id,text)

# ---------------- SUPPORT ----------------

@bot.message_handler(func=lambda m:m.text=="📞 Customer Support")
def support(m):

    bot.send_message(m.chat.id,"WhatsApp: 01607254046")

# ---------------- RESTART ----------------

@bot.message_handler(func=lambda m:m.text=="🔄 Restart Bot")
def restart(m):

    step.pop(m.from_user.id,None)
    data.pop(m.from_user.id,None)

    bot.send_message(m.chat.id,"Bot Restarted")
    start(m)

# ---------------- RUN BOT ----------------

while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except:
        time.sleep(5)
