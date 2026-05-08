from aiogram import Router, types
from aiogram.filters import Command
from source.config import ADMIN_ID
from source.keyboards.inlineadmin import admin_panel

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ <b>Akses ditolak</b>", parse_mode="HTML")
        return

    await message.answer(
        "<b>🔐 Admin Panel</b>",
        parse_mode="HTML",
        reply_markup=admin_panel()
    )