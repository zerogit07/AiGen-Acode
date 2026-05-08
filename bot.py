import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

# --- Router dari handler umum ---
from source.handlers.start import router as start_router
from source.handlers.status import router as status_router
from source.handlers.daftar import router as daftar_router

# --- Router dari frontend_admin ---
from source.handlers.frontend_admin.admin import router as admin_router
from source.handlers.frontend_admin.admsetpage import router as admsetpage_router
from source.handlers.frontend_admin.admapprove import router as admapprove_router
from source.handlers.frontend_admin.admsetstat import router as admsetstat_router
from source.handlers.frontend_admin.admmember import router as admmember_router
from source.handlers.frontend_admin.admsetmsg import router as admsetmsg_router
from source.handlers.frontend_admin.admsetlimit import router as admsetlimit_router
from source.handlers.frontend_admin.admsetdata import router as admsetdata_router
from source.handlers.frontend_admin.admsetmodel import router as admsetmodel_router
from source.handlers.frontend_admin.admsetapikey import router as admsetapikey_router
from source.handlers.frontend_admin.admsetproxy import router as admsetproxy_router

# --- Router dari frontend_models ---
from source.handlers.frontend_models.kling_2_1 import router as kling_21_router

# --- Database ---
from source.database.db import init_db, migrate_json_to_db

# --- Services ---
from source.services.job_manager import JobManager

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()



# Daftarkan semua router
dp.include_router(start_router)
dp.include_router(status_router)
dp.include_router(daftar_router)
dp.include_router(admin_router)
dp.include_router(admsetpage_router)
dp.include_router(admapprove_router)
dp.include_router(admsetstat_router)
dp.include_router(admmember_router)
dp.include_router(admsetmsg_router)
dp.include_router(admsetlimit_router)
dp.include_router(admsetdata_router)
dp.include_router(admsetmodel_router)
dp.include_router(admsetapikey_router)
dp.include_router(admsetproxy_router)
dp.include_router(kling_21_router)



async def main():
    await init_db()
    await migrate_json_to_db()
    
    # Inisialisasi JobManager agar siap menerima job
    await JobManager().initialize(bot)
    
    print("🤖 Bot berjalan...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
    
    
    