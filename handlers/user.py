# handlers/user.py

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from api_requests import send_order
from config import FIO, karta, max_pay, min_pay, pay_methods, payments_channel_id, ref_bonus, support_channel_id
from database.requests import add_user, get_service, get_user, add_order, sub_balance, add_balance, give_ref_bonus, get_order
from keyboards.user import back, categories_kb, menu_kb, pay_methods_kb, platforms_kb, services_kb, start_order_kb, tolov_qildim, send_order_kb, subscribe_kb, orders_kb, back_to_orders
from keyboards.admin import tolov_tasdiqla
from loader import bot
from texts.admin import text1
from texts.user import (msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8, msg9, msg12, msg13, msg15, msg16, msg17, msg18, msg19, msg20, msg31, msg29)

from helper import send_error, is_subscribed, translate_status, format_time, check_social_link

user_router = Router()


class UserHandler:
    def __init__(self, router: Router):
        self.router = router
        self.register_handlers()

    def register_handlers(self):
        pass



class Start(UserHandler):
    def register_handlers(self):

        @self.router.message(CommandStart())
        async def start(message: Message, command: CommandObject, state: FSMContext):
            try:
                await state.clear()
                user_id = message.from_user.id
                ref_id = command.args

                try:
                    ref_id = int(ref_id)
                except Exception:
                    ref_id = None

                await add_user(user_id, ref_id)
                if not await is_subscribed(user_id):
                    await message.answer(msg31, reply_markup=subscribe_kb())
                    return

                await message.answer(msg1, reply_markup=menu_kb(user_id))
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data == "subscribed")
        async def subscribed(callback: CallbackQuery, state: FSMContext):
            try:
                await state.clear()
                if not await is_subscribed(callback.from_user.id):
                    await callback.answer("❌ Siz kanalga obuna bo'lmagansiz!", show_alert=True)
                    return

                await callback.message.delete()
                await callback.message.answer(msg1, reply_markup=menu_kb(callback.from_user.id))
                await give_ref_bonus(callback.from_user.id)
                await callback.answer()

            except Exception as e:
                await send_error(e)

        @self.router.message(F.text == "⬅️ Orqaga")
        async def back_handler(message: Message, state: FSMContext):
            try:
                await state.clear()
                await message.answer(msg1, reply_markup=menu_kb(message.from_user.id))
            except Exception as e:
                await send_error(e)


class MyBalance(UserHandler):
    def register_handlers(self):

        @self.router.message(F.text == "👤Mening hisobim")
        async def my_balance(message: Message, state: FSMContext):
            try:
                await state.clear()
                user = await get_user(message.from_user.id)
                if not user:
                    await message.answer("/start buyrug'ini bosing!")
                    return
                await message.answer(
                    msg12.format(
                        user_id=message.from_user.id,
                        balance=user["balance"]/100,
                        orders_count=len(user["orders"]),
                        ref_count=len(user["ref_ids"]),
                        deposit=sum(p[2] for p in user["payments"])/100
                    )
                )
            except Exception as e:
                await send_error(e)


class PulIshlash(UserHandler):
    def register_handlers(self):

        @self.router.message(F.text == "💸 Pul ishlash")
        async def pul_ishlash(message: Message, state: FSMContext):
            try:
                await state.clear()
                bot_info = await bot.get_me()
                reflink = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
                await message.answer(msg13.format(reflink=reflink, ref_bonus=ref_bonus))
            except Exception as e:
                await send_error(e)

class PayState(StatesGroup):
    amount = State()
    check = State()


