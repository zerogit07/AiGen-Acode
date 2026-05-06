from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.db import get_all_models

async def menu_utama(user_id: int = None, is_admin: bool = False):
    """
    Membuat keyboard menu utama.
    - Admin: melihat semua model (termasuk nonaktif).
    - User/member: hanya model aktif.
    """
    if is_admin:
        models = await get_all_models(active_only=False)
    else:
        models = await get_all_models(active_only=True)

    builder = InlineKeyboardBuilder()

    if not models:
        builder.button(text="⚠️ Tidak ada model tersedia", callback_data="noop")
    else:
        for model in models:
            # model[0]=id, model[1]=name, model[2]=callback_data, model[3]=is_active, model[4]=sort_order
            name = model[1]
            callback = model[2]
            builder.button(text=name.center(25), callback_data=callback)

    # Susun 2 kolom seperti biasa
    builder.adjust(2)
    return builder.as_markup()