from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from source.states.admin_apikey import AdminApiKeyState
from source.database.db import (
    get_api_keys, add_api_keys_bulk, delete_api_key,
    toggle_api_key, reset_api_keys
)
from source.config import ADMIN_ID

router = Router()

KEYS_PER_PAGE = 10

# ------------------------------------------------------------
# MENU UTAMA SETTING API KEY
# ------------------------------------------------------------
@router.callback_query(F.data == "admin_set_api")
async def admsetapikey_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Manajemen API Key".center(25), callback_data="apikey_manage")
    builder.button(text="➕ Tambah API Key".center(25), callback_data="apikey_add")
    builder.button(text="🔄 Reset API Key".center(25), callback_data="apikey_reset")
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_panel")
    builder.adjust(2)

    await callback.message.edit_text(
        "<b>🔑 Setting API Key</b>\nSilakan pilih menu:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# ------------------------------------------------------------
# MANAJEMEN API KEY (DAFTAR) - Halaman pertama
# ------------------------------------------------------------
@router.callback_query(F.data == "apikey_manage")
async def apikey_manage_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    await show_apikey_page(callback, page=1)

# ------------------------------------------------------------
# NAVIGASI HALAMAN API KEY
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("apikey_page_"))
async def apikey_page_handler(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    page = int(callback.data.split("_")[-1])
    await show_apikey_page(callback, page)

async def show_apikey_page(callback: types.CallbackQuery, page: int):
    keys = await get_api_keys()
    total_pages = max(1, (len(keys) + KEYS_PER_PAGE - 1) // KEYS_PER_PAGE)
    start = (page - 1) * KEYS_PER_PAGE
    end = start + KEYS_PER_PAGE
    page_keys = keys[start:end]

    lines = [f"🔑 <b>Manajemen API Key ({page}/{total_pages})</b>"]

    keyboard_rows = []

    if not page_keys:
        lines.append("(Belum ada API key)")
    else:
        for k in page_keys:
            key_id = k["id"]
            masked_key = "..." + k["key"][-18:] if len(k["key"]) > 18 else "****"
            is_active = k["is_active"]

            row = [
                InlineKeyboardButton(text=masked_key, callback_data=f"apikey_detail_{key_id}"),
                InlineKeyboardButton(text="🔍", callback_data=f"apikey_info_{key_id}"),
                InlineKeyboardButton(text="🟢" if is_active else "🔴", callback_data=f"apikey_toggle_{key_id}"),
                InlineKeyboardButton(text="🗑️", callback_data=f"apikey_delete_{key_id}"),
            ]
            keyboard_rows.append(row)

    # Navigasi
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Sebelumnya", callback_data=f"apikey_page_{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="➡️ Selanjutnya", callback_data=f"apikey_page_{page+1}"))
    if nav_row:
        keyboard_rows.append(nav_row)

    # Kembali
    back_row = [InlineKeyboardButton(text="🔙 Kembali", callback_data="admin_set_api")]
    keyboard_rows.append(back_row)

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=markup
    )
    await callback.answer()

# ------------------------------------------------------------
# DETAIL API KEY
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("apikey_detail_"))
async def apikey_detail(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    key_id = int(callback.data.split("_")[2])
    keys = await get_api_keys()
    key_target = next((k for k in keys if k["id"] == key_id), None)
    if not key_target:
        await callback.answer("Key tidak ditemukan.", show_alert=True)
        return

    await callback.message.edit_text(
        f"🔑 <b>Detail API Key</b>\n\n"
        f"Key: <code>{key_target['key']}</code>\n"
        f"Status: {'🟢 Aktif' if key_target['is_active'] else '🔴 Nonaktif'}\n\n"
        f"⚠️ <i>Ini rahasia. Jangan bagikan ke siapa pun.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Kembali ke Manajemen", callback_data="apikey_manage"
        ).as_markup()
    )
    await callback.answer()

# ------------------------------------------------------------
# TOGGLE AKTIF/NONAKTIF
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("apikey_toggle_"))
async def apikey_toggle(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    key_id = int(callback.data.split("_")[2])
    id_target, new_state = await toggle_api_key(key_id)
    await callback.answer(
        f"Key {id_target} sekarang {'aktif' if new_state else 'nonaktif'}.",
        show_alert=True
    )
    # Kembali ke halaman yang sama (default halaman 1)
    await show_apikey_page(callback, page=1)

# ------------------------------------------------------------
# HAPUS API KEY
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("apikey_delete_"))
async def apikey_delete(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    key_id = int(callback.data.split("_")[2])
    await delete_api_key(key_id)
    await callback.answer(f"Key {key_id} dihapus.", show_alert=True)
    await show_apikey_page(callback, page=1)

# ------------------------------------------------------------
# TAMBAH API KEY (FSM)
# ------------------------------------------------------------
@router.callback_query(F.data == "apikey_add")
async def apikey_add_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await state.set_state(AdminApiKeyState.tambah_key)
    await callback.message.edit_text(
        "<b>Tambah API Key</b>\n\n"
        "Kirim satu atau lebih API key:\n\n"
        "<code>sk-xxxxxxxxxxxxxxxxxxxxxxxx1\n"
        "sk-xxxxxxxxxxxxxxxxxxxxxxxx2</code>\n\n"
        "Satu baris untuk satu key.\n"
        "Ketik /cancel untuk batal.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Kembali", callback_data="admin_set_api"
        ).as_markup()
    )
    await callback.answer()

@router.message(AdminApiKeyState.tambah_key)
async def apikey_add_process(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    lines = message.text.strip().split("\n")
    keys = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

    if not keys:
        await message.answer(
            "Tidak ada API key valid yang dikirim.",
            reply_markup=InlineKeyboardBuilder().button(
                text="🔙 Kembali", callback_data="admin_set_api"
            ).as_markup()
        )
        return

    count = await add_api_keys_bulk(keys)
    await state.clear()
    await message.answer(
        f"✅ {count} API key berhasil ditambahkan.",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Kembali ke Setting API Key", callback_data="admin_set_api"
        ).as_markup()
    )

# ------------------------------------------------------------
# RESET API KEY (KONFIRMASI YES / NO)
# ------------------------------------------------------------
@router.callback_query(F.data == "apikey_reset")
async def apikey_reset_prompt(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ya", callback_data="apikey_reset_confirm")
    builder.button(text="❌ Tidak", callback_data="admin_set_api")
    builder.adjust(2)

    await callback.message.edit_text(
        "<b>⚠️ Anda yakin ingin mereset semua API key?</b>\n"
        "Semua key yang tersimpan akan dihapus permanen.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "apikey_reset_confirm")
async def apikey_reset_confirm(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await reset_api_keys()
    await callback.message.edit_text(
        "🔄 Semua API key berhasil dihapus.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Kembali ke Setting API Key", callback_data="admin_set_api"
        ).as_markup()
    )
    await callback.answer()

# ------------------------------------------------------------
# CANCEL
# ------------------------------------------------------------
@router.message(F.command == "cancel")
async def apikey_cancel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Proses dibatalkan.")