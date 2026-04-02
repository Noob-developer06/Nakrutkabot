import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

DB_PATH = os.getenv("DB_PATH")

ADMIN = int(os.getenv("ADMIN"))

ref_bonus = int(os.getenv("REF_BONUS"))

karta = os.getenv("KARTA")
visa = os.getenv("VISA")
FIO = os.getenv("FIO")

min_pay = 1000
max_pay = 1000000

update_status_time = 10

payments_channel_id = -1003521269518
support_channel_id = -1003700981785
error_channel_id = -1003758049023
baza_channel_id = -1003758049023

channel_id = -1003757492292
channel_username = "ChatSmmX"


foiz = 1.5

CURRENCY_RATE = {
        "RUB": 160,
        "USD": 12500,
        "UZS": 1
}


pay_methods = {
    "click": "⚫ Click [ AVTO ]",
    "payme": "🔵 Payme [ AVTO ]",
    "paynet": "🟢 Paynet",
    "xazna": "🟡 Xazna",
    "uzum": "🟣 Uzum ",
    "apelsin": "🟠 Apelsin ",
    "tbc": "🔴 TBC ",
    "humo": "🟤 Humo ",
    "click_cashback": "⚫ Click [ CASHBACK ]",
    "hamkorbank": "🟦 Hamkorbank "
}
