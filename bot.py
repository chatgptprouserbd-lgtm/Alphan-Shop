import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import uuid
import os
import sys

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("shop.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS orders (order_id TEXT,user_id INTEGER,package TEXT,uid TEXT,number TEXT,status TEXT)")
conn.commit()

user_step = {}
order_data = {}

# package names
packages = {
"4l":"🟢 ৪ লাখ গ্লোরি – ৳750",
"6l":"🟢 ৬ লাখ গ্লোরি – ৳950",
"guild":"🔶 ফুল গিল্ড ম্যাক্স ৭ প্যাকেজ – ৳1350",
"trial":"⚡ ট্রায়াল প্যাকেজ – ৳180",
"lvl7":"⚡ ৭ লেভেল ম্যাক্স গিল্ড – ৳1150"
}

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):

    cursor.execute("INSERT OR IGNORE INTO users VALUES(?)",(message.from_user.id,))
    conn.commit()

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🛒 Shop Items","📦 My Orders")
    kb.add("📞 Customer Support","📜 Order Rules")
    kb.add("ℹ️ About Shop","🔄 Restart Bot")

    bot.send_message(
        message.chat.id,
        "👑 Welcome to ALPHAN GAMING SHOP\n\nGlory Bot Sale",
        reply_markup=kb
    )

# ---------------- SHOP ----------------

@bot.message_handler(func=lambda m: m.text=="🛒 Shop Items")
def shop(message):

    text = """
👑 ALPHAN SPECIAL OFFERS 👑
━━━━━━━━━━━━━━━━

🟢 ৪ লাখ গ্লোরি – ৳750 টাকা
🟢 ৬ লাখ গ্লোরি – ৳950 টাকা

🔶 ফুল গিল্ড ম্যাক্স ৭ প্যাকেজ – ৳1350 টাকা

⭐ রিজিওন টপ ১০ প্যাকেজ – যোগাযোগ করুন

⚡ ট্রায়াল প্যাকেজ (৪টি বোট ৮ ঘণ্টা) – ৳180 টাকা

⚡ ৭ লেভেল ম্যাক্স গিল্ড বিক্রি – ৳1150 টাকা

━━━━━━━━━━━━━━━━
একটি প্যাকেজ সিলেক্ট করুন
"""

    kb = InlineKeyboardMarkup()

    kb.add(InlineKeyboardButton("🟢 ৪ লাখ গ্লোরি",callback_data="4l"))
    kb.add(InlineKeyboardButton("🟢 ৬ লাখ গ্লোরি",callback_data="6l"))
    kb.add(InlineKeyboardButton("🔶 ফুল গিল্ড ম্যাক্স",callback_data="guild"))
    kb.add(InlineKeyboardButton("⚡ ট্রায়াল প্যাকেজ",callback_data="trial"))
    kb.add(InlineKeyboardButton("⚡ ৭ লেভেল ম্যাক্স গিল্ড",callback_data="lvl7"))

    bot.send_message(message.chat.id,text,reply_markup=kb)

# ---------------- PACKAGE SELECT ----------------

@bot.callback_query_handler(func=lambda call: call.data in packages)
def package(call):

    order_data[call.from_user.id] = {"package":packages[call.data]}
    user_step[call.from_user.id] = "uid"

    bot.send_message(call.message.chat.id,"Send Clan UID")

# ---------------- UID ----------------

@bot.message_handler(func=lambda m: user_step.get(m.from_user.id)=="uid")
def get_uid(message):

    order_data[message.from_user.id]["uid"] = message.text
    user_step[message.from_user.id] = "number"

    bot.send_message(message.chat.id,"Send WhatsApp Number")

# ---------------- NUMBER ----------------

@bot.message_handler(func=lambda m: user_step.get(m.from_user.id)=="number")
def get_number(message):

    order_data[message.from_user.id]["number"] = message.text
    user_step[message.from_user.id] = "ss"

    bot.send_message(message.chat.id,"Send Payment Screenshot")

# ---------------- SCREENSHOT ----------------

