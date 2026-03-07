import os
from dotenv import load_dotenv

# .env faylni yuklaymiz
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

DB_PATH = "database/data.db"

ADMIN = 6870313968

ref_bonus = 100

karta = "9860350148113086"
visa = "4916990322377653"
FIO = "Perman Shamuratov"

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
