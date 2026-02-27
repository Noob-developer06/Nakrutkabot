import aiosqlite
import asyncio

from api_requests import get_status
from helper import send_error
from texts.user import msg10, msg11
from loader import bot
from config import update_status_time, DB_PATH


async def edit_order():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, user_id, api_order_id, service_id, price, quantity, link
            FROM orders
            WHERE status IN ('Pending', 'Processing', 'In Progress')
        """)
        orders = await cursor.fetchall()

        for order in orders:
            order_id, user_id, api_order_id, service_id, price, quantity, link = order

            # Service ma'lumotini olish to'g'ridan-to'g'ri query bilan
            service_cursor = await db.execute("SELECT api_id FROM services WHERE id = ?", (service_id,))
            service = await service_cursor.fetchone()
            if not service:
                continue
            api_id = service[0]

            status_data = await get_status(api_id, api_order_id)
            if not status_data:
                continue

            status = status_data.get("status", "Pending")
            await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

            if status == "Completed":
                await db.execute(
                    "UPDATE orders SET completed_at = datetime('now', '+5 hours') WHERE id = ?",
                    (order_id,)
                )
                await bot.send_message(
                    chat_id=user_id,
                    text=msg10.format(
                        order_id=order_id,
                        link=link,
                        quantity=quantity
                    )
                )

            elif status == "Canceled":
                # User mavjudligini tekshirish
                user_cursor = await db.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
                user = await user_cursor.fetchone()
                if user:
                    await db.execute(
                        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                        (price, user_id)
                    )
                    await bot.send_message(
                        chat_id=user_id,
                        text=msg11.format(
                            order_id=order_id,
                            link=link,
                            quantity=quantity,
                            paid_amount=price
                        )
                    )

            elif status == "Partial":
                user_cursor = await db.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
                user = await user_cursor.fetchone()
                if user:
                    remains = status_data.get("remains", 0)
                    give_price = int(price * (quantity - remains) / quantity)
                    await db.execute(
                        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                        (give_price, user_id)
                    )

        # Commitni bitta joyda qilamiz
        await db.commit()


async def order_updater():
    while True:
        try:
            await edit_order()
        except Exception as e:
            await send_error(e)
        await asyncio.sleep(update_status_time)