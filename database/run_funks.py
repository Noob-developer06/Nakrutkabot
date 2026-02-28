import aiosqlite
import asyncio

from api_requests import get_status
from database.requests import get_service, add_balance
from helper import send_error
from texts.user import msg10, msg11
from loader import bot
from config import update_status_time, DB_PATH


async def edit_order():
    # 1️⃣ Faqat orderlarni olib chiqamiz
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, user_id, api_order_id, service_id, price, quantity, link
            FROM orders
            WHERE status IN ('Pending', 'Processing', 'In Progress')
        """)
        orders = await cursor.fetchall()

    # 2️⃣ Endi DB yopilgan
    for order in orders:
        order_id, user_id, api_order_id, service_id, price, quantity, link = order

        service = await get_service(service_id, db)
        if not service:
            continue

        status_data = await get_status(service["api_id"], api_order_id)
        if not status_data:
            continue

        status = status_data.get("status", "Pending")

        # 3️⃣ Faqat update payti DB ochiladi
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id)
            )
            await db.commit()

        # 4️⃣ Message va balance update DB dan tashqarida
        if status == "Completed":
            await bot.send_message(
                user_id,
                msg10.format(order_id=order_id, link=link, quantity=quantity),
                disable_web_page_preview=True
            )

        elif status == "Canceled":
            await add_balance(user_id, price, db)
            await bot.send_message(
                user_id,
                msg11.format(order_id=order_id, link=link, quantity=quantity, paid_amount=price),
                disable_web_page_preview=True
            )


async def order_updater():
    while True:
        try:
            await edit_order()  # Siz yozgan optimizatsiyalangan funksiya
        except Exception as e:
            await send_error(e)  # xatolarni loglash
        await asyncio.sleep(update_status_time)