import aiosqlite
import asyncio
from collections import defaultdict

from api_requests import get_status
from helper import send_error
from texts.user import msg10, msg11
from loader import bot
from config import update_status_time, DB_PATH


async def edit_order():
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        # Eng muhim sozlamalar – har safar ulanganda qayta o'rnatiladi
        await db.execute("PRAGMA busy_timeout = 15000;")      # 15 soniya kutadi
        await db.execute("PRAGMA journal_mode = WAL;")        # o'qish/yozish parallel bo'lishi uchun
        await db.execute("PRAGMA synchronous = NORMAL;")      # tezroq, ammo biroz xavfliroq (bot uchun odatda OK)

        cursor = await db.execute("""
            SELECT id, user_id, api_order_id, service_id, price, quantity, link
            FROM orders
            WHERE status IN ('Pending', 'Processing', 'In Progress')
        """)
        rows = await cursor.fetchall()

        if not rows:
            return

        # Batch yig'ish uchun strukturalar
        status_updates = []             # [(order_id, new_status), ...]
        completed_ids = []              # faqat completed bo'lganlar uchun
        refund_data = defaultdict(int)  # user_id → qaytariladigan umumiy summa
        messages_to_send = []           # (user_id, text) lar ro'yxati

        for row in rows:
            order_id, user_id, api_order_id, service_id, price, quantity, link = row

            # Service api_id ni olish (katta loyihada bu cache qilinishi mumkin)
            s_cur = await db.execute("SELECT api_id FROM services WHERE id = ?", (service_id,))
            service_row = await s_cur.fetchone()
            if not service_row:
                continue
            api_id = service_row[0]

            status_data = await get_status(api_id, api_order_id)
            if not status_data:
                continue

            new_status = status_data.get("status", "Pending")

            # Statusni yangilash uchun yig'amiz
            status_updates.append((new_status, order_id))

            if new_status == "Completed":
                completed_ids.append(order_id)
                # Telegram xabarini keyinroq yuboramiz (tranzaksiyadan tashqarida)
                text = msg10.format(order_id=order_id, link=link, quantity=quantity)
                messages_to_send.append((user_id, text))

            elif new_status == "Canceled":
                refund_data[user_id] += price
                text = msg11.format(
                    order_id=order_id,
                    link=link,
                    quantity=quantity,
                    paid_amount=price
                )
                messages_to_send.append((user_id, text))

            elif new_status == "Partial":
                remains = int(status_data.get("remains", 0))
                if remains < quantity:
                    give_price = int(price * (quantity - remains) / quantity)
                    refund_data[user_id] += give_price
                    # Agar xohlasangiz Partial uchun alohida xabar yuborish mumkin

        # Endi bitta tranzaksiya ichida hammasini yozamiz – imkon qadar tez
        try:
            # 1. Barcha statuslarni yangilash (bitta so'rov bilan)
            if status_updates:
                await db.executemany(
                    "UPDATE orders SET status = ? WHERE id = ?",
                    status_updates
                )

            # 2. Completed bo'lganlarga vaqt yozish (bitta so'rov)
            if completed_ids:
                placeholders = ",".join("?" * len(completed_ids))
                await db.execute(
                    f"UPDATE orders SET completed_at = datetime('now', '+5 hours') WHERE id IN ({placeholders})",
                    completed_ids
                )

            # 3. Balanslarni qaytarish (user bo'yicha guruhlangan)
            if refund_data:
                for user_id, total_refund in refund_data.items():
                    # User borligini tekshirish shart emas – agar yo'q bo'lsa update hech narsa qilmaydi
                    await db.execute(
                        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                        (total_refund, user_id)
                    )

            await db.commit()

        except aiosqlite.OperationalError as e:
            if "database is locked" in str(e).lower():
                # Bu yerda retry qilish mumkin, lekin hozircha faqat log
                await send_error(f"Lock during commit → {e}")
            else:
                raise

        # Telegram xabarlarini tranzaksiyadan tashqarida yuboramiz
        # (bu eng uzoq vaqt olishi mumkin, lekin bazaga ta'sir qilmaydi)
        for user_id, text in messages_to_send:
            try:
                await bot.send_message(chat_id=user_id, text=text)
            except Exception as send_err:
                await send_error(f"Telegram send failed: {send_err}")


async def order_updater():
    while True:
        try:
            await edit_order()
        except Exception as e:
            await send_error(e)
            # Agar juda tez-tez xato chiqsa, sleep ni oshirish mumkin
        await asyncio.sleep(update_status_time)