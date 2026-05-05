import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from app.handlers.start import router as start_router
from app.handlers.status import router as status_router
from app.handlers.admin import router as admin_router
from app.handlers.admsetpage import router as admsetpage_router
from app.handlers.daftar import router as daftar_router
from app.handlers.admapprove import router as admapprove_router
from app.handlers.admsetstat import router as admsetstat_router
from app.handlers.admmember import router as admmember_router
from app.handlers.admsetmsg import router as admsetmsg_router
from app.database.db import init_db, migrate_json_to_db


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(start_router)
dp.include_router(status_router)
dp.include_router(admin_router)
dp.include_router(admsetpage_router)
dp.include_router(daftar_router)
dp.include_router(admapprove_router)
dp.include_router(admsetstat_router)
dp.include_router(admmember_router)
dp.include_router(admsetmsg_router)



async def main():
    await init_db()
    await migrate_json_to_db()
    
    print("🤖 Bot berjalan...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())