class HisobToldirish(UserHandler):
    def register_handlers(self):

        @self.router.message(F.text == "💰Hisob toʻldirish")
        async def hisob_toldirish(message: Message, state: FSMContext):
            try:
                await state.clear()
                await message.answer(msg15, reply_markup=pay_methods_kb())
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("pay_method:"))
        async def pay_method(callback: CallbackQuery, state: FSMContext):
            try:
                await state.clear()
                await callback.message.delete()
                method = callback.data.split(":")[1]
                await state.update_data(pay_method=method)
                await callback.message.answer(
                    msg16.format(karta=karta, FIO=FIO, min_pay=min_pay, max_pay=max_pay),
                    reply_markup=tolov_qildim()
                )
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data == "tolov_qildim")
        async def confirm_payment(callback: CallbackQuery, state: FSMContext):
            try:
                await callback.message.delete()
                await callback.message.answer(msg17.format(min_pay=min_pay, max_pay=max_pay), reply_markup=back())
                await state.set_state(PayState.amount)
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.message(PayState.amount, F.text)
        async def amount_handler(message: Message, state: FSMContext):
            try:
                try:
                    amount = int(message.text)
                except Exception:
                    await message.answer(msg17.format(min_pay=min_pay, max_pay=max_pay))
                    return

                if amount < min_pay or amount > max_pay:
                    await message.answer(msg17.format(min_pay=min_pay, max_pay=max_pay))
                    return

                await state.update_data(amount=amount)
                await message.answer(msg18)
                await state.set_state(PayState.check)
            except Exception as e:
                await send_error(e)

        @self.router.message(PayState.check, F.photo)
        async def check_handler(message: Message, state: FSMContext):
            try:
                data = await state.get_data()
                method = data.get("pay_method")
                amount = data.get("amount")
                await message.answer(msg19)
                await bot.send_photo(
                    payments_channel_id,
                    message.photo[-1].file_id,
                    caption=text1.format(
                        user_id=message.from_user.id,
                        amount=amount,
                        pay_method=pay_methods[method]
                    ),
                    reply_markup=tolov_tasdiqla(message.from_user.id, amount)
                )
                await state.clear()
            except Exception as e:
                await send_error(e)

class SupportState(StatesGroup):
    text = State()


class SupportHandler(UserHandler):
    def register_handlers(self):

        @self.router.message(F.text == "☎️ Murojaat qilish")
        async def support(message: Message, state: FSMContext):
            try:
                await state.clear()
                await message.answer(msg20, reply_markup=back())
                await state.set_state(SupportState.text)
            except Exception as e:
                await send_error(e)

        @self.router.message(SupportState.text)
        async def support_text(message: Message, state: FSMContext):
            try:
                await message.answer("✅ Murojaatingiz qabul qilindi. Tez orada javob beramiz!")
                await bot.send_message(
                    support_channel_id,
                    f"🆔 {message.from_user.id} dan murojaat:\n\n{message.text}"
                )
                await state.clear()
            except Exception as e:
                await send_error(e)

class StartOrderState(StatesGroup):
    quantity = State()
    link = State()
    confirm = State()


