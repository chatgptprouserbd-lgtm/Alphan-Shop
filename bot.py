from flask import Flask
import threading
import os
import telebot
import uuid
import time
from telebot.types import *

# ---------------- KEEP ALIVE ----------------

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

def run():
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)

threading.Thread(target=run).start()

# ---------------- CONFIG ----------------

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

orders = {}

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
একটি প্যাকেজ সিলেক্ট করুন:
"""

    kb = InlineKeyboardMarkup()

    kb.add(InlineKeyboardButton("৪ লাখ গ্লোরি – ৳750",callback_data="p1"))
    kb.add(InlineKeyboardButton("৬ লাখ গ্লোরি – ৳950",callback_data="p2"))
    kb.add(InlineKeyboardButton("ফুল গিল্ড ম্যাক্স – ৳1350",callback_data="p3"))
    kb.add(InlineKeyboardButton("ট্রায়াল প্যাকেজ – ৳180",callback_data="p4"))
    kb.add(InlineKeyboardButton("৭ লেভেল ম্যাক্স গিল্ড – ৳1150",callback_data="p5"))

    bot.send_message(m.chat.id,text,reply_markup=kb)

# ---------------- PACKAGE SELECT ----------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("p"))
def package(c):

    packages = {
        "p1":"৪ লাখ গ্লোরি",
        "p2":"৬ লাখ গ্লোরি",
        "p3":"ফুল গিল্ড ম্যাক্স ৭ প্যাকেজ",
        "p4":"ট্রায়াল প্যাকেজ",
        "p5":"৭ লেভেল ম্যাক্স গিল্ড"
    }

    orders[c.from_user.id] = {}

    orders[c.from_user.id]["package"] = packages[c.data]

    bot.send_message(
        c.message.chat.id,
        "Send Clan UID"
    )

# ---------------- UID ----------------

@bot.message_handler(func=lambda m: m.from_user.id in orders and "uid" not in orders[m.from_user.id])
def uid(m):

    orders[m.from_user.id]["uid"] = m.text

    bot.send_message(
        m.chat.id,
        "Send WhatsApp number"
    )

# ---------------- WHATSAPP ----------------

@bot.message_handler(func=lambda m: m.from_user.id in orders and "whatsapp" not in orders[m.from_user.id])
def whatsapp(m):

    orders[m.from_user.id]["whatsapp"] = m.text

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

    uid = m.from_user.id

    if uid not in orders:
        return

    data = orders[uid]

    order_id = str(uuid.uuid4())[:8]

    caption = f"""
🆕 NEW ORDER

Order ID: {order_id}

Package: {data['package']}
Clan UID: {data['uid']}
WhatsApp: {data['whatsapp']}
"""

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("✅ Approve",callback_data=f"ok_{uid}"),
        InlineKeyboardButton("❌ Reject",callback_data=f"no_{uid}")
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

# ---------------- ADMIN ACTION ----------------

@bot.callback_query_handler(func=lambda c: c.data.startswith(("ok","no")))
def admin_action(c):

    action,user = c.data.split("_")

    user = int(user)

    if action == "ok":

        bot.send_message(
            user,
            "✅ Order Approved\n\nআপনার অর্ডার গ্রহণ করা হয়েছে।"
        )

    else:

        bot.send_message(
            user,
            "❌ Order Rejected\n\nSupport এ যোগাযোগ করুন।"
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

        print(e)

        time.sleep(10)
