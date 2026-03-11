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


def sales_stats():

    cursor.execute("SELECT COUNT(*) FROM orders")

    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='approved'")

    approved = cursor.fetchone()[0]

    return total,approved
