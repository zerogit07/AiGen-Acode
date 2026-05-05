from aiogram.utils.keyboard import InlineKeyboardBuilder

def daftar_keyboard(paket: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Kirim Bukti".center(25), callback_data=f"kirim_bukti_{paket}")
    builder.button(text="🔙 Kembali".center(25), callback_data="kembali_nonmember")
    builder.adjust(1)
    return builder.as_markup()