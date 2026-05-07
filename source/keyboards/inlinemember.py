from aiogram.utils.keyboard import InlineKeyboardBuilder

def member_list_keyboard(user_id: int, paket: str, page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Detail".center(25), callback_data=f"detail_{user_id}")
    builder.button(text="✏️ Ubah".center(25), callback_data=f"ubah_{user_id}")
    builder.button(text="🗑️ Hapus".center(25), callback_data=f"hapus_{user_id}")

    if total_pages > 1:
        if page > 0:
            builder.button(text="⬅️ Sebelumnya", callback_data=f"memberpage_{page-1}")
        if page < total_pages - 1:
            builder.button(text="➡️ Selanjutnya", callback_data=f"memberpage_{page+1}")

    builder.button(text="🔙 Kembali ke Setting Member".center(25), callback_data="admin_set_member")
    builder.adjust(3)
    return builder.as_markup()