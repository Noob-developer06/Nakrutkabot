#database/requests.py


import aiosqlite
from config import DB_PATH, ref_bonus
from loader import bot

# =======================
# 1️⃣ Create table
# =======================
async def create_table():
    async with aiosqlite.connect(DB_PATH) as db:
        # users
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            balance INTEGER DEFAULT 0,
            ref_from_id INTEGER,
            ref_bonus INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT (datetime('now', '+5 hours')),
            banned INTEGER DEFAULT 0
        )""")
        # payments
        await db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            created_at DATETIME DEFAULT (datetime('now', '+5 hours'))
        )""")
        # apis
        await db.execute("""
        CREATE TABLE IF NOT EXISTS apis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            key TEXT,
            currency TEXT
        )""")
        # platforms
        await db.execute("""
        CREATE TABLE IF NOT EXISTS platforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )""")
        # categories
        await db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            platform_id INTEGER
        )""")
        # services
        await db.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category_id INTEGER,
            price INTEGER,
            min_qty INTEGER,
            max_qty INTEGER,
            api_id INTEGER,
            api_service_id INTEGER,
            description TEXT,
            refill INTEGER,
            cancel INTEGER,
            activity INTEGER DEFAULT 1        
        )""")
        # orders
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_id INTEGER,
            link TEXT,
            quantity INTEGER,
            price INTEGER,
            api_order_id INTEGER,
            status TEXT DEFAULT 'Pending',
            created_at DATETIME DEFAULT (datetime('now', '+5 hours')),
            completed_at DATETIME DEFAULT NULL
        )""")
        await db.commit()


# =======================
# 2️⃣ User bilan bog‘liq
# =======================
async def add_user(user_id: int, ref_from_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()

        if user:
            return False

        # O‘zini o‘zi refer qilmasin
        if ref_from_id and ref_from_id == user_id:
            ref_from_id = None

        if ref_from_id:
            cursor = await db.execute("SELECT id FROM users WHERE user_id = ?", (ref_from_id,))
            ref_user = await cursor.fetchone()

            if ref_user:
                await db.execute("INSERT INTO users (user_id, ref_from_id) VALUES (?, ?)", (user_id, ref_from_id))
                try:
                    await bot.send_message(chat_id=ref_from_id, text=f'🆕 Sizga yangi <a href="tg://user?id={user_id}">taklif</a> mavjud!')
                except Exception:
                    pass
            else:
                await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        else:
            await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))

        await db.commit()   # ✅ MUHIM
        return True




async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            return None
        user_data = {
            "user_id": user[1],
            "balance": user[2],
            "ref_from_id": user[3],
            "ref_bonus": user[4],
            "created_at": user[5],
            "banned": user[6]
        }
        ref_cursor = await db.execute("SELECT user_id FROM users WHERE ref_from_id = ?", (user_id,))
        user_data["ref_ids"] = await ref_cursor.fetchall()
        orders_cursor = await db.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
        user_data["orders"] = await orders_cursor.fetchall()
        payments_cursor = await db.execute("SELECT * FROM payments WHERE user_id = ?", (user_id,))
        user_data["payments"] = await payments_cursor.fetchall()
        return user_data

async def add_balance(user_id: int, amount: int, db=None):
    if db is None:
        async with aiosqlite.connect(DB_PATH, timeout=30) as db:
            return await add_balance(user_id, amount, db)

    cursor = await db.execute(
        "SELECT id FROM users WHERE user_id = ?",
        (user_id,)
    )
    user = await cursor.fetchone()
    if not user:
        return False

    await db.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, user_id)
    )

    return True

async def sub_balance(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            UPDATE users
            SET balance = balance - ?
            WHERE user_id = ?
            AND balance >= ?
            """,
            (amount, user_id, amount)
        ) as cursor:
            await db.commit()
            if cursor.rowcount == 0:
                return False
            return True
        
