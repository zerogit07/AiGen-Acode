from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from app.states.adminpage import AdminPageState
from app.utils.gambar_page import simpan_gambar
from config import ADMIN_ID

router = Router()

def tombol_kembali():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Kembali ke Admin Panel".center(25), callback_data="admin_panel")
    return b.as_markup()

@router.callback_query(F.data == "admin_set_page")
async def admsetpage_menu_utama(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="🖼️ Ubah Gambar Start".center(25), callback_data="admsetpage_start")
    b.button(text="🖼️ Ubah Gambar Menu".center(25), callback_data="admsetpage_menu")
    b.button(text="🔙 Kembali".center(25), callback_data="admin_panel")
    b.adjust(1)

    await callback.message.edit_text(
        "<b>📄 Halaman Setting</b>\nSilakan pilih gambar yang ingin diubah.",
        parse_mode="HTML",
        reply_markup=b.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "admsetpage_start")
async def admsetpage_mulai_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    await state.set_state(AdminPageState.menunggu_gambar_start)
    await callback.message.edit_text(
        "Kirim URL gambar untuk <b>halaman start (non‑member)</b>.\n"
        "Ketik /cancel untuk batal.",
        parse_mode="HTML",
        reply_markup=tombol_kembali()
    )
    await callback.answer()

@router.callback_query(F.data == "admsetpage_menu")
async def admsetpage_mulai_menu(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    await state.set_state(AdminPageState.menunggu_gambar_menu)
    await callback.message.edit_text(
        "Kirim URL gambar untuk <b>halaman menu</b>.",
        parse_mode="HTML",
        reply_markup=tombol_kembali()
    )
    await callback.answer()

@router.message(AdminPageState.menunggu_gambar_start)
async def admsetpage_simpan_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("URL harus diawali http/https.")
        return
    simpan_gambar("start_image", url)
    await state.clear()
    await message.answer("✅ Gambar halaman start berhasil disimpan!", reply_markup=tombol_kembali())

@router.message(AdminPageState.menunggu_gambar_menu)
async def admsetpage_simpan_menu(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("URL harus diawali http/https.")
        return
    simpan_gambar("menu_image", url)
    await state.clear()
    await message.answer("✅ Gambar halaman menu berhasil disimpan!", reply_markup=tombol_kembali())

@router.message(F.command == "cancel")
async def admsetpage_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Proses dibatalkan.")