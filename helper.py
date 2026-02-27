#helper.py 

from urllib.parse import urlparse

import sys
import traceback
from loader import bot
from config import error_channel_id, channel_id

async def send_error(error: Exception):
    tb = "".join(traceback.format_exception(*sys.exc_info()))[-3800:]  # qisqartirish
    text = (
        f"⚠️ <b>Xatolik yuz berdi!</b>\n\n"
        f"<b>Xatolik turi:</b> <code>{type(error).__name__}</code>\n"
        f"<b>Xabar:</b> <code>{error}</code>\n\n"
        f"<b>Traceback:</b>\n<code>{tb}</code>"
    )
    try:
        await bot.send_message(error_channel_id, text)
    except Exception as e:
        print("❌ Xatolikni yuborishda muammo:", e)

def get_domain(url: str) -> str:
    return urlparse(url).netloc


async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status not in ("left", "kicked")
    except Exception as e:
        await send_error(e)
        return False

def translate_status(status: str) -> str:
    """
    Topsmm.uz statusini o'zbek tiliga aylantiradi
    """
    status_map = {
        "Completed": "✅ Bajarildi",
        "In progress": "🔄 Jarayonda",
        "Processing": "🔄 Jarayonda",
        "Pending": "⏳ Kutilmoqda",
        "Canceled": "❌ Bekor qilindi",
        "Partial": "⚠️ Qisman bajarildi"
    }
    return status_map.get(status.strip(), status)
