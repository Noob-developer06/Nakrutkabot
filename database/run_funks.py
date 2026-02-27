import aiosqlite
import asyncio

from api_requests import get_status
from database.requests import get_service, get_user, add_balance
from helper import send_error
from texts.user import msg10, msg11
from loader import bot
from config import update_status_time, DB_PATH


async def edit_order():
    async with aiosqlite.connect(DB_PATH, timeout=10) as db:

        cursor = await db.execute("""
            SELECT id, user_id, api_order_id, service_id, price, quantity, link
            FROM orders
            WHERE status IN ('Pending', 'Processing', 'In Progress')
        """)
        orders = await cursor.fetchall()

        for order in orders:
            order_id, user_id, api_order_id, service_id, price, quantity, link = order

            service = await get_service(service_id)
            if not service:
                continue

            api_id = service["api_id"]
            status_data = await get_status(api_id, api_order_id)
            if not status_data:
                continue

            status = status_data.get("status", "Pending")

            await db.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id)
            )

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
                    ),
                    disable_web_page_preview=True,
                    parse_mode="HTML"
                )

            elif status == "Canceled":
                await add_balance(user_id, price, db=db)

                await bot.send_message(
                    chat_id=user_id,
                    text=msg11.format(
                        order_id=order_id,
                        link=link,
                        quantity=quantity,
                        paid_amount=price
                    ),
                    disable_web_page_preview=True,
                    parse_mode="HTML"
                )

            elif status == "Partial":
                remains = status_data.get("remains", 0)
                give_price = int(price * (quantity - remains) / quantity)

                await add_balance(user_id, give_price, db=db)

        await db.commit()



async def order_updater():
    while True:
        try:
            await edit_order()  # Siz yozgan optimizatsiyalangan funksiya
        except Exception as e:
            await send_error(e)  # xatolarni loglash
        await asyncio.sleep(update_status_time)
