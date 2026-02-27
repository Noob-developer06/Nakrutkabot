import time
from aiogram import BaseMiddleware
from aiogram.types import Message

class PrivateFloodMiddleware(BaseMiddleware):
    def __init__(self, delay: int = 2, ttl: int = 30):
        """
        delay = necha sekunddan keyin keyingi xabar handlerga yetadi
        ttl = RAMda user vaqtini qancha saqlash
        """
        self.delay = delay
        self.ttl = ttl
        self.last_message_time = {}
        self.warned_users = {}  # userga 1 marta eslatma berish uchun

    async def __call__(self, handler, event: Message, data: dict):
        if not event.from_user:
            return await handler(event, data)

        now = time.time()
        user_id = event.from_user.id

        # eski userlarni tozalash
        for uid, t in list(self.last_message_time.items()):
            if now - t > self.ttl:
                del self.last_message_time[uid]
                self.warned_users.pop(uid, None)

        last_time = self.last_message_time.get(user_id)

        if last_time and now - last_time < self.delay:
            # agar foydalanuvchi allaqachon ogohlantirilmagan bo'lsa
            if not self.warned_users.get(user_id, False):
                await event.answer(f"⚠️ Iltimos, biroz sekinroq yozing.")
                self.warned_users[user_id] = True  # keyingi tez xabarlar uchun yana javob bermaydi
            return  # handlerga yubormaymiz

        # oxirgi xabar vaqtini yangilaymiz
        self.last_message_time[user_id] = now
        self.warned_users[user_id] = False

        return await handler(event, data)
