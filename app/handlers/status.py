from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    user_id = message.from_user.id
    # Data dummy dulu
    status = "Non Member"
    expired = "-"

    text = (
        f"📊 <b>Status Akun</b>\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"🏷️ Status: {status}\n"
        f"⏳ Expired: {expired}"
    )
    await message.answer(text, parse_mode="HTML")