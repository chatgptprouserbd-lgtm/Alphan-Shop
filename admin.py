from telebot.types import InlineKeyboardMarkup,InlineKeyboardButton

def admin_panel():

    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton("📦 Orders",callback_data="admin_orders")
    )

    markup.add(
        InlineKeyboardButton("📢 Broadcast",callback_data="admin_broadcast")
    )

    markup.add(
        InlineKeyboardButton("➕ Add Item",callback_data="admin_add_item")
    )

    markup.add(
        InlineKeyboardButton("🎟 Generate Coupon",callback_data="admin_coupon")
    )

    markup.add(
        InlineKeyboardButton("📊 Sales Stats",callback_data="admin_stats")
    )

    return markup
