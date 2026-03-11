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

cursor.execute("""
CREATE TABLE IF NOT EXISTS coupons(
code TEXT,
discount INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS shop_items(
id TEXT,
name TEXT,
price INTEGER
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


def add_coupon(code,discount):
    cursor.execute(
        "INSERT INTO coupons VALUES(?,?)",
        (code,discount)
    )
    conn.commit()


def get_coupon(code):
    cursor.execute(
        "SELECT * FROM coupons WHERE code=?",
        (code,)
    )
    return cursor.fetchone()


def add_item(i,name,price):
    cursor.execute(
        "INSERT INTO shop_items VALUES(?,?,?)",
        (i,name,price)
    )
    conn.commit()


def get_items():
    cursor.execute("SELECT * FROM shop_items")
    return cursor.fetchall()
