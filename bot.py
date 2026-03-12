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

# ---------------- BOT CONFIG ----------------

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# ---------------- DATABASE ----------------

conn = sqlite3.connect("shop.db",check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY)")
cursor.execute("""CREATE TABLE IF NOT EXISTS orders(
order_id TEXT,
user_id INTEGER,
package TEXT,
uid TEXT,
number TEXT,
status TEXT
)""")

conn.commit()

user_step={}
order_data={}

# ---------------- PRICE LIST ----------------

prices={
"4l":750,
"6l":950,
"guild":1350,
"trial":180,
"lvl7":1150
}

packages={
"4l":"🟢 ৪ লাখ গ্লোরি",
"6l":"🟢 ৬ লাখ গ্লোরি",
"guild":"🔶 ফুল গিল্ড ম্যাক্স",
"trial":"⚡ ট্রায়াল প্যাকেজ",
"lvl7":"⚡ ৭ লেভেল ম্যাক্স গিল্ড"
}

# ---------------- START ----------------

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

# ---------------- ADMIN PANEL ----------------

@bot.message_handler(commands=['admin'])
def admin_panel(message):

    if message.from_user.id!=ADMIN_ID:
        return

    kb=ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📢 Send Notice","💰 Edit Price")

    bot.send_message(message.chat.id,"🔧 ADMIN PANEL",reply_markup=kb)

# ---------------- NOTICE ----------------

@bot.message_handler(func=lambda m:m.text=="📢 Send Notice")
def ask_notice(message):

    if message.from_user.id!=ADMIN_ID:
        return

    user_step[message.from_user.id]="notice"

    bot.send_message(message.chat.id,"Write notice message")

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="notice")
def send_notice(message):

    if message.from_user.id!=ADMIN_ID:
        return

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

# ---------------- EDIT PRICE ----------------

@bot.message_handler(func=lambda m:m.text=="💰 Edit Price")
def edit_price(message):

    if message.from_user.id!=ADMIN_ID:
        return

    kb=ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🟢 ৪ লাখ গ্লোরি","🟢 ৬ লাখ গ্লোরি")
    kb.add("🔶 ফুল গিল্ড ম্যাক্স","⚡ ট্রায়াল প্যাকেজ")
    kb.add("⚡ ৭ লেভেল ম্যাক্স গিল্ড")

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
def update_price(message):

    key=order_data[message.from_user.id]

    prices[key]=int(message.text)

    bot.send_message(message.chat.id,f"✅ Price Updated\n\n{packages[key]} → {message.text} Tk")

    user_step[message.from_user.id]=None

# ---------------- SHOP ----------------

@bot.message_handler(func=lambda m:m.text=="🛒 Shop Items")
def shop(message):

    text=f"""
👑 ALPHAN SPECIAL OFFERS 👑

🟢 ৪ লাখ গ্লোরি – ৳{prices['4l']}
🟢 ৬ লাখ গ্লোরি – ৳{prices['6l']}
🔶 ফুল গিল্ড ম্যাক্স – ৳{prices['guild']}
⚡ ট্রায়াল প্যাকেজ – ৳{prices['trial']}
⚡ ৭ লেভেল ম্যাক্স গিল্ড – ৳{prices['lvl7']}
"""

    kb=InlineKeyboardMarkup()

    for k,v in packages.items():
        kb.add(InlineKeyboardButton(v,callback_data=k))

    bot.send_message(message.chat.id,text,reply_markup=kb)

# ---------------- ORDER ----------------

@bot.callback_query_handler(func=lambda call:call.data in packages)
def package(call):

    order_data[call.from_user.id]={"package":packages[call.data]}

    user_step[call.from_user.id]="uid"

    bot.send_message(call.message.chat.id,"Send Clan UID")

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="uid")
def uid(message):

    order_data[message.from_user.id]["uid"]=message.text
    user_step[message.from_user.id]="number"

    bot.send_message(message.chat.id,"Send WhatsApp Number")

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="number")
def number(message):

    order_data[message.from_user.id]["number"]=message.text
    user_step[message.from_user.id]="ss"

    bot.send_message(message.chat.id,
"""💳 Payment Number

Bkash / Nagad

01861316505

Only Send Money

Send payment screenshot""")

# ---------------- SCREENSHOT ----------------

@bot.message_handler(content_types=['photo'])
def screenshot(message):

    if user_step.get(message.from_user.id)!="ss":
        return

    data=order_data[message.from_user.id]

    order_id=str(uuid.uuid4())[:8]

    cursor.execute(
        "INSERT INTO orders VALUES(?,?,?,?,?,?)",
        (order_id,message.from_user.id,data["package"],data["uid"],data["number"],"pending")
    )

    conn.commit()

    kb=InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("✅ Approve",callback_data="approve_"+order_id),
        InlineKeyboardButton("❌ Reject",callback_data="reject_"+order_id)
    )

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        f"""🆕 NEW ORDER

Order ID: {order_id}

Package: {data['package']}
Clan UID: {data['uid']}
WhatsApp: {data['number']}""",
        reply_markup=kb
    )

    bot.send_message(message.chat.id,"✅ Order Submitted Successfully")

    user_step[message.from_user.id]=None

# ---------------- APPROVE / REJECT ----------------

@bot.callback_query_handler(func=lambda c:c.data.startswith("approve"))
def approve(call):

    order_id=call.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='approved' WHERE order_id=?",(order_id,))
    conn.commit()

    bot.edit_message_caption(
        f"Order ID {order_id}\n\nSTATUS: ✅ APPROVED",
        call.message.chat.id,
        call.message.message_id
    )

@bot.callback_query_handler(func=lambda c:c.data.startswith("reject"))
def reject(call):

    order_id=call.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='rejected' WHERE order_id=?",(order_id,))
    conn.commit()

    bot.edit_message_caption(
        f"Order ID {order_id}\n\nSTATUS: ❌ REJECTED",
        call.message.chat.id,
        call.message.message_id
    )

# ---------------- SAFE POLLING ----------------

while True:
    try:
        bot.infinity_polling(timeout=60,long_polling_timeout=30,skip_pending=True)
    except Exception as e:
        print(e)
        time.sleep(5)
