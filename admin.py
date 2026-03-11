from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel():

    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton("📦 View Orders", callback_data="admin_orders")
    )

    markup.add(
        InlineKeyboardButton("🎟 Generate Coupon", callback_data="admin_coupon")
    )

    markup.add(
        InlineKeyboardButton("📊 Sales Stats", callback_data="admin_stats")
    )

    markup.add(
        InlineKeyboardButton("📢 Broadcast Notice", callback_data="admin_broadcast")
    )

    return markup
