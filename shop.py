from telebot.types import InlineKeyboardMarkup,InlineKeyboardButton
from database import get_items

def shop_menu():

    markup = InlineKeyboardMarkup()

    items = get_items()

    for item in items:

        markup.add(
            InlineKeyboardButton(
                f"{item[1]} - {item[2]}৳",
                callback_data=f"order_{item[0]}"
            )
        )

    return markup
