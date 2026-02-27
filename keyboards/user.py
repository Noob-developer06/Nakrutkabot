#keyboards/user.py

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import KeyboardButton, InlineKeyboardButton

from database.requests import get_platforms, get_categories, get_services, get_user

from config import ADMIN, pay_methods, channel_username
from helper import translate_status


def menu_kb(user_id):
    builder = ReplyKeyboardBuilder()

    builder.add(KeyboardButton(text="🗂 Xizmatlar"))
    builder.add(KeyboardButton(text="👤Mening hisobim"))
    builder.add(KeyboardButton(text="🔍 Buyurtmalarim"))
    builder.add(KeyboardButton(text="💰Hisob toʻldirish"))
    builder.add(KeyboardButton(text="💸 Pul ishlash"))
    builder.add(KeyboardButton(text="📚 Qo'llanmalar"))
    builder.add(KeyboardButton(text="☎️ Murojaat qilish"))
    if user_id == ADMIN:
        builder.add(KeyboardButton(text="🗄️ Boshqaruv"))
    builder.adjust(1, 2)  # 1 qator va 2 ta tugma

    return builder.as_markup(resize_keyboard=True)
  # Har bir qatorda 2 ta tugma


def back():
    back_builder = ReplyKeyboardBuilder()
    back_builder.add(KeyboardButton(text="⬅️ Orqaga"))
    back_builder.adjust(1)
    return back_builder.as_markup(resize_keyboard=True)

def pay_methods_kb():
     builder = InlineKeyboardBuilder()
     for key, value in pay_methods.items():
          builder.add(InlineKeyboardButton(text=value, callback_data=f"pay_method:{key}"))
     builder.adjust(2)
     return builder.as_markup()


def tolov_qildim():
     builder = InlineKeyboardBuilder()
     builder.add(InlineKeyboardButton(text="✅To'lov qildim", callback_data="tolov_qildim"))
     builder.adjust(1)
     return builder.as_markup()


async def platforms_kb(user_id: int):
     platforms = await get_platforms()
     builder = InlineKeyboardBuilder()
     for platform in platforms:
          builder.add(InlineKeyboardButton(text=platform[1], callback_data=f"platform:{platform[0]}"))
     builder.adjust(2)
     if user_id == ADMIN:
         builder.row(InlineKeyboardButton(text="➕ Qo'shish", callback_data="add_platform"))

     return builder.as_markup()


async def categories_kb(platform_id: int, user_id: int):
      categories = await get_categories(platform_id)
      builder = InlineKeyboardBuilder()
      for category in categories:
           builder.add(InlineKeyboardButton(text=category[1], callback_data=f"category:{category[0]}:{platform_id}"))
      builder.adjust(1)
      if user_id == ADMIN:
           builder.row(InlineKeyboardButton(text="➕ Qo'shish", callback_data=f"add_category:{platform_id}"),
                       InlineKeyboardButton(text="✏️Tahrirlash", callback_data=f"edit_platform:{platform_id}"),
                       InlineKeyboardButton(text="❌O'chirish", callback_data=f"delete_platform:{platform_id}"))
      builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_platforms"))
      return builder.as_markup()


async def services_kb(category_id: int, platform_id: int, user_id: int):
      services = await get_services(category_id)
      builder = InlineKeyboardBuilder()
      for service in services:
           price = service[4]
           builder.add(InlineKeyboardButton(text=f"{service[1][:15]} - {price/100} so'm", callback_data=f"service:{service[0]}"))
      builder.adjust(1)
      if user_id == ADMIN:
           builder.row(InlineKeyboardButton(text="➕ Qo'shish", callback_data=f"add_service:{category_id}"),
                       InlineKeyboardButton(text="✏️Tahrirlash", callback_data=f"edit_category:{category_id}"),
                       InlineKeyboardButton(text="❌O'chirish", callback_data=f"delete_category:{category_id}"))
      builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"platform:{platform_id}"))
      return builder.as_markup()



def start_order_kb(user_id: int, service_id: int, category_id: int, platform_id: int):
      builder = InlineKeyboardBuilder()
      builder.add(InlineKeyboardButton(text="✅Buyurtma berish", callback_data=f"start_order:{service_id}"))
      if user_id == ADMIN:
          builder.row(InlineKeyboardButton(text="📝 Tahrirlash", callback_data=f"edit_service:{service_id}"),
                      InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"delete_service:{service_id}"))
      builder.add(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"category:{category_id}:{platform_id}"))
      builder.adjust(1, 2, 1)
      return builder.as_markup()


def send_order_kb():
      builder = InlineKeyboardBuilder()
      builder.add(InlineKeyboardButton(text="✅Yuborish", callback_data="send_order"))
      builder.adjust(1)
      return builder.as_markup()

def subscribe_kb():
      builder = InlineKeyboardBuilder()
      builder.add(InlineKeyboardButton(text="➕️ Obuna bo'lish", url=f"https://t.me/{channel_username}"))
      builder.add(InlineKeyboardButton(text="✅ Tekshirish", callback_data="subscribed"))
      builder.adjust(1)
      return builder.as_markup()


PER_PAGE = 5  # Har bir sahifada 5 ta buyurtma

async def orders_kb(user_id: int, page: int = 1):
    user = await get_user(user_id)
    orders = user.get("orders", [])
    if not orders:
        return None

    orders = orders[::-1]  # teskari tartib

    builder = InlineKeyboardBuilder()
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    total_pages = (len(orders) + PER_PAGE - 1) // PER_PAGE

    # Buyurtmalar tugmalari
    for order in orders[start:end]:
        status = translate_status(order[7])
        text = f"🆔 {order[0]} - {status}"
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"order:{order[0]}"
        ))

    builder.adjust(1)  # har qatorda 1 tugma

    # Navigatsiya tugmalari
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"page:{page-1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore")
    )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"page:{page+1}")
        )

    builder.row(*nav_buttons)

    return builder.as_markup()

def back_to_orders(order_id, refill=False, cancel=False):
    builder = InlineKeyboardBuilder()

    if refill:
        builder.add(
            InlineKeyboardButton(text="➕ Qayta to'ldirish", callback_data=f"refill:{order_id}")
        )
    if cancel:
        builder.add(
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel:{order_id}")
        )

    builder.add(
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="ordersback")
    )

    builder.adjust(2, 1)
    return builder.as_markup()
     
