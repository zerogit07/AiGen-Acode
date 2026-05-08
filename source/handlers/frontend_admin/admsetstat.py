from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from source.utils.gambar_page import ambil_semua_member, ambil_semua_nonmember
from source.config import ADMIN_ID

router = Router()

@router.callback_query(F.data == "admin_statistic")
async def admsetstat_show(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    members = ambil_semua_member()
    nonmembers = ambil_semua_nonmember()

    # Hitung
    lite = sum(1 for p in members.values() if p == "Lite")
    pro = sum(1 for p in members.values() if p == "Pro")
    ultra = sum(1 for p in members.values() if p == "Ultra")
    total_member = lite + pro + ultra
    total_nonmember = len(nonmembers)

    text = (
        "📊 <b>Statistik</b>\n"
        f"Lite: {lite}\n"
        f"Pro: {pro}\n"
        f"Ultra: {ultra}\n"
        f"Non member: {total_nonmember}\n"
        f"Total member: {total_member}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_panel")
    builder.adjust(1)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()