import aiosqlite
import asyncio

from api_requests import get_status
from database.requests import add_balance  # faqat add_balance qoladi
from helper import send_error
from texts.user import msg10, msg11
from loader import bot
from config import update_status_time, DB_PATH


async def edit_order():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, user_id, api_order_id, service_id, price, quantity, link, status
            FROM orders
            WHERE status IN ('Pending', 'Processing', 'In Progress')
        """)
        orders = await cursor.fetchall()

        for order in orders:
            order_id, user_id, api_order_id, service_id, price, quantity, link, current_status = order

            status_data = await get_status(service_id, api_order_id)
            if not status_data:
                continue

            new_status = status_data.get("status", "Pending")

            # 🔹 Agar status o‘zgarmagan bo‘lsa, update qilinmaydi
            if new_status == current_status:
                continue

            # 🔹 Order statusni yangilash
            await db.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (new_status, order_id)
            )

            # 🔹 Message va balance update
            if new_status == "Completed":
                await bot.send_message(
                    user_id,
                    msg10.format(order_id=order_id, link=link, quantity=quantity),
                    disable_web_page_preview=True
                )

            elif new_status == "Canceled":
                # 🔹 add_balance ni shu yerda chaqiramiz, db uzatiladi
                await add_balance(user_id, price, db)

                await bot.send_message(
                    user_id,
                    msg11.format(order_id=order_id, link=link, quantity=quantity, paid_amount=price),
                    disable_web_page_preview=True
                )

        # 🔹 Commit faqat oxirida
        await db.commit()


async def order_updater():
    while True:
        try:
            await edit_order()
        except Exception as e:
            await send_error(e)
        await asyncio.sleep(update_status_time)