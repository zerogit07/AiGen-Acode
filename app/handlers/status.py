from aiogram import Router, types
from aiogram.filters import Command
from config import ADMIN_ID
from app.utils.gambar_page import get_member

router = Router()

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    user_id = message.from_user.id

    # Admin
    if user_id == ADMIN_ID:
        status = "Admin"
        expired = "Unlimited"
    else:
        paket = get_member(user_id)
        if paket:
            status = f"Member {paket}"
            expired = "-"   # nanti diganti dari database
        else:
            status = "Non Member"
            expired = "-"

    text = (
        f"📊 <b>Status Akun</b>\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"🏷️ Status: {status}\n"
        f"⏳ Expired: {expired}"
    )
    await message.answer(text, parse_mode="HTML")