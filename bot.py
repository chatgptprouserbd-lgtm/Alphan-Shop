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
"p1":"🟢 ৪ লাখ গ্লোরি",
"p2":"🟢 ৬ লাখ গ্লোরি",
"p3":"🔶 ফুল গিল্ড ম্যাক্স",
"p4":"⚡ ট্রায়াল প্যাকেজ",
"p5":"⚡ ৭ লেভেল গিল্ড ক্রয়"
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

# ---------------- ADMIN PANEL ----------------

@bot.message_handler(commands=['admin'])
def admin_panel(m):

    if m.from_user.id != ADMIN_ID:
        return

    kb=ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📢 Send Notice","💰 Edit Price")

    bot.send_message(m.chat.id,"ADMIN PANEL",reply_markup=kb)

# ---------------- NOTICE ----------------

@bot.message_handler(func=lambda m:m.text=="📢 Send Notice")
def notice_ask(m):

    if m.from_user.id != ADMIN_ID:
        return

    user_step[m.from_user.id]="notice"
    bot.send_message(m.chat.id,"Send notice message")

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="notice")
def send_notice(m):

    cursor.execute("SELECT id FROM users")
    users=cursor.fetchall()

    text=f"""
⚠️ IMPORTANT NOTICE

━━━━━━━━━━━━━━

{m.text}

━━━━━━━━━━━━━━

— ALPHAN GAMING SHOP
"""

    for u in users:
        try:
            bot.send_message(u[0],text)
        except:
            pass

    bot.send_message(m.chat.id,"Notice Sent")
    user_step.pop(m.from_user.id,None)

# ---------------- EDIT PRICE ----------------

@bot.message_handler(func=lambda m:m.text=="💰 Edit Price")
def edit_price(m):

    if m.from_user.id != ADMIN_ID:
        return

    kb=InlineKeyboardMarkup()

    kb.add(InlineKeyboardButton("8L Glory",callback_data="edit_p1"))
    kb.add(InlineKeyboardButton("6L Glory",callback_data="edit_p2"))
    kb.add(InlineKeyboardButton("Full Guild",callback_data="edit_p3"))
    kb.add(InlineKeyboardButton("Trial",callback_data="edit_p4"))
    kb.add(InlineKeyboardButton("7 Level Guild",callback_data="edit_p5"))

    bot.send_message(m.chat.id,"Select package",reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith("edit_"))
def edit_select(c):

    pkg=c.data.split("_")[1]
    order_data[c.from_user.id]={"edit":pkg}

    user_step[c.from_user.id]="price"

    bot.send_message(c.message.chat.id,"Send new price")

@bot.message_handler(func=lambda m:user_step.get(m.from_user.id)=="price")
def save_price(m):

    pkg=order_data[m.from_user.id]["edit"]

    cursor.execute(
    "UPDATE prices SET price=? WHERE package=?",
    (int(m.text),pkg)
    )

    conn.commit()

    bot.send_message(m.chat.id,"Price Updated")
    user_step.pop(m.from_user.id,None)

# ---------------- PRICE LIST ----------------

@bot.message_handler(func=lambda m:m.text=="👑 Price List")
def price_list(m):

    text=f"""
👑 ALPHAN SPECIAL OFFERS 👑

🟢 ৪ লাখ গ্লোরি – ৳{get_price('p1')}
🟢 ৬ লাখ গ্লোরি – ৳{get_price('p2')}
🔶 ফুল গিল্ড ম্যাক্স – ৳{get_price('p3')}
⚡ ট্রায়াল প্যাকেজ – ৳{get_price('p4')}
⚡ ৭ লেভেল গিল্ড ক্রয় – ৳{get_price('p5')}
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
"""
💳 PAYMENT INSTRUCTION

━━━━━━━━━━━━━━

📱 bKash / Nagad

Number: 01861316505

✔ Only Send Money

━━━━━━━━━━━━━━

📸 Payment করার পরে অবশ্যই
original screenshot send করবেন।

⚠️ Fake screenshot দিলে order reject হবে।
"""
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

    bot.send_message(
m.chat.id,
"""
✅ ORDER RECEIVED