async def add_payment(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        if user:
            await db.execute("INSERT INTO payments (user_id, amount) VALUES (?, ?)", (user_id, amount))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.commit()
            return True
        return False



async def give_ref_bonus(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT ref_bonus, ref_from_id FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        if not result:
            return False
        current_ref_bonus, ref_from_id = result
        if current_ref_bonus > 0 or not ref_from_id:
            return False
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (ref_bonus * 100, ref_from_id))
        await db.execute("UPDATE users SET ref_bonus = ? WHERE user_id = ?", (ref_bonus * 100, user_id))
        try:
            await bot.send_message(chat_id=ref_from_id,
                                   text=f"🎉 Sizga {ref_bonus} so'm referal bonusi berildi!")
        except Exception:
            pass
        await db.commit()
        return True


# =======================
# 3️⃣ API bilan bog‘liq
# =======================
async def add_api(url: str, key: str, currency: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO apis (url, key, currency) VALUES (?, ?, ?)", (url, key, currency))
        await db.commit()
        return True

async def get_api(api_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM apis WHERE id = ?", (api_id,))
        return await cursor.fetchone()

async def get_apis():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM apis")
        return await cursor.fetchall()

async def del_api(api_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM apis WHERE id = ?", (api_id,))
        await db.commit()
        return True

# =======================
# 4️⃣ Platform bilan bog‘liq
# =======================
async def add_platform(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO platforms (name) VALUES (?)", (name,))
        await db.commit()
        return True

async def get_platforms():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM platforms")
        return await cursor.fetchall()

async def del_platform(platform_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM platforms WHERE id = ?", (platform_id,))
        await db.commit()
        return True
# =======================
# 5️⃣ Category bilan bog‘liq
# =======================
async def add_category(name: str, platform_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM platforms WHERE id = ?", (platform_id,))
        if not await cursor.fetchone():
            return False
        await db.execute("INSERT INTO categories (name, platform_id) VALUES (?, ?)", (name, platform_id))
        await db.commit()
        return True

async def get_categories(platform_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM categories WHERE platform_id = ?", (platform_id,))
        return await cursor.fetchall()

async def del_category(category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        await db.commit()
        return True


# =======================
# 6️⃣ Service bilan bog‘liq (yangilangan)
# =======================
async def add_service(name: str, category_id: int, api_id: int, api_service_id: int, price: int = 0,
                      min_qty: int = 1, max_qty: int = 1, refill: int = 0, cancel: int = 0,
                      activity: int = 1, description: str=None):
    async with aiosqlite.connect(DB_PATH) as db:
        # Category va API mavjudligini tekshirish
        cursor = await db.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
        if not await cursor.fetchone():
            return False
        cursor = await db.execute("SELECT id FROM apis WHERE id = ?", (api_id,))
        if not await cursor.fetchone():
            return False

        # Service qo'shish
        await db.execute("""
            INSERT INTO services (name, category_id, price, min_qty, max_qty, api_id, api_service_id, description, refill, cancel, activity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, category_id, price, min_qty, max_qty, api_id, api_service_id, description, refill, cancel, activity))
        await db.commit()
        return True


async def get_services(category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, name, api_id, api_service_id, price, min_qty, max_qty, refill, cancel, activity 
            FROM services 
            WHERE category_id = ? AND activity = 1
            ORDER BY price ASC
        """, (category_id,))
        return await cursor.fetchall()

import aiosqlite
from config import DB_PATH

async def get_service(service_id: int, db=None):
    if db is None:
        async with aiosqlite.connect(DB_PATH) as db:
            return await get_service(service_id, db)

    # Service ma'lumotini olish
    cursor = await db.execute("SELECT * FROM services WHERE id = ?", (service_id,))
    service = await cursor.fetchone()
    if not service:
        return None

    data = {
        "id": service[0],
        "name": service[1],
        "category_id": service[2],
        "price": service[3],
        "min_qty": service[4],
        "max_qty": service[5],
        "api_id": service[6],
        "api_service_id": service[7],
        "description": service[8],
        "refill": service[9],
        "cancel": service[10],
        "activity": service[11]
    }

    # Avg time orders orqali
    avg_cursor = await db.execute("""
        SELECT AVG(strftime('%s', completed_at) - strftime('%s', created_at)) 
        FROM orders 
        WHERE service_id = ? AND status = 'Completed'
    """, (service_id,))
    avg_time = await avg_cursor.fetchone()
    data["avg_time"] = int(avg_time[0]) if avg_time and avg_time[0] else None

    # Category orqali platform_id olish
    p_cursor = await db.execute("SELECT platform_id FROM categories WHERE id = ?", (service[2],))
    platform = await p_cursor.fetchone()
    data["platform_id"] = platform[0] if platform else None

    # Service orders count
    orders_cursor = await db.execute("SELECT COUNT(*) FROM orders WHERE service_id = ?", (service_id,))
    orders_count = await orders_cursor.fetchone()
    data["service_orders_count"] = orders_count[0] if orders_count else 0

    return data

async def edit_service(service_id: int, **kwargs):
    async with aiosqlite.connect(DB_PATH) as db:
        # Yangilanishi kerak bo'lgan maydonlarni aniqlash
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['name', 'price', 'min_qty', 'max_qty', 'description', 'refill', 'cancel', 'activity']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        # SQL so'rovini yaratish
        query = f"UPDATE services SET {', '.join(fields)} WHERE id = ?"
        values.append(service_id)
        
        # Yangilash
        await db.execute(query, tuple(values))
        await db.commit()
        return True




async def del_service(service_id: int, off_activity = True):
    async with aiosqlite.connect(DB_PATH) as db:
        if off_activity:
            await db.execute("UPDATE services SET activity = 0 WHERE id = ?", (service_id,))
        else:
            await db.execute("DELETE FROM services WHERE id = ?", (service_id,))
        await db.commit()
        return True

# =======================
# 7️⃣ Orders bilan bog‘liq
# =======================
async def add_order(user_id: int, service_id: int, link: str, quantity: int, price: int, api_order_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        if not await cursor.fetchone():
            return None
        cursor = await db.execute("SELECT 1 FROM services WHERE id = ?", (service_id,))
        if not await cursor.fetchone():
            return None
        cursor = await db.execute("INSERT INTO orders (user_id, service_id, link, quantity, price, api_order_id) VALUES (?, ?, ?, ?, ?, ?)", (user_id, service_id, link, quantity, price, api_order_id))
        await db.commit()
        return cursor.lastrowid

async def get_order(order_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return await cursor.fetchone()


