from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from source.states.admin_apikey import AdminApiKeyState
from source.database.db import (
    get_api_keys, add_api_keys_bulk, delete_api_key,
    toggle_api_key, reset_api_keys
)
from config import ADMIN_ID

router = Router()

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

@router.callback_query(F.data == "apikey_manage")
async def apikey_manage_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    keys = await get_api_keys()
    lines = ["🔑 <b>Daftar API Key</b>\n"]
    if not keys:
        lines.append("(Belum ada API key)")

    builder = InlineKeyboardBuilder()
    for k in keys:
        status = "🟢" if k[2] else "🔴"
        masked_key = "..." + k[1][-4:] if len(k[1]) > 4 else "****"
        lines.append(f"{status} Key: {masked_key}")

        builder.button(text="Detail", callback_data=f"apikey_detail_{k[0]}")
        builder.button(
            text="Nonaktifkan" if k[2] else "Aktifkan",
            callback_data=f"apikey_toggle_{k[0]}"
        )
        builder.button(text="🗑️ Hapus", callback_data=f"apikey_delete_{k[0]}")

    builder.button(text="🔙 Kembali".center(25), callback_data="admin_set_api")
    builder.adjust(3)  # 3 tombol aksi per key, lalu tombol kembali

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("apikey_detail_"))
async def apikey_detail(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    key_id = int(callback.data.split("_")[2])
    keys = await get_api_keys()
    key_target = next((k for k in keys if k[0] == key_id), None)
    if not key_target:
        await callback.answer("Key tidak ditemukan.", show_alert=True)
        return

    await callback.message.edit_text(
        f"🔑 <b>Detail API Key</b>\n\n"
        f"Key: <code>{key_target[1]}</code>\n"
        f"Status: {'🟢 Aktif' if key_target[2] else '🔴 Nonaktif'}\n\n"
        f"⚠️ <i>Ini rahasia. Jangan bagikan ke siapa pun.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder(
            buttons=[[{"text": "🔙 Kembali ke Daftar", "callback_data": "apikey_manage"}]]
        ).as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("apikey_toggle_"))
async def apikey_toggle(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    key_id = int(callback.data.split("_")[2])
    id_target, new_state = await toggle_api_key(key_id)
    await callback.answer(f"Key {id_target} sekarang {'aktif' if new_state else 'nonaktif'}.", show_alert=True)
    await apikey_manage_list(callback)

@router.callback_query(F.data.startswith("apikey_delete_"))
async def apikey_delete(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    key_id = int(callback.data.split("_")[2])
    await delete_api_key(key_id)
    await callback.answer(f"Key {key_id} dihapus.", show_alert=True)
    await apikey_manage_list(callback)

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
        reply_markup=InlineKeyboardBuilder(
            buttons=[[{"text": "🔙 Kembali", "callback_data": "admin_set_api"}]]
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
            reply_markup=InlineKeyboardBuilder(
                buttons=[[{"text": "🔙 Kembali", "callback_data": "admin_set_api"}]]
            ).as_markup()
        )
        return

    count = await add_api_keys_bulk(keys)
    await state.clear()
    await message.answer(
        f"✅ {count} API key berhasil ditambahkan.",
        reply_markup=InlineKeyboardBuilder(
            buttons=[[{"text": "🔙 Kembali ke Setting API Key", "callback_data": "admin_set_api"}]]
        ).as_markup()
    )

@router.callback_query(F.data == "apikey_reset")
async def apikey_reset_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await state.set_state(AdminApiKeyState.reset_key)
    await callback.message.edit_text(
        "<b>⚠️ Reset API Key</b>\n\n"
        "Ini akan <b>menghapus semua API key</b> yang ada.\n"
        "Kirim daftar API key baru:\n\n"
        "<code>sk-xxxxxxxxxxxxxxxxxxxxxxxx1\n"
        "sk-xxxxxxxxxxxxxxxxxxxxxxxx2</code>\n\n"
        "Satu baris untuk satu key.\n"
        "Ketik /cancel untuk batal.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder(
            buttons=[[{"text": "🔙 Kembali", "callback_data": "admin_set_api"}]]
        ).as_markup()
    )
    await callback.answer()

@router.message(AdminApiKeyState.reset_key)
async def apikey_reset_process(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    lines = message.text.strip().split("\n")
    keys = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

    if not keys:
        await message.answer(
            "Tidak ada API key valid untuk di-reset.",
            reply_markup=InlineKeyboardBuilder(
                buttons=[[{"text": "🔙 Kembali", "callback_data": "admin_set_api"}]]
            ).as_markup()
        )
        return

    count = await reset_api_keys(keys)
    await state.clear()
    await message.answer(
        f"🔄 {count} API key baru berhasil dimasukkan (data lama terhapus).",
        reply_markup=InlineKeyboardBuilder(
            buttons=[[{"text": "🔙 Kembali ke Setting API Key", "callback_data": "admin_set_api"}]]
        ).as_markup()
    )

@router.message(F.command == "cancel")
async def apikey_cancel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Proses dibatalkan.")