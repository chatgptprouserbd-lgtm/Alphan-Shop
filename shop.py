from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

shop_items = {
    "glory4": ("৪ লাখ গ্লোরি", 750),
    "glory6": ("৬ লাখ গ্লোরি", 950),
    "guild7": ("ফুল গিল্ড ম্যাক্স ৭ প্যাকেজ", 1350),
    "trial": ("ট্রায়াল প্যাকেজ", 180),
    "guildlvl7": ("৭ লেভেল ম্যাক্স গিল্ড", 1050)
}

def shop_menu():

    markup = InlineKeyboardMarkup()

    for key,data in shop_items.items():

        name = data[0]
        price = data[1]

        markup.add(
            InlineKeyboardButton(
                f"{name} - {price}৳",
                callback_data=f"order_{key}"
            )
        )

    return markup
