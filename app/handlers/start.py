from aiogram import Router, types
from aiogram.filters import Command
from config import ADMIN_ID
from app.keyboards.inlinestart import menu_utama
from app.keyboards.inlinenonmember import nonmember_keyboard
from app.utils.gambar_page import ambil_gambar, ambil_deskripsi, get_member, catat_nonmember

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    # Admin
    if user_id == ADMIN_ID:
        await message.answer(
            "<b>🤖 Menu Utama</b>",
            parse_mode="HTML",
            reply_markup=await menu_utama(user_id=user_id, is_admin=True)
        )
        return

    # Member (Lite, Pro, Ultra)
    paket = get_member(user_id)
    if paket:
        await message.answer(
            "<b>🤖 Menu Utama</b>",
            parse_mode="HTML",
            reply_markup=await menu_utama(user_id=user_id, is_admin=False)
        )
        return

    # 3. Non‑member
    catat_nonmember(user_id)
    url_gambar = ambil_gambar("start_image")
    deskripsi = ambil_deskripsi("banner")
    if not deskripsi:
        deskripsi = "Maaf, kamu belum terdaftar.\nSilakan pilih paket pendaftaran di bawah ini:"

    if url_gambar:
        await message.answer_photo(
            photo=url_gambar,
            caption=deskripsi,
            reply_markup=nonmember_keyboard()
        )
    else:
        await message.answer(
            deskripsi,
            reply_markup=nonmember_keyboard()
        )