class Xizmatlar(UserHandler):
    def register_handlers(self):

        @self.router.message(F.text == "🗂 Xizmatlar")
        async def xizmatlar(message: Message, state: FSMContext):
            try:
                await state.clear()
                await message.answer(msg2, reply_markup=await platforms_kb(message.from_user.id))
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data == "back_to_platforms")
        async def back_to_platforms(callback: CallbackQuery, state: FSMContext):
            try:
                await state.clear()
                await callback.message.edit_text(msg2, reply_markup=await platforms_kb(callback.from_user.id))
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("platform:"))
        async def platform(callback: CallbackQuery, state: FSMContext):
            try:
                await state.clear()
                platform_id = int(callback.data.split(":")[1])
                await callback.message.edit_text(msg3, reply_markup=await categories_kb(platform_id, callback.from_user.id))
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("category:"))
        async def category(callback: CallbackQuery, state: FSMContext):
            try:
                await state.clear()
                parts = callback.data.split(":")
                await callback.message.edit_text(msg4, reply_markup=await services_kb(int(parts[1]), int(parts[2]), callback.from_user.id))
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("service:"))
        async def service(callback: CallbackQuery, state: FSMContext):
            try:
                await state.clear()
                user_id = callback.from_user.id
                service_id = int(callback.data.split(":")[1])
                service_data = await get_service(service_id)
                if not service_data:
                    await callback.answer("Xizmat topilmadi", show_alert=True)
                    return

                price = service_data["price"]
                chegirma = 0
                cancel = "Mavjud" if service_data["cancel"] == 1 else "Mavjud emas"
                refill = "Mavjud" if service_data["refill"] == 1 else "Mavjud emas"
                description = service_data["description"] or ""
                avg_time = format_time(service_data["avg_time"]) or "Yangi xizmat"
                min_qty = service_data["min_qty"]
                max_qty = service_data["max_qty"]
                service_order_count = service_data["service_orders_count"]

                await callback.message.edit_text(
                    msg5.format(
                        service_name=service_data["name"],
                        service_id=service_id,
                        price=price / 100,
                        chegirma=chegirma,
                        service_order_count=service_order_count,
                        description=description,
                        avg_time=avg_time,
                        refill=refill,
                        cancel=cancel,
                        min=min_qty,
                        max=max_qty
                    ),
                    reply_markup=start_order_kb(user_id, service_id, service_data["category_id"], service_data["platform_id"])
                )
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data.startswith("start_order:"))
        async def start_order(callback: CallbackQuery, state: FSMContext):
            try:
                await state.clear()
                service_id = int(callback.data.split(":")[1])

                service_data = await get_service(service_id)
                if not service_data:
                    await callback.answer("Xizmat topilmadi", show_alert=True)
                    return

                min_qty = service_data["min_qty"]
                max_qty = service_data["max_qty"]

                await state.update_data(service_id=service_id, min_qty=min_qty, max_qty=max_qty)
                await callback.message.edit_text(msg6.format(min=min_qty, max=max_qty), reply_markup=back())
                await state.set_state(StartOrderState.quantity)
                await callback.answer()
            except Exception as e:
                await send_error(e)

        @self.router.message(StartOrderState.quantity, F.text)
        async def quantity(message: Message, state: FSMContext):
            try:
                data = await state.get_data()
                qty = int(message.text)
                if qty < data.get("min_qty") or qty > data.get("max_qty"):
                    await message.answer(msg6.format(min=data.get("min_qty"), max=data.get("max_qty")))
                    return
                await state.update_data(quantity=qty)
                await message.answer(msg7)
                await state.set_state(StartOrderState.link)
            except Exception as e:
                await send_error(e)

        @self.router.message(StartOrderState.link, F.text)
        async def link(message: Message, state: FSMContext):
            try:
                link = message.text
                if not check_social_link(link):
                    await message.answer("❌ Noto‘g‘ri link!\n\nIltimos, to‘g‘ri havolani qayta yuboring.")
                    return
                data = await state.get_data()
                service_id = data.get("service_id")
                service_data = await get_service(service_id)
                if not service_data:
                    await message.answer("❌ Xizmat topilmadi.")
                    await state.clear()
                    return

                quantity = data.get("quantity")
                price = int(service_data["price"] * quantity / 1000)
                name = service_data["name"]

                await message.answer(
                    msg8.format(
                        id=service_id,
                        name=name,
                        quantity=quantity,
                        link=link,
                        price=price / 100
                    ),
                    reply_markup=send_order_kb(), disable_web_page_preview = True
                )
                await state.update_data(link=link, price=price)
                await state.set_state(StartOrderState.confirm)
            except Exception as e:
                await send_error(e)

        @self.router.callback_query(F.data == "send_order", StartOrderState.confirm)
        async def confirm_order(callback: CallbackQuery, state: FSMContext):
            try:
                try:
                    await callback.message.delete()
                except Exception:
                    pass

                data = await state.get_data()
                service_id, price, link, quantity = data.get("service_id"), data.get("price"), data.get("link"), data.get("quantity")

                if not all([service_id, link, quantity]):
                    await callback.message.answer("❌ Xatolik. Qayta urinib ko'ring.")
                    await state.clear()
                    return

                try:
                    price = int(price)
                except Exception:
                    await callback.message.answer("❌ Xatolik. Qayta urinib ko'ring.")
                    await state.clear()
                    return

                if not await sub_balance(callback.from_user.id, price):
                    await callback.message.answer("❌ Hisobingizda yetarli mablag' mavjud emas!")
                    await state.clear()
                    return

                service_data = await get_service(service_id)
                if not service_data:
                    await callback.message.answer("❌ Xizmat topilmadi.")
                    await add_balance(callback.from_user.id, price)
                    await state.clear()
                    return

                order = await send_order(service_data["api_id"], service_data["api_service_id"], link, quantity)
                if not isinstance(order, dict) or not order.get("order"):
                    await callback.message.answer("❌ API xatolik. Qayta urinib ko'ring.")
                    await add_balance(callback.from_user.id, price)
                    await state.clear()
                    return

                order_id = await add_order(callback.from_user.id, service_id, link, quantity, price, order["order"])
                await callback.message.answer(msg9.format(order_id=order_id))
                await state.clear()
                await callback.answer()
            except Exception as e:
                await send_error(e)




