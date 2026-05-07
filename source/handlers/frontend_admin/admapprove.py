from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from source.states.daftar_state import DaftarState
from source.utils.gambar_page import set_member
from config import ADMIN_ID

router = Router()

# === SETUJUI ===
@router.callback_query(F.data.startswith("approve_"))
async def adm_approve(callback: types.CallbackQuery, bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    _, user_id, paket = callback.data.split("_")
    user_id = int(user_id)

    set_member(user_id, paket)

    await bot.send_message(
        chat_id=user_id,
        text=f"🎉 Selamat! Pendaftaran <b>{paket}</b> kamu disetujui.\nSekarang kamu bisa menggunakan semua fitur AiGen Studio.",
        parse_mode="HTML"
    )

    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n✅ <b>[DISETUJUI]</b>",
        parse_mode="HTML"
    )
    await callback.answer("Disetujui.")

# === TOLAK (minta alasan) ===
@router.callback_query(F.data.startswith("reject_"))
async def adm_reject_minta_alasan(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    _, user_id, paket = callback.data.split("_")
    await state.set_state(DaftarState.menunggu_alasan)
    await state.update_data(user_id=int(user_id), paket=paket, msg_id=callback.message.message_id)
    await callback.message.answer("📝 Kirim alasan penolakan sekarang.")
    await callback.answer()

@router.message(DaftarState.menunggu_alasan)
async def adm_alasan_diterima(message: types.Message, state: FSMContext, bot):
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    user_id = data["user_id"]
    paket = data["paket"]
    msg_id = data["msg_id"]
    alasan = message.text

    await bot.send_message(
        chat_id=user_id,
        text=f"❌ Pendaftaran <b>{paket}</b> kamu ditolak.\nAlasan: {alasan}",
        parse_mode="HTML"
    )

    await bot.edit_message_caption(
        chat_id=ADMIN_ID,
        message_id=msg_id,
        caption=f"{message.reply_to_message.caption}\n\n❌ <b>[DITOLAK]</b> - {alasan}",
        parse_mode="HTML"
    )

    await state.clear()
    await message.answer("Alasan sudah dikirim ke user.")