import aiosqlite
import asyncio

from api_requests import get_status
from helper import send_error
from texts.user import msg10, msg11
from loader import bot
from config import update_status_time, DB_PATH, ADMIN


async def edit_order():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                """
                SELECT id, api_order_id, user_id, service_id, price, status, quantity, link 
                FROM orders 
                WHERE status IN ('Pending', 'Processing', 'In progress')
                """
            )
            orders = await cursor.fetchall()
            await cursor.close()

            if not orders:
                return False

            # Faqat muhim holatlarda admin'ga xabar yuborishni kamaytirdik
            # await bot.send_message(ADMIN, f"edit_order: {len(orders)} ta faol buyurtma topildi")

            for order in orders:
                order_id, api_order_id, user_id, service_id, price, old_status, quantity, link = order

                # Tip konvertatsiyasi – eng muhim qism
                try:
                    price_f = float(price or 0)
                    quantity_i = int(float(quantity or 0))  # string yoki float bo'lsa ham ishlaydi
                except (TypeError, ValueError):
                    # await bot.send_message(ADMIN, f"#{order_id} TIP XATOSI: price={price!r}, quantity={quantity!r}")
                    continue

                cursor_service = await db.execute(
                    "SELECT api_id FROM services WHERE id = ?",
                    (service_id,)
                )
                service = await cursor_service.fetchone()
                await cursor_service.close()

                if not service:
                    continue

                api_id = service[0]

                status_data = await get_status(api_id, api_order_id)
                if not status_data or "error" in status_data:
                    continue

                new_status = status_data.get("status")
                if not new_status or new_status == old_status:
                    continue

                # Statusni yangilash
                await db.execute(
                    "UPDATE orders SET status = ? WHERE id = ?",
                    (new_status, order_id)
                )

                new_status_lower = new_status.lower()

                if new_status_lower == "completed":
                    await db.execute(
                        "UPDATE orders SET completed_at = datetime('now', '+5 hours') WHERE id = ?",
                        (order_id,)
                    )
                    try:
                        await bot.send_message(
                            user_id,
                            msg10.format(order_id=order_id, link=link, quantity=quantity_i),
                            disable_web_page_preview=True
                        )
                    except:
                        pass  # foydalanuvchi bloklagan bo'lishi mumkin

                elif new_status_lower in ("canceled", "cancelled"):
                    paid_amount = int(price_f)

                    try:
                        await bot.send_message(
                            user_id,
                            msg11.format(
                                order_id=order_id,
                                link=link,
                                quantity=quantity_i,
                                paid_amount=paid_amount
                            )
                        )
                    except:
                        pass

                    if paid_amount > 0:
                        await db.execute(
                            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                            (paid_amount, user_id)
                        )

                elif "partial" in new_status_lower:
                    # Partial holati (turli yozilishlar uchun)
                    remains_raw = status_data.get("remains", "0")
                    try:
                        remains = int(remains_raw)
                    except:
                        remains = 0

                    if quantity_i > 0 and remains > 0:
                        try:
                            refund = int(price_f * 100 * remains / quantity_i)
                            if refund > 0:
                                await db.execute(
                                    "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                                    (refund, user_id)
                                )
                                # Faqat muhim holatda admin'ga xabar
                                # await bot.send_message(ADMIN, f"Partial refund #{order_id}: {refund}")
                        except Exception as calc_error:
                            await send_error(calc_error)
                            # await bot.send_message(ADMIN, f"#{order_id} partial hisob xatosi")

            await db.commit()
            return True

    except Exception as e:
        await send_error(e)
        try:
            # Xavfsiz xabar – < > belgilarini almashtirish orqali parse xatosini oldini olish
            safe_msg = f"edit_order umumiy xato: {type(e).__name__} → {str(e).replace('<','<').replace('>','>')}"
            await bot.send_message(ADMIN, safe_msg)
        except:
            pass  # agar telegram ham xato bersa, jim bo'lamiz
        return False


async def order_updater():
    while True:
        try:
            await edit_order()
        except Exception as e:
            await send_error(e)

        await asyncio.sleep(update_status_time)