@bot.message_handler(content_types=['photo'])
def screenshot(message):

    if user_step.get(message.from_user.id)!="ss":
        return

    data = order_data[message.from_user.id]
    order_id = str(uuid.uuid4())[:8]

    cursor.execute(
        "INSERT INTO orders VALUES(?,?,?,?,?,?)",
        (order_id,message.from_user.id,data["package"],data["uid"],data["number"],"pending")
    )
    conn.commit()

    kb = InlineKeyboardMarkup()
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
WhatsApp: {data['number']}
""",
        reply_markup=kb
    )

    bot.send_message(message.chat.id,"✅ Order Submitted Successfully\n\nঅনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।")

    user_step[message.from_user.id]=None

# ---------------- APPROVE ----------------

@bot.callback_query_handler(func=lambda c:c.data.startswith("approve"))
def approve(call):

    order_id = call.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='approved' WHERE order_id=?",(order_id,))
    conn.commit()

    bot.edit_message_caption(
        f"Order ID {order_id}\n\nSTATUS: ✅ APPROVED",
        call.message.chat.id,
        call.message.message_id
    )

    cursor.execute("SELECT user_id FROM orders WHERE order_id=?",(order_id,))
    user = cursor.fetchone()[0]

    bot.send_message(user,"✅ Order Approved")

# ---------------- REJECT ----------------

@bot.callback_query_handler(func=lambda c:c.data.startswith("reject"))
def reject(call):

    order_id = call.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='rejected' WHERE order_id=?",(order_id,))
    conn.commit()

    bot.edit_message_caption(
        f"Order ID {order_id}\n\nSTATUS: ❌ REJECTED",
        call.message.chat.id,
        call.message.message_id
    )

    cursor.execute("SELECT user_id FROM orders WHERE order_id=?",(order_id,))
    user = cursor.fetchone()[0]

    bot.send_message(user,"❌ Order Rejected")

# ---------------- MY ORDERS ----------------

@bot.message_handler(func=lambda m: m.text=="📦 My Orders")
def my_orders(message):

    cursor.execute(
        "SELECT order_id,package,status FROM orders WHERE user_id=?",
        (message.from_user.id,)
    )

    orders = cursor.fetchall()

    if not orders:
        bot.send_message(message.chat.id,"❌ No orders found")
        return

    text="📦 YOUR ORDERS\n\n"

    for o in orders:

        status = "⏳ Pending"

        if o[2]=="approved":
            status="✅ Approved"

        if o[2]=="rejected":
            status="❌ Rejected"

        text += f"Order ID: {o[0]}\nPackage: {o[1]}\nStatus: {status}\n\n"

    bot.send_message(message.chat.id,text)

# ---------------- NOTICE ----------------

@bot.message_handler(commands=['notice'])
def notice(message):

    if message.from_user.id!=ADMIN_ID:
        return

    text = message.text.replace("/notice ","")

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for u in users:
        try:
            bot.send_message(u[0],text)
        except:
            pass

    bot.send_message(message.chat.id,"Notice Sent")

# ---------------- RULES ----------------

@bot.message_handler(func=lambda m:m.text=="📜 Order Rules")
def rules(message):

    bot.send_message(
        message.chat.id,
"""📜 ORDER RULES

• Guild Auto Approval ON রাখতে হবে
• সঠিক Clan ID দিতে হবে
• Original payment screenshot দিতে হবে
• Payment এ Only Send Money করবেন"""
)

# ---------------- SUPPORT ----------------

@bot.message_handler(func=lambda m:m.text=="📞 Customer Support")
def support(message):

    bot.send_message(message.chat.id,"WhatsApp: 01607254046")

# ---------------- ABOUT ----------------

@bot.message_handler(func=lambda m:m.text=="ℹ️ About Shop")
def about(message):

    bot.send_message(
        message.chat.id,
"""Welcome to ALPHAN GAMING SHOP

⚡ Fast Delivery
🔒 Trusted Service
💬 24/7 Support"""
)

# ---------------- RESTART ----------------

@bot.message_handler(func=lambda m:m.text=="🔄 Restart Bot")
def restart(message):

    if message.from_user.id!=ADMIN_ID:
        return

    bot.send_message(message.chat.id,"Restarting...")

    os.execv(sys.executable, ['python'] + sys.argv)

# ---------------- RUN ----------------

bot.infinity_polling()
import time

while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
