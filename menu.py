from telebot import types


# Main menu
main_menu = types.InlineKeyboardMarkup(row_width=5)
main_menu.add(
    # types.InlineKeyboardButton(text='🛍 Каталог', callback_data='catalog'),
    types.InlineKeyboardButton(text='👤 Профиль', callback_data='profile'),
    types.InlineKeyboardButton(text='🕹️ Играть', callback_data='play'),
    types.InlineKeyboardButton(text='🛠 Настройки', callback_data='settings')
    # types.InlineKeyboardButton(text='🛒 Мои покупки', callback_data='purchases'),
    # types.InlineKeyboardButton(text='💸 Пополнить баланс', callback_data='replenish_balance'),
)
main_menu.add(
    types.InlineKeyboardButton(text='👥 Социальное', callback_data='social'),
)

# profile menu
main_profile_menu = types.InlineKeyboardMarkup(row_width=5)
main_profile_menu.add(
    # types.InlineKeyboardButton(text='🛍 Каталог', callback_data='catalog'),
    types.InlineKeyboardButton(text='📚 Мои коллекции', callback_data='collection'),
    types.InlineKeyboardButton(text='💾 Созданные коллекции', callback_data='person_collection'),
    types.InlineKeyboardButton(text='❔ О боте', callback_data='about')
    # types.InlineKeyboardButton(text='🛒 Мои покупки', callback_data='purchases'),
    # types.InlineKeyboardButton(text='💸 Пополнить баланс', callback_data='replenish_balance'),
)
main_profile_menu.add(
    types.InlineKeyboardButton(text='🔙 Назад', callback_data='menu'),
)
