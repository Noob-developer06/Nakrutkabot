
#handlers admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram.types import FSInputFile
import os

from database.requests import (
    add_platform, add_category, get_apis,
    get_api, add_service, add_payment, add_api, edit_service
)
from api_requests import get_api_service, get_balance
from keyboards.user import back
from keyboards.admin import (
    apis_kb, admin_panel_kb,
    add_service_apis_kb, edit_api_kb,
    back_admin_panel_kb, update_service_kb
)
from helper import get_domain, send_error
from filters import AdminFilter
from loader import bot
from texts.admin import text2, text3, text4, text5, text6
from config import CURRENCY_RATE, foiz, baza_channel_id


admin_router = Router()


# =========================
# Base class
# =========================
class AdminHandler:
    def __init__(self, router: Router):
        self.router = router
        self.register_handlers()

    def register_handlers(self):
        pass


# =========================
# Admin panel
# =========================
class AdminPanel(AdminHandler):
    def register_handlers(self):
        @self.router.message(F.text == "🗄️ Boshqaruv", AdminFilter())
        async def show_admin_panel(message: Message):
            await message.answer("Admin panel", reply_markup=admin_panel_kb())


# =========================
# API
# =========================
class AddApiState(StatesGroup):
    url = State()
    key = State()


class Api(AdminHandler):

    async def build_api_list_text(self):
        try:
            apis = await get_apis()
            msg = f"🔑 API'lar ro'yhati: {len(apis)}\n\n"

            for api in apis:
                api_balance = await get_balance(api_id=api[0])
                balance = api_balance.get("balance", "N/A")
                currency = api_balance.get("currency", "N/A")
                msg += f"{api[0]}. {get_domain(api[1])} - {balance} {currency}\n"

            return msg
        except Exception as e:
            await send_error(e)
            return "❌ API ro'yhatini olishda xatolik yuz berdi."

    def register_handlers(self):

        @self.router.message(F.text == "🔑 API", AdminFilter())
        async def show_apis(message: Message):
            try:
                msg = await self.build_api_list_text()
                await message.answer(msg, reply_markup=await apis_kb())
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data == "back_to_apis")
        async def back_to_apis(callback: CallbackQuery):
            try:
                msg = await self.build_api_list_text()
                await callback.message.edit_text(msg, reply_markup=await apis_kb())
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("api:"))
        async def show_api_info(callback: CallbackQuery):
            try:
                api_id = int(callback.data.split(":")[1])
                api = await get_api(api_id)

                url = api[1]
                key = api[2]
                domain = get_domain(url)

                api_balance = await get_balance(api_id=api_id)
                balance = api_balance.get("balance", "N/A")
                currency = api_balance.get("currency", "N/A")

                await callback.message.edit_text(
                    text6.format(
                        domain=domain,
                        url=url,
                        key=key,
                        balance=balance,
                        currency=currency
                    ),
                    reply_markup=edit_api_kb(api_id)
                )
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data == "add_api")
        async def start_add_api(callback: CallbackQuery, state: FSMContext):
            try:
                await callback.message.delete()
            except Exception:
                pass

            try:
                await callback.message.answer(
                    "API manzilini kiriting:\n\nNamuna: https://capitalsmmapi.uz/api/v2",
                    reply_markup=back_admin_panel_kb()
                )
                await state.set_state(AddApiState.url)
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.message(AddApiState.url)
        async def process_api_url(message: Message, state: FSMContext):
            try:
                await state.update_data(url=message.text)
                await message.answer("API kalitini kiriting:")
                await state.set_state(AddApiState.key)
            except Exception as e:
                await send_error(e)

        @self.router.message(AddApiState.key)
        async def process_api_key(message: Message, state: FSMContext):
            try:
                data = await state.get_data()
                url = data.get("url")
                key = message.text

                api_balance = await get_balance(api_id=None, url=url, key=key)

                if not api_balance:
                    await message.answer("❌ API kaliti yoki manzili xato!")
                    return

                balance = api_balance.get("balance", "N/A")
                currency = api_balance.get("currency", "N/A")

                await add_api(url, key, currency)

                await message.answer(
                    f"✅ API muvaffaqiyatli qo'shildi!\n\nBalans: {balance} {currency}"
                )
                await state.clear()
            except Exception as e:
                await send_error(e)

