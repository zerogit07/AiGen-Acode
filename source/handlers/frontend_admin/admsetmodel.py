from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from source.database.db import get_all_models, swap_model_order, toggle_model_active
from config import ADMIN_ID

router = Router()

@router.callback_query(F.data == "admin_set_model")
async def admsetmodel_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    models = await get_all_models()
    lines = ["📋 <b>Daftar Model</b>\n"]
    for m in models:
        status = "🟢" if m[3] else "🔴"
        lines.append(f"{status} {m[4]}. {m[1]}")

    builder = InlineKeyboardBuilder()
    for m in models:
        builder.button(text=f"{m[1]}".center(25), callback_data=f"modeldetail_{m[0]}")
        builder.button(text="⬆", callback_data=f"modelup_{m[0]}")
        builder.button(text="⬇", callback_data=f"modeldn_{m[0]}")
        builder.button(
            text="Nonaktifkan" if m[3] else "Aktifkan",
            callback_data=f"modeltoggle_{m[0]}"
        )
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_panel")
    builder.adjust(4)

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("modelup_"))
async def model_up(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    model_id = int(callback.data.split("_")[1])
    models = await get_all_models()
    # Cari id model di atasnya
    ids = [m[0] for m in models]
    idx = ids.index(model_id)
    if idx > 0:
        await swap_model_order(model_id, ids[idx-1])
    await admsetmodel_menu(callback)

@router.callback_query(F.data.startswith("modeldn_"))
async def model_down(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    model_id = int(callback.data.split("_")[1])
    models = await get_all_models()
    ids = [m[0] for m in models]
    idx = ids.index(model_id)
    if idx < len(ids) - 1:
        await swap_model_order(model_id, ids[idx+1])
    await admsetmodel_menu(callback)

@router.callback_query(F.data.startswith("modeltoggle_"))
async def model_toggle(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    model_id = int(callback.data.split("_")[1])
    name, new_state = await toggle_model_active(model_id)
    await callback.answer(f"{name} sekarang {'aktif' if new_state else 'nonaktif'}.", show_alert=True)
    await admsetmodel_menu(callback)