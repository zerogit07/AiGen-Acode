from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from source.states.adminmsg import AdminMsgState
from source.utils.gambar_page import ambil_semua_member, ambil_semua_nonmember
from source.config import ADMIN_ID

router = Router()

# === MENU UTAMA SETTING MESSAGE ===
@router.callback_query(F.data == "admin_set_message")
async def admsetmsg_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Broadcast".center(25), callback_data="msg_broadcast")
    builder.button(text="📩 Privat Message".center(25), callback_data="msg_privat")
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_panel")
    builder.adjust(2)

    await callback.message.edit_text(
        "<b>💬 Setting Message</b>\nPilih jenis pesan yang ingin dikirim.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ============================================================
# BROADCAST
# ============================================================
@router.callback_query(F.data == "msg_broadcast")
async def broadcast_pilih_target(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await state.set_state(AdminMsgState.pilih_target)

    builder = InlineKeyboardBuilder()
    builder.button(text="Lite", callback_data="target_Lite")
    builder.button(text="Pro", callback_data="target_Pro")
    builder.button(text="Ultra", callback_data="target_Ultra")
    builder.button(text="Non Member", callback_data="target_Nonmember")
    builder.button(text="Semua (Member + Non Member)", callback_data="target_All")
    builder.button(text="🔙 Kembali", callback_data="admin_set_message")
    builder.adjust(2)

    await callback.message.edit_text(
        "Pilih target broadcast:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(AdminMsgState.pilih_target, F.data.startswith("target_"))
async def broadcast_tulis_pesan(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    target = callback.data.replace("target_", "")
    await state.update_data(target=target)
    await state.set_state(AdminMsgState.tulis_pesan)

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali", callback_data="admin_set_message")
    builder.adjust(1)

    await callback.message.edit_text(
        f"Target: <b>{target}</b>\n\nKetik pesan yang ingin dikirim.\nGunakan /cancel untuk batal.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.message(AdminMsgState.tulis_pesan)
async def broadcast_konfirmasi(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    pesan = message.text.strip()
    if not pesan:
        await message.answer("Pesan tidak boleh kosong.")
        return

    data = await state.get_data()
    target = data["target"]

    await state.update_data(pesan=pesan)
    await state.set_state(AdminMsgState.konfirmasi)

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Kirim", callback_data="broadcast_send")
    builder.button(text="❌ Batal", callback_data="admin_set_message")
    builder.adjust(2)

    await message.answer(
        f"📋 <b>Preview Broadcast</b>\n"
        f"Target: {target}\n\n"
        f"<i>{pesan}</i>\n\n"
        f"Apakah yakin ingin mengirim?",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@router.callback_query(AdminMsgState.konfirmasi, F.data == "broadcast_send")
async def broadcast_kirim(callback: types.CallbackQuery, state: FSMContext, bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    data = await state.get_data()
    target = data["target"]
    pesan = data["pesan"]

    # Kumpulkan user ID berdasarkan target
    target_ids = []

    if target == "All":
        members = ambil_semua_member()
        target_ids.extend(members.keys())
        target_ids.extend(ambil_semua_nonmember())
    elif target == "Nonmember":
        target_ids = ambil_semua_nonmember()
    else:  # Lite, Pro, Ultra
        members = ambil_semua_member()
        target_ids = [uid for uid, p in members.items() if p == target]

    target_ids = list(set(int(uid) for uid in target_ids))  # Bersihkan duplikat

    sukses = 0
    gagal = 0
    for uid in target_ids:
        try:
            await bot.send_message(chat_id=uid, text=pesan, parse_mode="HTML")
            sukses += 1
        except Exception:
            gagal += 1

    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali", callback_data="admin_set_message")
    builder.adjust(1)

    await callback.message.edit_text(
        f"✅ <b>Broadcast selesai</b>\n"
        f"Target: {target}\n"
        f"Terkirim: {sukses}\n"
        f"Gagal: {gagal}",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ============================================================
# PRIVAT MESSAGE
# ============================================================
@router.callback_query(F.data == "msg_privat")
async def privat_input_userid(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await state.set_state(AdminMsgState.input_userid)

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali", callback_data="admin_set_message")
    builder.adjust(1)

    await callback.message.edit_text(
        "Masukkan User ID tujuan:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.message(AdminMsgState.input_userid)
async def privat_tulis_pesan(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("User ID harus berupa angka.")
        return

    await state.update_data(target_uid=user_id)
    await state.set_state(AdminMsgState.tulis_privat)

    await message.answer(
        f"Target: <code>{user_id}</code>\n\nKetik pesan yang ingin dikirim.",
        parse_mode="HTML"
    )


@router.message(AdminMsgState.tulis_privat)
async def privat_konfirmasi(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    pesan = message.text.strip()
    if not pesan:
        await message.answer("Pesan tidak boleh kosong.")
        return

    data = await state.get_data()
    user_id = data["target_uid"]

    await state.update_data(pesan=pesan)
    await state.set_state(AdminMsgState.konfirmasi_privat)

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Kirim", callback_data="privat_send")
    builder.button(text="❌ Batal", callback_data="admin_set_message")
    builder.adjust(2)

    await message.answer(
        f"📋 <b>Preview Privat Message</b>\n"
        f"Target: <code>{user_id}</code>\n\n"
        f"<i>{pesan}</i>\n\n"
        f"Apakah yakin ingin mengirim?",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@router.callback_query(AdminMsgState.konfirmasi_privat, F.data == "privat_send")
async def privat_kirim(callback: types.CallbackQuery, state: FSMContext, bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    data = await state.get_data()
    user_id = data["target_uid"]
    pesan = data["pesan"]

    try:
        await bot.send_message(chat_id=user_id, text=pesan, parse_mode="HTML")
        status = f"✅ Pesan berhasil dikirim ke user <code>{user_id}</code>."
    except Exception:
        status = f"❌ Gagal mengirim ke user <code>{user_id}</code>. Mungkin belum pernah chat bot."

    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali", callback_data="admin_set_message")
    builder.adjust(1)

    await callback.message.edit_text(
        status,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# === CANCEL ===
@router.message(F.command == "cancel")
async def msg_cancel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Proses dibatalkan.")