#main.py


import asyncio
import logging

from loader import bot, dp
from middlewares import PrivateFloodMiddleware


from database.requests import create_table
from database.run_funk import order_updater
from handlers.user import user_router
from handlers.admin import admin_router
# Log sozlamalari
logging.basicConfig(level=logging.INFO)


#dp.message.middleware(PrivateFloodMiddleware())

dp.include_routers(admin_router)
dp.include_routers(user_router)

async def main():
    await create_table()
    asyncio.create_task(order_updater())
    
    logging.info("Bot ishga tushdi")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logging.info("Bot ishini to‘xtatdi")

if __name__ == "__main__":
    asyncio.run(main())
