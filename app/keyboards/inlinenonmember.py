from aiogram.utils.keyboard import InlineKeyboardBuilder

def nonmember_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Lite".center(25), callback_data="register_lite")
    builder.button(text="🔥 Pro".center(25), callback_data="register_pro")
    builder.button(text="💎 Ultra".center(25), callback_data="register_ultra")
    builder.adjust(2)
    return builder.as_markup()