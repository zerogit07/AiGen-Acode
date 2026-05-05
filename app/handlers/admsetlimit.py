from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.states.admin_limit import AdminLimitState
from app.database.db import set_limit
from config import ADMIN_ID

router = Router()

def back_to_admin():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali ke Admin Panel".center(25), callback_data="admin_panel")
    return builder.as_markup()

# === MENU SETTING LIMIT ===
@router.callback_query(F.data == "admin_set_limit")
async def admsetlimit_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="Lite", callback_data="limit_pilih_Lite")
    builder.button(text="Pro", callback_data="limit_pilih_Pro")
    builder.button(text="Ultra", callback_data="limit_pilih_Ultra")
    builder.button(text="🔙 Kembali", callback_data="admin_panel")
    builder.adjust(3)

    await callback.message.edit_text(
        "<b>📊 Setting Limit</b>\nPilih paket yang ingin diubah limit-nya.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# === PILIH PAKET ===
@router.callback_query(F.data.startswith("limit_pilih_"))
async def limit_pilih(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    paket = callback.data.replace("limit_pilih_", "")
    await state.update_data(paket=paket)
    await state.set_state(AdminLimitState.input_process)

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali", callback_data="admin_set_limit")
    builder.adjust(1)

    await callback.message.edit_text(
        f"Paket: <b>{paket}</b>\n\nKirim angka untuk <b>Process Limit</b> (maksimal proses berjalan).\nKetik /cancel untuk batal.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# === INPUT PROCESS LIMIT ===
@router.message(AdminLimitState.input_process)
async def limit_input_process(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        process_limit = int(message.text.strip())
    except ValueError:
        await message.answer("Harus berupa angka. Coba lagi.")
        return

    await state.update_data(process_limit=process_limit)
    await state.set_state(AdminLimitState.input_daily)

    await message.answer("Kirim angka untuk <b>Daily Quota</b> (batas per hari).", parse_mode="HTML")

# === INPUT DAILY QUOTA ===
@router.message(AdminLimitState.input_daily)
async def limit_input_daily(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        daily_quota = int(message.text.strip())
    except ValueError:
        await message.answer("Harus berupa angka. Coba lagi.")
        return

    data = await state.get_data()
    paket = data["paket"]
    process_limit = data["process_limit"]

    await set_limit(paket, process_limit, daily_quota)
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali ke Setting Limit", callback_data="admin_set_limit")
    builder.adjust(1)

    await message.answer(
        f"✅ Limit <b>{paket}</b> berhasil diperbarui!\n"
        f"Process Limit: {process_limit}\n"
        f"Daily Quota: {daily_quota}",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

# === CANCEL ===
@router.message(F.command == "cancel")
async def limit_cancel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Proses dibatalkan.", reply_markup=back_to_admin())