# =========================
# Platform / Category / Service
# =========================
class AddPlatform(StatesGroup):
    name = State()


class AddCategory(StatesGroup):
    name = State()


class AddServiceState(StatesGroup):
    service_id = State()


class AddService(AdminHandler):

    def register_handlers(self):

        @self.router.callback_query(F.data == "add_platform")
        async def start_add_platform(callback: CallbackQuery, state: FSMContext):
            try:
                try:
                    await callback.message.delete()
                except Exception:
                    pass

                await callback.message.answer(
                    "Platform nomini kiriting",
                    reply_markup=back()
                )
                await state.set_state(AddPlatform.name)
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.message(AddPlatform.name)
        async def save_platform(message: Message, state: FSMContext):
            try:
                await add_platform(message.text)
                await message.answer("Platform qo'shildi")
                await state.clear()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("add_category:"))
        async def start_add_category(callback: CallbackQuery, state: FSMContext):
            try:
                try:
                    await callback.message.delete()
                except Exception:
                    pass

                platform_id = int(callback.data.split(":")[1])
                await state.update_data(platform_id=platform_id)

                await callback.message.answer(
                    "Kategoriya nomini kiriting",
                    reply_markup=back()
                )
                await state.set_state(AddCategory.name)
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.message(AddCategory.name)
        async def save_category(message: Message, state: FSMContext):
            try:
                data = await state.get_data()
                await add_category(message.text, data.get("platform_id"))
                await message.answer("Kategoriya qo'shildi")
                await state.clear()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("add_service:"))
        async def start_add_service(callback: CallbackQuery, state: FSMContext):
            try:
                category_id = int(callback.data.split(":")[1])
                await state.update_data(category_id=category_id)

                apis = await get_apis()
                text = "📋 Xizmat APIsini tanlang:\n\n"

                for api in apis:
                    text += f"{api[0]} - {get_domain(api[1])}\n"

                await callback.message.answer(
                    text,
                    reply_markup=await add_service_apis_kb()
                )
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("add_service_api:"))
        async def choose_service_api(callback: CallbackQuery, state: FSMContext):
            try:
                api_id = int(callback.data.split(":")[1])
                await state.update_data(api_id=api_id)

                await callback.message.answer("Xizmat ID sini kiriting")
                await state.set_state(AddServiceState.service_id)
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.message(AddServiceState.service_id)
        async def save_service(message: Message, state: FSMContext):
            try:
                try:
                    api_service_id = int(message.text)
                except ValueError:
                    await message.answer("❌ Xizmat ID sini raqamda kiriting!")
                    return

                data = await state.get_data()
                category_id = data.get("category_id")
                api_id = data.get("api_id")

                api_service = await get_api_service(api_id, api_service_id)

                if not api_service:
                    await message.answer("❌ Xizmat topilmadi!")
                    return

                api = await get_api(api_id)

                price = float(api_service.get("rate"))
                kurs = CURRENCY_RATE.get(api[3], 1)
                price = int(price * kurs * foiz * 100)

                await add_service(
                    name=api_service.get("name"),
                    category_id=category_id,
                    api_id=api_id,
                    api_service_id=api_service_id,
                    price=price,
                    min_qty=api_service.get("min"),
                    max_qty=api_service.get("max"),
                    refill=api_service.get("refill"),
                    cancel=api_service.get("cancel"),
                    description=None
                )

                await message.answer("✅ Xizmat muvaffaqiyatli qo'shildi!")
                await state.clear()
            except Exception as e:
                await send_error(e)

#===========================
# Update service
#===========================
class UpdateServiceState(StatesGroup):
    edit_service = State()

