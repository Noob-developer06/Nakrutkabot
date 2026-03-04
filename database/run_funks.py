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
                "SELECT id, api_order_id, user_id, service_id, price, status, quantity, link FROM orders "
                "WHERE status IN ('Pending', 'Processing', 'In progress')"
            )
            orders = await cursor.fetchall()
            await cursor.close()

            if not orders:
                await bot.send_message(ADMIN, "edit_order: Hech qanday faol buyurtma topilmadi (Pending/Processing/In progress)")
                return False

            await bot.send_message(ADMIN, f"edit_order: {len(orders)} ta faol buyurtma topildi")

            for order in orders:
                order_id, api_order_id, user_id, service_id, price, old_status, quantity, link = order

                await bot.send_message(ADMIN, f"Buyurtma #{order_id} | old_status: {old_status} | price tip: {type(price)} | quantity tip: {type(quantity)}")

                # Tip konvertatsiyasi
                try:
                    price_f = float(price)
                    quantity_i = int(quantity)
                except (TypeError, ValueError) as ex:
                    await bot.send_message(ADMIN, f"#{order_id} TIP XATOSI: {ex}\nprice={price!r}\nquantity={quantity!r}")
                    continue

                cursor_service = await db.execute(
                    "SELECT api_id FROM services WHERE id = ?",
                    (service_id,)
                )
                service = await cursor_service.fetchone()
                await cursor_service.close()

                if not service:
                    await bot.send_message(ADMIN, f"#{order_id} xizmati topilmadi (service_id={service_id})")
                    continue

                api_id = service[0]

                status_data = await get_status(api_id, api_order_id)
                if not status_data or "error" in status_data:
                    await bot.send_message(ADMIN, f"#{order_id} API xatosi: {status_data}")
                    continue

                new_status = status_data.get("status")
                if not new_status:
                    await bot.send_message(ADMIN, f"#{order_id} status bo'sh keldi: {status_data}")
                    continue

                await bot.send_message(ADMIN, f"#{order_id} → old: {old_status} | new: {new_status!r}")

                if new_status == old_status:
                    continue

                # Statusni yangilash
                await db.execute(
                    "UPDATE orders SET status = ? WHERE id = ?",
                    (new_status, order_id)
                )

                if new_status == "Completed":
                    await db.execute(
                        "UPDATE orders SET completed_at = datetime('now', '+5 hours') WHERE id = ?",
                        (order_id,)
                    )
                    await bot.send_message(
                        user_id,
                        msg10.format(order_id=order_id, link=link, quantity=quantity_i),
                        disable_web_page_preview=True
                    )

                elif new_status == "Canceled":
                    paid_amount = int(price_f)

                    await bot.send_message(
                        user_id,
                        msg11.format(
                            order_id=order_id,
                            link=link,
                            quantity=quantity_i,
                            paid_amount=paid_amount
                        )
                    )

                    if paid_amount > 0:
                        await db.execute(
                            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                            (paid_amount, user_id)
                        )

                elif new_status.lower() in ("partial", "partially"):  # case-insensitive + turli variantlar
                    await bot.send_message(ADMIN, f"PARTIAL (yoki shunga o'xshash) holatga kirdi → #{order_id}")

                    remains_raw = status_data.get("remains", "0")
                    try:
                        remains = int(remains_raw)
                    except Exception as ex:
                        await bot.send_message(ADMIN, f"#{order_id} remains konvert xatosi: {ex} | raw={remains_raw!r}")
                        remains = 0

                    await bot.send_message(ADMIN, f"#{order_id} remains tipi: {type(remains)}, qiymati: {remains}")

                    if quantity_i > 0 and remains > 0:
                        try:
                            return_price = int(price_f * 100 * remains / quantity_i)
                            await bot.send_message(ADMIN, f"#{order_id} qaytariladigan summa: {return_price}")

                            if return_price > 0:
                                await db.execute(
                                    "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                                    (return_price, user_id)
                                )
                        except Exception as calc_ex:
                            await bot.send_message(ADMIN, f"#{order_id} hisoblash xatosi: {calc_ex}")

            await db.commit()
            return True

    except Exception as e:
        await send_error(e)
        await bot.send_message(ADMIN, f"edit_order umumiy xato: {type(e).__name__} → {str(e)}")
        return False


async def order_updater():
    while True:
        try:
            await edit_order()
        except Exception as e:
            await send_error(e)
            # agar xohlasangiz shu yerga ham admin habar qo'shsa bo'ladi

        await asyncio.sleep(update_status_time)