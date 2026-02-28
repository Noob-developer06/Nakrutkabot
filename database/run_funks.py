import aiosqlite
import asyncio

from api_requests import get_status
from helper import send_error
from texts.user import msg10, msg11
from loader import bot
from config import update_status_time, DB_PATH


async def edit_order():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, api_order_id, user_id, service_id, price, status, quantity, link FROM orders "
                "WHERE status IN ('Pending', 'Processing', 'In progress')"
            )
            orders = await cursor.fetchall()
            await cursor.close()
            if not orders:
                return False

            for order in orders:
                order_id, api_order_id, user_id, service_id, price, old_status, quantity, link = order
                cursor_service = await db.execute("SELECT api_id FROM services WHERE id = ?", (service_id,))
                service = await cursor_service.fetchone()
                await cursor_service.close()
                if not service:
                    continue
                api_id = service[0]

                status = await get_status(api_id, api_order_id)
                if "error" in status:
                    continue

                new_status = status.get("status")
                if new_status == old_status:
                    continue

                await db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))

                if new_status == "Completed":
                    await db.execute("UPDATE orders SET completed_at = datetime('now', '+5 hours') WHERE id = ?", (order_id,))
                    await bot.send_message(user_id, msg10.format(order_id=order_id, link=link, quantity=quantity), disable_web_page_preview=True)

                if new_status == "Canceled":
                    paid_amount = price or 0
                    await bot.send_message(user_id, msg11.format(order_id=order_id, link=link, quantity=quantity, paid_amount=paid_amount))
                    if paid_amount != 0:
                        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (price, user_id))

                if new_status == "Partial":
                    remains = status.get("remains", 0)
                    return_price = price * 100 * remains / quantity
                    if return_price != 0:
                        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (return_price, user_id))

            await db.commit()
            return True

    except Exception as e:
        await send_error(e)



async def order_updater():
    while True:
        try:
            await edit_order()  # Siz yozgan optimizatsiyalangan funksiya
        except Exception as e:
            await send_error(e)  # xatolarni loglash
        await asyncio.sleep(update_status_time)