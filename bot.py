:::writing{variant="standard" id="48291"}
from flask import Flask
import threading
import os
import time
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import uuid

# ---------------- KEEP ALIVE ----------------

app = Flask(name)

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

trial_notice = """
⚠️ TRIAL PACKAGE NOTICE

━━━━━━━━━━━━━━

এই Trial Package এ ৪টি Bot থাকবে ৮ ঘন্টার জন্য।

আপনি মোট কত Glory পাবেন তা আগে থেকে বলা সম্ভব নয়।
এটি সম্পূর্ণ Server activity এর উপর নির্ভর করে।

কখনও কখনও Server এ বেশি Rush থাকলে Bot Guild এ ঢুকতে সময় লাগতে পারে।

━━━━━━━━━━━━━━

⚠️ এটি একটি Trial Package।

যদি এই সমস্যা না চান তাহলে Premium Package ব্যবহার করুন।

━━━━━━━━━━━━━━
"""

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

    bot.send_message(m.chat.id,"⚙️ ADMIN PANEL",reply_markup=kb)

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

    bot.send_message(m.chat.id,"✅ Notice Sent")
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

    pkg=c.data.split("")[1]
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

    bot.send_message(m.chat.id,"✅ Price Updated")
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

    if c.data=="p4":

        kb=InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Continue",callback_data="confirm_trial"))

        bot.send_message(c.message.chat.id,trial_notice,reply_markup=kb)
        return

    order_data[c.from_user.id]={"package":packages[c.data]}
    user_step[c.from_user.id]="uid"

    bot.send_message(c.message.chat.id,"Send Clan UID")

@bot.callback_query_handler(func=lambda c:c.data=="confirm_trial")
def confirm_trial(c):

    order_data[c.from_user.id]={"package":packages["p4"]}
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

    bot.send_message(m.chat.id,"Send Payment Screenshot")

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
    InlineKeyboardButton("✅ Approve",callback_data="a"+oid),
    InlineKeyboardButton("❌ Reject",callback_data="r_"+oid)
    )

    bot.send_photo(
    ADMIN_ID,
    m.photo[-1].file_id,
    f"NEW ORDER\n\nID: {oid}\nPackage: {d['package']}\nUID: {d['uid']}\nWA: {d['number']}",
    reply_markup=kb
    )

    bot.send_message(m.chat.id,"✅ Order Submitted")

    user_step.pop(m.from_user.id,None)
    order_data.pop(m.from_user.id,None)

# ---------------- APPROVE ----------------

@bot.callback_query_handler(func=lambda c:c.data.startswith("a_"))
def approve(c):

    oid=c.data.split("")[1]

    cursor.execute("UPDATE orders SET status='approved' WHERE order_id=?",(oid,))
    conn.commit()

    bot.edit_message_caption(f"Order {oid}\n\n✅ APPROVED",c.message.chat.id,c.message.message_id)

# ---------------- REJECT ----------------

@bot.callback_query_handler(func=lambda c:c.data.startswith("r"))
def reject(c):

    oid=c.data.split("_")[1]

    cursor.execute("UPDATE orders SET status='rejected' WHERE order_id=?",(oid,))
    conn.commit()

    bot.edit_message_caption(f"Order {oid}\n\n❌ REJECTED",c.message.chat.id,c.message.message_id)

# ---------------- RESTART ----------------

@bot.message_handler(func=lambda m:m.text=="🔄 Restart Bot")
def restart(m):

    user_step.pop(m.from_user.id,None)
    order_data.pop(m.from_user.id,None)

    bot.send_message(m.chat.id,"🔄 Bot Restarted")
