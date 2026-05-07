import base64
from aiogram import Bot

async def file_id_to_base64(bot: Bot, file_id: str) -> str:
    """
    Mengunduh gambar dari Telegram (pakai file_id) dan mengubahnya
    menjadi string Base64 yang siap dikirim ke API Magnific.
    """
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    base64_str = base64.b64encode(file_bytes.read()).decode("utf-8")
    return base64_str