class UpdateService(AdminHandler):

    def register_handlers(self):

        # =========================
        # Edit menyuni ochish
        # =========================
        @self.router.callback_query(F.data.startswith("edit_service:"))
        async def open_edit_menu(callback: CallbackQuery):
            try:
                service_id = int(callback.data.split(":")[1])

                await callback.message.edit_text(
                    "✏️ Qaysi maydonni tahrirlaysiz?",
                    reply_markup=update_service_kb(service_id)
                )
                await callback.answer()

            except Exception as e:
                await send_error(e)

        # =========================
        # Maydon tanlash
        # =========================
        @self.router.callback_query(F.data.startswith("edit:"))
        async def select_field(callback: CallbackQuery, state: FSMContext):
            try:
                key, service_id = callback.data.split(":")
                service_id = int(service_id)

                await state.update_data(service_id=service_id, key=key)

                texts = {
                    "price": "💰 Yangi narxni kiriting (so'm):",
                    "min_qty": "📉 Yangi minimal miqdorni kiriting:",
                    "max_qty": "📈 Yangi maksimal miqdorni kiriting:",
                    "description": "📝 Yangi tavsifni kiriting:",
                    "name": "🏷 Yangi nomni kiriting:",
                    "activity": "🔄 1 - Aktiv\n0 - Noaktiv"
                }

                await callback.message.answer(texts.get(key, "Yangi qiymat kiriting:"))

                await state.set_state(UpdateServiceState.edit_service)
                await callback.answer()

            except Exception as e:
                await send_error(e)

        # =========================
        # Qiymat qabul qilish
        # =========================
        @self.router.message(UpdateServiceState.edit_service)
        async def update_value(message: Message, state: FSMContext):
            try:
                data = await state.get_data()
                service_id = data.get("service_id")
                key = data.get("key")
                value = message.text

                # Son bo‘lishi kerak bo‘lgan maydonlar
                if key in ["price", "min_qty", "max_qty", "activity"]:
                    if not value.isdigit():
                        return await message.answer("❌ Faqat son kiriting!")

                    value = int(value)

                    if key == "price" and value <= 0:
                        return await message.answer("❌ Narx 0 dan katta bo‘lishi kerak!")

                # Bazani yangilash
                result = await edit_service(service_id, **{key: value})

                if result:
                    await message.answer("✅ Xizmat muvaffaqiyatli yangilandi!")
                else:
                    await message.answer("⚠️ O‘zgarish amalga oshmadi.")

                await state.clear()

            except Exception as e:
                await send_error(e)




# =========================
# Payment confirmation
# =========================
class TolovTasdiqla(AdminHandler):
    def register_handlers(self):

        @self.router.callback_query(F.data.startswith("tolov_tasdiqla:"))
        async def confirm_payment(callback: CallbackQuery):
            try:
                _, user_id, amount = callback.data.split(":")
                user_id, amount = int(user_id), int(amount)

                await add_payment(user_id, amount * 100)

                await callback.message.edit_caption(
                    caption=text2.format(user_id=user_id, amount=amount),
                    reply_markup=None
                )

                await bot.send_message(user_id, text5.format(amount=amount))
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("tolov_bekor:"))
        async def cancel_payment(callback: CallbackQuery):
            try:
                _, user_id, amount = callback.data.split(":")
                user_id, amount = int(user_id), int(amount)

                await callback.message.edit_caption(
                    caption=text3.format(user_id=user_id, amount=amount),
                    reply_markup=None
                )

                await bot.send_message(user_id, text4.format(amount=amount))
                await callback.answer()
            except Exception as e:
                await send_error(e)




#===========================

@admin_router.message(F.text == "/permanadmin", AdminFilter())
async def send_database_file(message: Message):
    
    file_path = "database/data.db"

    if os.path.exists(file_path):
        await message.bot.send_document(
            chat_id=baza_channel_id,  # kanal ID
            document=FSInputFile(file_path)
        )
        await message.answer("✅ Fayl kanalga yuborildi.")
    else:
        await message.answer("⚠️ Fayl topilmadi: data.db")



Api(admin_router)
AdminPanel(admin_router)
AddService(admin_router)
TolovTasdiqla(admin_router)
UpdateService(admin_router)