class MyOrders(UserHandler):
    def register_handlers(self):

        # 🔹 Buyurtmalarim
        @self.router.message(F.text == "🔍 Buyurtmalarim")
        async def orders(message: Message, state: FSMContext):
            try:
                await state.clear()
                user_id = message.from_user.id
                kb = await orders_kb(user_id)

                if not kb:
                    await message.answer("❌ Sizda hali buyurtmalar mavjud emas.")
                    return

                await message.answer("📊 Buyurtmalaringiz ro'yxati:", reply_markup=kb)

            except Exception as e:
                await send_error(e)


        # 🔹 Bitta buyurtma ichiga kirish
        @self.router.callback_query(F.data.startswith("order:"))
        async def order(callback: CallbackQuery, state: FSMContext):
            try:
                await state.clear()
                order_id = int(callback.data.split(":")[1])
                order = await get_order(order_id)

                if not order:
                    await callback.answer("Buyurtma topilmadi", show_alert=True)
                    return

                service_id = order[2]
                link = order[3]
                quantity = order[4]
                price = order[5]
                status = translate_status(order[7])
                created_at = order[8]

                service_data = await get_service(service_id)
                if not service_data:
                    await callback.answer("Xizmat topilmadi", show_alert=True)
                    return

                refill = service_data["refill"]
                cancel = service_data["cancel"]
                service_name = service_data["name"]
                service_id = service_data["id"]

                await callback.message.edit_text(
                    msg29.format(
                        order_id=order_id,
                        id=service_id,
                        service_name=service_name,
                        link=link,
                        quantity=quantity,
                        price=price / 100,
                        created_at=created_at,
                        status=status
                    ),
                    reply_markup=back_to_orders(
                        order_id,
                        refill=refill,
                        cancel=cancel
                    ), disable_web_page_preview = True
                )

                await callback.answer()

            except Exception as e:
                await send_error(e)


        # 🔹 Pagination
        @self.router.callback_query(F.data.startswith("page:"))
        async def paginate_orders(callback: CallbackQuery):
            try:
                page = int(callback.data.split(":")[1])
                kb = await orders_kb(callback.from_user.id, page)

                if kb:
                    await callback.message.edit_reply_markup(reply_markup=kb)

                await callback.answer()

            except Exception as e:
                await send_error(e)


        # 🔹 Orqaga
        @self.router.callback_query(F.data == "ordersback")
        async def ordersback(callback: CallbackQuery, state: FSMContext):
            try:
                user_id = callback.from_user.id
                kb = await orders_kb(user_id)

                if not kb:
                    await callback.message.edit_text("❌ Sizda hali buyurtmalar mavjud emas.")
                else:
                    await callback.message.edit_text("📊 Buyurtmalaringiz ro'yxati:", reply_markup=kb)

                await callback.answer()

            except Exception as e:
                await send_error(e)



Start(user_router)
MyBalance(user_router)
PulIshlash(user_router)
HisobToldirish(user_router)
SupportHandler(user_router)
Xizmatlar(user_router)
MyOrders(user_router)