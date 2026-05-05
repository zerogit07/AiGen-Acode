from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.states.adminpage import AdminPageState
from app.utils.gambar_page import simpan_gambar, simpan_deskripsi
from config import ADMIN_ID

router = Router()

def tombol_kembali_admin():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali ke Admin Panel".center(25), callback_data="admin_panel")
    return builder.as_markup()

# === MENU SETTING PAGE ===
@router.callback_query(F.data == "admin_set_page")
async def admsetpage_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🖼️ Ubah Banner".center(25), callback_data="admsetpage_banner")
    builder.button(text="💳 Ubah QRIS".center(25), callback_data="admsetpage_qris")
    builder.button(text="📝 Deskripsi Banner".center(25), callback_data="admsetpage_desc_banner")
    builder.button(text="📝 Deskripsi Lite".center(25), callback_data="admsetpage_desc_lite")
    builder.button(text="📝 Deskripsi Pro".center(25), callback_data="admsetpage_desc_pro")
    builder.button(text="📝 Deskripsi Ultra".center(25), callback_data="admsetpage_desc_ultra")
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_panel")
    builder.adjust(1)

    await callback.message.edit_text(
        "<b>📄 Halaman Setting</b>\nPilih pengaturan yang ingin diubah.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# === BANNER ===
@router.callback_query(F.data == "admsetpage_banner")
async def admsetpage_banner(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    await state.set_state(AdminPageState.menunggu_banner)
    await callback.message.edit_text(
        "Kirim URL gambar untuk <b>Banner</b>.",
        parse_mode="HTML",
        reply_markup=tombol_kembali_admin()
    )
    await callback.answer()

# === QRIS ===
@router.callback_query(F.data == "admsetpage_qris")
async def admsetpage_qris(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    await state.set_state(AdminPageState.menunggu_qris)
    await callback.message.edit_text(
        "Kirim URL gambar untuk <b>QRIS</b>.",
        parse_mode="HTML",
        reply_markup=tombol_kembali_admin()
    )
    await callback.answer()

# === DESKRIPSI ===
@router.callback_query(F.data.startswith("admsetpage_desc_"))
async def admsetpage_deskripsi(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    kunci = callback.data.replace("admsetpage_desc_", "")  # banner, lite, pro, ultra
    await state.set_state(AdminPageState.menunggu_deskripsi)
    await state.update_data(kunci_deskripsi=kunci)

    await callback.message.edit_text(
        f"Kirim teks deskripsi untuk <b>{kunci.capitalize()}</b>.\n"
        "Ketik /cancel untuk batal.",
        parse_mode="HTML",
        reply_markup=tombol_kembali_admin()
    )
    await callback.answer()

# === SIMPAN GAMBAR ===
@router.message(AdminPageState.menunggu_banner)
async def simpan_banner(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("URL harus diawali http/https.")
        return
    simpan_gambar("start_image", url)
    await state.clear()
    await message.answer("✅ Banner berhasil disimpan!", reply_markup=tombol_kembali_admin())

@router.message(AdminPageState.menunggu_qris)
async def simpan_qris(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("URL harus diawali http/https.")
        return
    simpan_gambar("qris", url)
    await state.clear()
    await message.answer("✅ QRIS berhasil disimpan!", reply_markup=tombol_kembali_admin())

# === SIMPAN DESKRIPSI ===
@router.message(AdminPageState.menunggu_deskripsi)
async def simpan_deskripsi_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    kunci = data.get("kunci_deskripsi")
    if not kunci:
        await state.clear()
        return

    teks = message.text.strip()
    simpan_deskripsi(kunci, teks)
    await state.clear()
    await message.answer(f"✅ Deskripsi <b>{kunci.capitalize()}</b> berhasil disimpan!", parse_mode="HTML",
                         reply_markup=tombol_kembali_admin())

# === CANCEL ===
@router.message(F.command == "cancel")
async def admsetpage_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Proses dibatalkan.", reply_markup=tombol_kembali_admin())