from flask import Flask
import threading
import os
import telebot
import uuid
import sqlite3
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

# ---------------- BOT CONFIG ----------------

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# ---------------- DATABASE ----------------

conn = sqlite3.connect("orders.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
order_id TEXT,
user_id INTEGER,
package TEXT,
uid TEXT,
whatsapp TEXT,
coupon TEXT,
status TEXT
)
""")

conn.commit()

user_step = {}

# ---------------- MENU ----------------

def menu():

    m = ReplyKeyboardMarkup(resize_keyboard=True)

    m.add("🛒 Shop Items", "📦 My Orders")
    m.add("📞 Customer Support", "📜 Order Rules")
    m.add("ℹ️ About Shop", "🔄 Restart Bot")

    return m

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        "👑 Welcome to ALPHAN GAMING SHOP\n\nGlory Bot Sale",
        reply_markup=menu()
    )

# ---------------- RESTART ----------------

@bot.message_handler(func=lambda m: m.text == "🔄 Restart Bot")
def restart(message):
    start(message)

# ---------------- ABOUT ----------------

@bot.message_handler(func=lambda m: m.text == "ℹ️ About Shop")
def about(message):

    text = """
👑 ALPHAN GAMING SHOP

🎮 Professional Glory Bot Service

⚡ Fast Delivery
⚡ Trusted Service
⚡ 24/7 Support

📞 WhatsApp:
01607254046
"""

    bot.send_message(message.chat.id, text)

# ---------------- RULES ----------------

@bot.message_handler(func=lambda m: m.text == "📜 Order Rules")
def rules(message):

    text = """
📜 ORDER RULES

• Guild অবশ্যই Auto Approval ON রাখবেন

• অবশ্যই সঠিক Guild / Clan UID দিবেন

• Payment করার পরে Original Screenshot দিবেন

• Payment করার সময় Only Send Money ব্যবহার করবেন
"""

    bot.send_message(message.chat.id, text)

# ---------------- SUPPORT ----------------

@bot.message_handler(func=lambda m: m.text == "📞 Customer Support")
def support(message):

    bot.send_message(
        message.chat.id,
        "WhatsApp Support:\n01607254046"
    )

@bot.message_handler(commands=['admin'])
def admin_panel(message):

    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not admin")
        return

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("📦 View Orders", callback_data="view_orders")
    )

    kb.add(
        InlineKeyboardButton("🎟 Generate Coupon", callback_data="gen_coupon")
    )

    kb.add(
        InlineKeyboardButton("📢 Send Notice", callback_data="notice")
    )

    bot.send_message(
        message.chat.id,
        "🛠 ADMIN PANEL",
        reply_markup=kb
    )

# ---------------- SHOP ----------------

@bot.message_handler(func=lambda m: m.text == "🛒 Shop Items")
def shop(message):

    text = """
👑 ALPHAN SPECIAL OFFERS 👑
━━━━━━━━━━━━━━━━

🟢 ৪ লাখ গ্লোরি – ৳750 টাকা
🟢 ৬ লাখ গ্লোরি – ৳950 টাকা

🔶 ফুল গিল্ড ম্যাক্স ৭ প্যাকেজ – ৳1350 টাকা

🌟 রিজিওন টপ ১০ প্যাকেজ – যোগাযোগ করুন

⚡ ট্রায়াল প্যাকেজ (৪টি বোট ৮ ঘন্টা) – ৳180 টাকা

⚡ ৭ লেভেল ম্যাক্স গিল্ড বিক্রি – ৳1150 টাকা

━━━━━━━━━━━━━━━━
একটি প্যাকেজ সিলেক্ট করুন:
"""

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("৪ লাখ গ্লোরি", callback_data="p1"),
        InlineKeyboardButton("৬ লাখ গ্লোরি", callback_data="p2")
    )

    kb.add(
        InlineKeyboardButton("ফুল গিল্ড ম্যাক্স", callback_data="p3")
    )

    kb.add(
        InlineKeyboardButton("ট্রায়াল প্যাকেজ", callback_data="p4")
    )

    kb.add(
        InlineKeyboardButton("৭ লেভেল গিল্ড", callback_data="p5")
    )

    bot.send_message(message.chat.id, text, reply_markup=kb)

# ---------------- PACKAGE ----------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("p"))
def package(c):

    packages = {
        "p1": "৪ লাখ গ্লোরি",
        "p2": "৬ লাখ গ্লোরি",
        "p3": "ফুল গিল্ড ম্যাক্স",
        "p4": "ট্রায়াল প্যাকেজ",
        "p5": "৭ লেভেল গিল্ড"
    }

    user_step[c.from_user.id] = {
        "package": packages[c.data]
    }

    bot.send_message(c.message.chat.id, "Send Clan UID")

# ---------------- UID ----------------

@bot.message_handler(func=lambda m: m.from_user.id in user_step and "uid" not in user_step[m.from_user.id])
def uid(message):

    user_step[message.from_user.id]["uid"] = message.text

    bot.send_message(message.chat.id, "Send WhatsApp number")

# ---------------- WHATSAPP ----------------

@bot.message_handler(func=lambda m: m.from_user.id in user_step and "whatsapp" not in user_step[m.from_user.id])
def whatsapp(message):

    user_step[message.from_user.id]["whatsapp"] = message.text

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("🎟 Enter Coupon", callback_data="coupon")
    )

    kb.add(
        InlineKeyboardButton("❌ Don't have coupon", callback_data="nocoupon")
    )

    bot.send_message(
        message.chat.id,
        "Do you have a coupon?",
        reply_markup=kb
    )

# ---------------- COUPON ----------------

@bot.callback_query_handler(func=lambda c: c.data in ["coupon","nocoupon"])
def coupon(c):

    if c.data == "nocoupon":

        user_step[c.from_user.id]["coupon"] = "NONE"

        payment(c.message)

    else:

        bot.send_message(
            c.message.chat.id,
            "Send coupon code"
        )

# ---------------- PAYMENT ----------------

def payment(message):

    text = """
💳 PAYMENT METHOD

bKash: 01861316505
Nagad: 01861316505

⚠️ Only Send Money

Payment করার পরে screenshot পাঠান।
"""

    bot.send_message(message.chat.id, text)

# ---------------- SCREENSHOT ----------------

@bot.message_handler(content_types=['photo'])
def screenshot(message):

    uid = message.from_user.id

    if uid not in user_step:
        return

    data = user_step[uid]

    order_id = str(uuid.uuid4())[:8]

    cursor.execute(
        "INSERT INTO orders VALUES(?,?,?,?,?,?,?)",
        (
            order_id,
            uid,
            data["package"],
            data["uid"],
            data["whatsapp"],
            data.get("coupon","NONE"),
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
Coupon: {data.get("coupon","NONE")}
"""

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"ok_{order_id}_{uid}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"no_{order_id}_{uid}")
    )

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=caption,
        reply_markup=kb
    )

    bot.send_message(
        message.chat.id,
        "✅ Order Submitted Successfully\n\nঅনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।"
    )

    del user_step[uid]

# ---------------- ADMIN ACTION ----------------

@bot.callback_query_handler(func=lambda c: c.data.startswith(("ok","no")))
def admin_action(c):

    data = c.data.split("_")

    action = data[0]
    order = data[1]
    user = int(data[2])

    if action == "ok":

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

# ---------------- STABLE POLLING ----------------

while True:

    try:

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=30,
            skip_pending=True
        )

    except Exception as e:

        print("Bot crashed:", e)

        time.sleep(10)
