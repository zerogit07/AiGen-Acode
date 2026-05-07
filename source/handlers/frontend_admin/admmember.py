from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from source.states.member_state import MemberState
from source.utils.gambar_page import (
    ambil_semua_member, ambil_semua_nonmember,
    set_member, get_member, hapus_member, semua_member_urut
)
from config import ADMIN_ID

router = Router()
MEMBERS_PER_PAGE = 10

def back_to_setting_member():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali ke Setting Member".center(25), callback_data="admin_set_member")
    return builder.as_markup()

# === MAIN SETTING MEMBER ===
@router.callback_query(F.data == "admin_set_member")
async def admin_set_member(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    members = ambil_semua_member()
    nonmembers = ambil_semua_nonmember()

    lite = sum(1 for p in members.values() if p == "Lite")
    pro = sum(1 for p in members.values() if p == "Pro")
    ultra = sum(1 for p in members.values() if p == "Ultra")
    total_member = lite + pro + ultra
    total_nonmember = len(nonmembers)

    stat_text = (
        "📊 <b>Statistik</b>\n"
        f"Lite: {lite}\n"
        f"Pro: {pro}\n"
        f"Ultra: {ultra}\n"
        f"Non member: {total_nonmember}\n"
        f"Total member: {total_member}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Manajemen Member".center(25), callback_data="member_manage_0")
    builder.button(text="➕ Tambah Member".center(25), callback_data="member_add")
    builder.button(text="🔍 Cari Member".center(25), callback_data="member_search")
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_panel")
    builder.adjust(2)

    await callback.message.edit_text(
        stat_text + "\n\nPilih menu di bawah:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# === MANAJEMEN MEMBER (PAGINASI) ===
@router.callback_query(F.data.startswith("member_manage_"))
async def member_manage(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    page = int(callback.data.split("_")[-1])
    all_members = semua_member_urut()
    items = list(all_members.items())
    total_pages = (len(items) + MEMBERS_PER_PAGE - 1) // MEMBERS_PER_PAGE

    start = page * MEMBERS_PER_PAGE
    end = start + MEMBERS_PER_PAGE
    page_items = items[start:end]

    if not page_items:
        await callback.message.edit_text(
            "📋 Belum ada member.",
            reply_markup=back_to_setting_member()
        )
        await callback.answer()
        return

    lines = [f"📋 <b>Daftar Member (hal {page+1}/{total_pages})</b>\n"]
    for uid, paket in page_items:
        lines.append(f"🆔 <code>{uid}</code> — {paket}")

    text = "\n".join(lines)

    # --- KEYBOARD AKSI PER MEMBER (3 kolom) ---
    action_builder = InlineKeyboardBuilder()
    for uid, paket in page_items:
        action_builder.button(text=f"{uid} — {paket}", callback_data=f"detail_{uid}")
        action_builder.button(text="✏️ Ubah", callback_data=f"ubah_{uid}")
        action_builder.button(text="🗑️ Hapus", callback_data=f"hapus_{uid}")
    action_builder.adjust(3)

    # --- NAVIGASI HALAMAN ---
    nav_builder = InlineKeyboardBuilder()
    if page > 0:
        nav_builder.button(text="⬅️ Sebelumnya", callback_data=f"member_manage_{page-1}")
    if page < total_pages - 1:
        nav_builder.button(text="➡️ Selanjutnya", callback_data=f"member_manage_{page+1}")
    if page > 0 and page < total_pages - 1:
        nav_builder.adjust(2)
    else:
        nav_builder.adjust(1)

    # --- TOMBOL KEMBALI (full width) ---
    back_builder = InlineKeyboardBuilder()
    back_builder.button(text="🔙 Kembali ke Setting Member".center(25), callback_data="admin_set_member")
    back_builder.adjust(1)

    # Gabungkan: aksi → navigasi → kembali
    action_builder.attach(InlineKeyboardBuilder.from_markup(nav_builder.as_markup()))
    action_builder.attach(InlineKeyboardBuilder.from_markup(back_builder.as_markup()))

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=action_builder.as_markup()
    )
    await callback.answer()

# === DETAIL MEMBER ===
@router.callback_query(F.data.startswith("detail_"))
async def member_detail(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    user_id = callback.data.split("_")[1]
    paket = get_member(int(user_id))
    if not paket:
        await callback.answer("Member tidak ditemukan.", show_alert=True)
        return

    text = (
        f"🔍 <b>Detail Member</b>\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Paket: {paket}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_setting_member())
    await callback.answer()

# === UBAH PAKET ===
@router.callback_query(F.data.startswith("ubah_"))
async def member_ubah_pilih(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    user_id = callback.data.split("_")[1]
    await state.set_state(MemberState.ubah_paket)
    await state.update_data(user_id=user_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="Lite", callback_data="setpaket_Lite")
    builder.button(text="Pro", callback_data="setpaket_Pro")
    builder.button(text="Ultra", callback_data="setpaket_Ultra")
    builder.button(text="Non Member", callback_data="setpaket_Non")
    builder.button(text="Kembali", callback_data="admin_set_member")
    builder.adjust(2)

    await callback.message.edit_text(
        f"Pilih paket baru untuk user <code>{user_id}</code>:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("setpaket_"))
async def member_ubah_simpan(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    paket = callback.data.split("_")[1]
    data = await state.get_data()
    user_id = int(data["user_id"])

    if paket == "Non":
        hapus_member(user_id)
        try:
            await callback.bot.send_message(user_id, "❌ Status member kamu telah dicabut oleh admin.")
        except Exception:
            pass
        await callback.message.edit_text(
            f"User {user_id} telah dihapus dari member.",
            reply_markup=back_to_setting_member()
        )
    else:
        set_member(user_id, paket)
        try:
            await callback.bot.send_message(user_id, f"🎉 Admin telah mengubah paket kamu menjadi <b>{paket}</b>.")
        except Exception:
            pass
        await callback.message.edit_text(
            f"User {user_id} berhasil diubah ke {paket}.",
            reply_markup=back_to_setting_member()
        )

    await state.clear()
    await callback.answer()

# === HAPUS MEMBER ===
@router.callback_query(F.data.startswith("hapus_"))
async def member_hapus(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    user_id = int(callback.data.split("_")[1])
    hapus_member(user_id)
    try:
        await callback.bot.send_message(user_id, "❌ Status member kamu telah dicabut oleh admin.")
    except Exception:
        pass

    await callback.message.edit_text(
        f"User {user_id} telah dihapus dari member.",
        reply_markup=back_to_setting_member()
    )
    await callback.answer()

# === TAMBAH MEMBER ===
@router.callback_query(F.data == "member_add")
async def member_add(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await state.set_state(MemberState.pilih_paket)
    builder = InlineKeyboardBuilder()
    builder.button(text="Lite", callback_data="addpaket_Lite")
    builder.button(text="Pro", callback_data="addpaket_Pro")
    builder.button(text="Ultra", callback_data="addpaket_Ultra")
    builder.button(text="Kembali", callback_data="admin_set_member")
    builder.adjust(2)

    await callback.message.edit_text(
        "Pilih paket untuk member baru:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("addpaket_"))
async def member_add_paket(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    paket = callback.data.split("_")[1]
    await state.update_data(paket=paket)
    await state.set_state(MemberState.masukkan_userid)

    await callback.message.edit_text(
        f"Masukkan User ID untuk member <b>{paket}</b>:",
        parse_mode="HTML",
        reply_markup=back_to_setting_member()
    )
    await callback.answer()

@router.message(MemberState.masukkan_userid)
async def member_add_simpan(message: types.Message, state: FSMContext, bot):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("User ID harus berupa angka.", reply_markup=back_to_setting_member())
        return

    data = await state.get_data()
    paket = data["paket"]
    set_member(user_id, paket)

    try:
        await bot.send_message(user_id, f"🎉 Admin telah menambahkan kamu sebagai member <b>{paket}</b>.")
    except Exception:
        await message.answer("User tidak bisa dikirimi notifikasi (mungkin belum pernah chat bot).")

    await state.clear()
    await message.answer(
        f"✅ User {user_id} berhasil ditambahkan sebagai member {paket}.",
        reply_markup=back_to_setting_member()
    )

# === CARI MEMBER ===
@router.callback_query(F.data == "member_search")
async def member_search(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await state.set_state(MemberState.cari_userid)
    await callback.message.edit_text(
        "Masukkan User ID yang ingin dicari:",
        reply_markup=back_to_setting_member()
    )
    await callback.answer()

@router.message(MemberState.cari_userid)
async def member_search_result(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("User ID harus berupa angka.", reply_markup=back_to_setting_member())
        return

    paket = get_member(user_id)
    await state.clear()

    if not paket:
        await message.answer("🔍 Member tidak ditemukan.", reply_markup=back_to_setting_member())
        return

    text = (
        f"🔍 <b>Hasil Pencarian</b>\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Paket: {paket}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=back_to_setting_member())