━━━━━━━━━━━━━━

আপনার order সফলভাবে submit হয়েছে।

⏳ এখন Admin review করবে।

অনুগ্রহ করে কিছু সময় অপেক্ষা করুন।

━━━━━━━━━━━━━━

🙏 ALPHAN GAMING SHOP ব্যবহার করার জন্য ধন্যবাদ।
"""
)

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

    cursor.execute("SELECT user_id FROM orders WHERE order_id=?",(oid,))
    user_id=cursor.fetchone()[0]

    bot.send_message(
    user_id,
    f"""
✅ ORDER APPROVED

━━━━━━━━━━━━━━

Your Order ID: {oid}

Your order has been approved.

━━━━━━━━━━━━━━

Thank you for choosing
ALPHAN GAMING SHOP
"""
    )

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

    cursor.execute("SELECT user_id FROM orders WHERE order_id=?",(oid,))
    user_id=cursor.fetchone()[0]

    bot.send_message(
    user_id,
    f"""
❌ ORDER REJECTED

━━━━━━━━━━━━━━

Your Order ID: {oid}

Unfortunately your order was rejected.

Please contact support if needed.

━━━━━━━━━━━━━━

ALPHAN GAMING SHOP
"""
    )

# ---------------- MY ORDERS ----------------

@bot.message_handler(func=lambda m:m.text=="📦 My Orders")
def my_orders(m):

    cursor.execute(
    "SELECT order_id,package,status FROM orders WHERE user_id=?",
    (m.from_user.id,)
    )

    rows=cursor.fetchall()

    if not rows:
        bot.send_message(m.chat.id,"No orders found")
        return

    text="YOUR ORDERS\n\n"

    for r in rows:
        text+=f"{r[0]} | {r[1]} | {r[2]}\n"

    bot.send_message(m.chat.id,text)

# ---------------- SUPPORT ----------------

@bot.message_handler(func=lambda m:m.text=="📞 Customer Support")
def support(m):

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            "📞 Chat on WhatsApp",
            url="https://wa.me/8801607254046"
        )
    )

    bot.send_message(
        m.chat.id,
        "Customer Support এ যোগাযোগ করতে নিচের বাটনে চাপুন:",
        reply_markup=kb
    )
# ---------------- RULES ----------------

@bot.message_handler(func=lambda m:m.text=="📜 Order Rules")
def rules(m):

    bot.send_message(
m.chat.id,
"""
📜 ORDER RULES

━━━━━━━━━━━━━━

1️⃣ Guild অবশ্যই **Auto Approval ON** করে রাখবেন

2️⃣ Order করার সময় **সঠিক Clan / Guild UID** দিবেন

3️⃣ Payment করার পরে **Original Screenshot** দিতে হবে

4️⃣ Payment অবশ্যই **Send Money** করতে হবে

5️⃣ ভুল UID দিলে bot দায়ী থাকবে না

━━━━━━━━━━━━━━

✔ Rules follow করলে order দ্রুত approve হবে
"""
)

# ---------------- ABOUT ----------------

@bot.message_handler(func=lambda m:m.text=="ℹ️ About Shop")
def about(m):

    bot.send_message(
m.chat.id,
"""
ℹ️ ABOUT ALPHAN GAMING SHOP

━━━━━━━━━━━━━━

👑 Shop Name:
ALPHAN GAMING SHOP

⚡ Service:
Glory Bot Sale

🎮 আমরা Free Fire guild boosting
এবং glory service প্রদান করি।

✔ Trusted Service
✔ Fast Delivery
✔ Active Support

━━━━━━━━━━━━━━

📞 Support:
WhatsApp - 01607254046
"""
)

# ---------------- RESTART ----------------

@bot.message_handler(func=lambda m:m.text=="🔄 Restart Bot")
def restart(m):

    user_step.pop(m.from_user.id,None)
    order_data.pop(m.from_user.id,None)

    bot.send_message(m.chat.id,"Bot Restarted")
    start(m)

# ---------------- RUN BOT ----------------

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(e)
        time.sleep(5)
