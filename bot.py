from flask import Flask
import threading
import os
import time
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import uuid

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

# ---------------- DEFAULT PRICES ----------------

default_prices={
"p1":750,
"p2":950,
"p3":1350,
"p4":180,
"p5":1150
}

for k,v in default_prices.items():
    cursor.execute("INSERT OR IGNORE INTO prices VALUES(?,?)",(k,v))

conn.commit()

def get_price(p):
    cursor.execute("SELECT price FROM prices WHERE package=?",(p,))
    return cursor.fetchone()[0]

packages={
"p1":"🟢 ৮ লাখ গ্লোরি",
"p2":"🟢 ৬ লাখ গ্লোরি",
"p3":"🔶 ফুল গিল্ড ম্যাক্স",
"p4":"⚡ ট্রায়াল প্যাকেজ",
"p5":"⚡ ৭ লেভেল ম্যাক্স গিল্ড"
}

user_step={}
order_data={}

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(m):

    cursor.execute("INSERT OR IGNORE INTO users VALUES(?)",(m.from_user.id,))
    conn.commit()

    kb=ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("👑 Price List")
    kb.add("🛒 Shop Items","📦 My Orders")
    kb.add("📞 Customer Support","📜 Order Rules")
    kb.add("ℹ️ About Shop","🔄 Restart Bot")

    bot.send_message(
        m.chat.id,
        "👑 Welcome to ALPHAN GAMING SHOP\n\nGlory Bot Sale",
        reply_markup=kb
    )

# ---------------- PRICE LIST ----------------

@bot.message_handler(func=lambda m:m.text=="👑 Price List")
def price_list(m):

    text=f"""
👑 ALPHAN SPECIAL OFFERS 👑

🟢 ৮ লাখ গ্লোরি – ৳{get_price('p1')}
🟢 ৬ লাখ গ্লোরি – ৳{get_price('p2')}
🔶 ফুল গিল্ড ম্যাক্স – ৳{get_price('p3')}
⚡ ট্রায়াল প্যাকেজ – ৳{get_price('p4')}
⚡ ৭ লেভেল ম্যাক্স গিল্ড – ৳{get_price('p5')}
"""

    bot.send_message(m.chat.id,text)

# ---------------- SHOP ITEMS ----------------

@bot.message_handler(func=lambda m:m.text=="🛒 Shop Items")
def shop(m):

    kb=InlineKeyboardMarkup()

    for k,v in packages.items():
        kb.add(InlineKeyboardButton(v,callback_data=k))

    bot.send_message(m.chat.id,"Package select করুন",reply_markup=kb)

# ---------------- PACKAGE SELECT ----------------

@bot.callback_query_handler(func=lambda c:c.data in packages)
def package_select(c):

    order_data[c.from_user.id]={"package":packages[c.data]}
    user_step[c.from_user.id]="uid"

    bot.send_message(c.message.chat.id,"Send Clan UID")

# ---------------- UID ----------------

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="uid")
def uid(m):

    order_data[m.from_user.id]["uid"]=m.text
    user_step[m.from_user.id]="number"

    bot.send_message(m.chat.id,"Send WhatsApp Number")

# ---------------- NUMBER ----------------

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="number")
def number(m):

    order_data[m.from_user.id]["number"]=m.text
    user_step[m.from_user.id]="ss"

    bot.send_message(
        m.chat.id,
        "💳 Payment Number\n\n01861316505\n\nSend Money Only\nThen send screenshot"
    )

# ---------------- SCREENSHOT ----------------

@bot.message_handler(content_types=['photo'])
def screenshot(m):

    if user_step.get(m.from_user.id)!="ss":
        return

    d=order_data[m.from_user.id]

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
    f"""NEW ORDER

ID: {oid}

Package: {d['package']}
UID: {d['uid']}
WA: {d['number']}""",
    reply_markup=kb
    )

    bot.send_message(m.chat.id,"✅ Order Submitted\n\nPlease wait for admin approval")

    user_step.pop(m.from_user.id,None)
    order_data.pop(m.from_user.id,None)

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
    (m.from_user.id,)
    )

    rows=cursor.fetchall()

    if not rows:
        bot.send_message(m.chat.id,"❌ No orders found")
        return

    text="📦 YOUR ORDERS\n\n"

    for r in rows:
        text+=f"{r[0]} | {r[1]} | {r[2]}\n"

    bot.send_message(m.chat.id,text)

# ---------------- SUPPORT ----------------

@bot.message_handler(func=lambda m:m.text=="📞 Customer Support")
def support(m):

    bot.send_message(m.chat.id,"WhatsApp: 01607254046")

# ---------------- RULES ----------------

@bot.message_handler(func=lambda m:m.text=="📜 Order Rules")
def rules(m):

    bot.send_message(
        m.chat.id,
        "Guild auto approval on রাখবেন\nসঠিক UID দিবেন\nOriginal payment screenshot দিবেন"
    )

# ---------------- ABOUT ----------------

@bot.message_handler(func=lambda m:m.text=="ℹ️ About Shop")
def about(m):

    bot.send_message(
        m.chat.id,
        "ALPHAN GAMING SHOP\nGlory Bot Sale"
    )

# ---------------- RESTART ----------------

@bot.message_handler(func=lambda m:m.text=="🔄 Restart Bot")
def restart(m):

    user_step.pop(m.from_user.id,None)
    order_data.pop(m.from_user.id,None)

    bot.send_message(m.chat.id,"🔄 Bot Restarted")

    start(m)

# ---------------- RUN BOT ----------------

while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except:
        time.sleep(5)
