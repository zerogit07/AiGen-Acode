import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from app.handlers.start import router as start_router
from app.handlers.status import router as status_router
from app.handlers.admin import router as admin_router
from app.handlers.admsetpage import router as admsetpage_router


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(start_router)
dp.include_router(status_router)
dp.include_router(admin_router)
dp.include_router(admsetpage_router)

async def main():
    print("🤖 Bot berjalan...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())