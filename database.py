import sqlite3

conn = sqlite3.connect("shop.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
order_id TEXT,
user_id INTEGER,
clan_uid TEXT,
whatsapp TEXT,
item TEXT,
coupon TEXT,
status TEXT
)
""")

conn.commit()

def add_order(order):
    cursor.execute(
        "INSERT INTO orders VALUES(?,?,?,?,?,?,?)",
        order
    )
    conn.commit()

def get_orders():
    cursor.execute("SELECT * FROM orders")
    return cursor.fetchall()
