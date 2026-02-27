#keyboards/admin.py
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, KeyboardButton


from database.requests import get_apis

def admin_panel_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="⚙️ Asosiy sozlamalar"))
    builder.add(KeyboardButton(text="📊 Statistika"))
    builder.add(KeyboardButton(text="📨 Xabar yuborish"))
    builder.add(KeyboardButton(text="🔐 Majbur obuna kanallar"))
    builder.add(KeyboardButton(text="💳 To'lov tizimlar"))
    builder.add(KeyboardButton(text="🔑 API"))
    builder.add(KeyboardButton(text="🧑‍💻 Foydalanuvchini boshqarish"))
    builder.add(KeyboardButton(text="📈 Xizmatlar"))
    builder.add(KeyboardButton(text="📊 Buyurtmalar"))
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.adjust(1, 2, 1, 2, 1, 2)
    return builder.as_markup(resize_keyboard=True)



async def add_service_apis_kb():
   apis = await get_apis()
   builder = InlineKeyboardBuilder()
   for api in apis:
        builder.add(InlineKeyboardButton(text=f"{api[0]}", callback_data=f"add_service_api:{api[0]}"))
   builder.adjust(2)
   return builder.as_markup()

async def apis_kb():
   apis = await get_apis()
   builder = InlineKeyboardBuilder()
   for api in apis:
        builder.add(InlineKeyboardButton(text=f"{api[0]}", callback_data=f"api:{api[0]}"))
   builder.adjust(2)
   builder.row(InlineKeyboardButton(text="➕ API qo'shish", callback_data="add_api"))
   return builder.as_markup()

def edit_api_kb(api_id: int):
      builder = InlineKeyboardBuilder()
      builder.add(InlineKeyboardButton(text="✏️ Kalitni ozgartirish", callback_data=f"edit_api_key:{api_id}"))
      builder.add(InlineKeyboardButton(text="⏪ Orqaga", callback_data="back_to_apis"))
      builder.add(InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"delete_api:{api_id}"))
      builder.adjust(1, 2)
      return builder.as_markup()
     
def tolov_tasdiqla(user_id: int, amount: int):
   builder = InlineKeyboardBuilder()
   builder.row(InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tolov_tasdiqla:{user_id}:{amount}"),
              InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"tolov_bekor:{user_id}:{amount}"))
   return builder.as_markup()

def back_admin_panel_kb():
      builder = ReplyKeyboardBuilder()
      builder.add(KeyboardButton(text="🗄️ Boshqaruv"))
      
      return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


#=====================///////
# Update service
def update_service_kb(service_id):
     builder = InlineKeyboardBuilder()
     builder.add(InlineKeyboardButton(text="✏️ Narx", callback_data=f"edit:price:{service_id}"))
     builder.add(InlineKeyboardButton(text="✏️ Min", callback_data=f"edit:min_qty:{service_id}"))
     builder.add(InlineKeyboardButton(text="✏️ Max", callback_data=f"edit:max_qty:{service_id}"))
     builder.add(InlineKeyboardButton(text="✏️ Description", callback_data=f"edit:description:{service_id}"))
     builder.add(InlineKeyboardButton(text="✏️ Name", callback_data=f"edit:name:{service_id}"))
     builder.add(InlineKeyboardButton(text="⬅️Orqaga", callback_data=f"service:{service_id}"))
     builder.adjust(2)
     return builder.as_markup()

