import asyncio
import sqlite3
import requests
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties 

TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CARD = "4441111008011946"

# CryptoBot API
CRYPTO_TOKEN = "466345:AADMm3mzlC6KGJmwt3r771bUPIx40CMEKhQ"
CRYPTO_API = "https://pay.crypt.bot/api"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- ЦЕНЫ ДЛЯ СТАНДОФФ (ОСТАЁТСЯ) ---
SO2_PRICES = {
    "7": {"uah": 150, "usd": 3.5},
    "30": {"uah": 300, "usd": 7},
    "90": {"uah": 700, "usd": 16.5}
}

# --- НОВЫЕ ЦЕНЫ ДЛЯ PUBG ЧИТОВ (ТОЛЬКО ГРИВНЫ) ---
PUBG_PRICES = {
    "zolo": {"1": 85, "3": 180, "7": 325, "14": 400, "30": 690, "60": 1000},
    "impact": {"1": 115, "7": 480, "30": 1170},
    "king": {"1": 100, "7": 425, "30": 1060},
    "inferno": {"1": 80, "3": 200, "7": 350, "15": 530, "30": 690, "60": 950},
    "zolo_cis": {"1": 70, "3": 150, "7": 250, "14": 350, "30": 700, "60": 900}
}

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiry_date TEXT,
        product_name TEXT,
        subscribed_at TEXT,
        banned INTEGER DEFAULT 0,
        ban_reason TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS crypto_payments (
        payment_id TEXT PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        days TEXT,
        product TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT
    )
''')

cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
conn.commit()

# --- СОСТОЯНИЯ ---
class OrderState(StatesGroup):
    waiting_for_receipt = State()
    waiting_for_admin_file = State()
    waiting_for_admin_key = State()
    broadcast_text = State()
    ban_reason = State()

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key"), 
         InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💬 Наши отзывы", callback_data="show_reviews"), 
         InlineKeyboardButton(text="📊 Статус ПО", callback_data="check_status")],
        [InlineKeyboardButton(text="🆘 Техподдержка", url="https://t.me/IllyaGarant")]
    ])
    return kb

# --- ФУНКЦИИ CRYPTOBOT (ТЕ ЖЕ) ---
async def create_crypto_invoice(user_id, amount, days, product):
    url = f"{CRYPTO_API}/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    data = {
        "asset": "USDT",
        "amount": amount,
        "description": f"{product} - {days} дней",
        "paid_btn_name": "openBot",
        "paid_btn_url": f"https://t.me/{(await bot.get_me()).username}",
        "payload": f"{user_id}|{days}|{product}"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                return result["result"]
    except Exception as e:
        print(f"CryptoBot error: {e}")
    return None

async def check_crypto_payment(payment_id):
    url = f"{CRYPTO_API}/getInvoices"
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    params = {"invoice_ids": payment_id}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            result = response.json()
            if result.get("ok") and result.get("result", {}).get("items"):
                return result["result"]["items"][0]
    except:
        pass
    return None

# --- ПРОВЕРКА БАНА ---
async def check_ban(user_id):
    cursor.execute('SELECT banned, ban_reason FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    if res and res[0] == 1:
        return True, res[1]
    return False, None

# ---------- ГЛАВНОЕ МЕНЮ (СТАРТ) ----------
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = int(message.from_user.id)
    
    banned, reason = await check_ban(user_id)
    if banned:
        await message.answer(f"⛔️ <b>Вы заблокированы</b>\nПричина: {reason}")
        return
    
    cursor.execute('INSERT OR IGNORE INTO users (user_id, subscribed_at) VALUES (?, ?)', 
                  (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    caption = f"🔥 <b>Plutonium Store</b>\n\n📈 Статус ПО: {status}\n\nДобро пожаловать!"
    await message.answer_photo(
        photo="https://files.catbox.moe/916cwt.png", 
        caption=caption, 
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "start")
async def start_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    
    banned, reason = await check_ban(call.from_user.id)
    if banned:
        await call.message.edit_text(f"⛔️ <b>Вы заблокированы</b>\nПричина: {reason}")
        return
    
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    caption = f"🔥 <b>Plutonium Store</b>\n\n📈 Статус ПО: {status}\n\nДобро пожаловать!"
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=caption), 
        reply_markup=get_main_keyboard()
    )

# ---------- ПРОФИЛЬ ----------
@dp.callback_query(F.data == "profile")
async def profile_callback(call: types.CallbackQuery):
    await call.answer()
    user_id = int(call.from_user.id)
    
    banned, reason = await check_ban(user_id)
    if banned:
        await call.message.edit_text(f"⛔️ <b>Вы заблокированы</b>\nПричина: {reason}")
        return
    
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    
    time_left = "Нет активной подписки"
    product = "Нет"
    
    if res and res[0]:
        try:
            expiry_date = datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S')
            diff = expiry_date - datetime.now()
            if diff.total_seconds() > 0:
                days = diff.days
                hours = diff.seconds // 3600
                minutes = (diff.seconds % 3600) // 60
                time_left = f"{days} дн. {hours} ч. {minutes} мин."
                product = res[1] if res[1] else "Plutonium"
            else:
                time_left = "Истекла"
                cursor.execute('UPDATE users SET expiry_date = NULL, product_name = NULL WHERE user_id = ?', (user_id,))
                conn.commit()
        except:
            time_left = "Ошибка"
    
    cap = f"👤 <b>Профиль</b>\n\n🆔 ID: <code>{user_id}</code>\n📦 Товар: {product}\n⏳ Осталось: <b>{time_left}</b>"
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=cap), 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    )

# ---------- СТАТУС ПО ----------
@dp.callback_query(F.data == "check_status")
async def check_status(call: types.CallbackQuery):
    await call.answer()
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=f"📊 <b>Статус ПО:</b> {status}"), 
        reply_markup=kb
    )

# ---------- ОТЗЫВЫ ----------
@dp.callback_query(F.data == "show_reviews")
async def reviews_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Канал с отзывами", url="https://t.me/plutoniumrewiews")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐ <b>Наши отзывы</b>"), 
        reply_markup=kb
    )

# ---------- МЕНЮ ПОКУПКИ ----------
@dp.callback_query(F.data == "buy_key")
async def buy_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔫 Standoff 2", callback_data="so2_menu")],
        [InlineKeyboardButton(text="🎯 PUBG Mobile", callback_data="pubg_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", 
                             caption="🎮 <b>Выберите игру:</b>"),
        reply_markup=kb
    )

# ---------- МЕНЮ STANDOFF 2 (КАК БЫЛО) ----------
@dp.callback_query(F.data == "so2_menu")
async def so2_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Plutonium Non Root", callback_data="plut_info")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", 
                             caption="⚙️ <b>Standoff 2</b>\nВыберите версию:"),
        reply_markup=kb
    )

@dp.callback_query(F.data == "plut_info")
async def plut_info_callback(call: types.CallbackQuery):
    await call.answer()
    desc = ("🔴 <b>Plutonium для Standoff 2</b>\n\n"
            "🦾 Чит без рута\n\n"
            "<b>Функции:</b>\n"
            "• Aimbot\n• Wallhack\n• ESP\n• И многое другое")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней - 150₴ / 3.5$", callback_data="so2_7"),
         InlineKeyboardButton(text="30 дней - 300₴ / 7$", callback_data="so2_30")],
        [InlineKeyboardButton(text="90 дней - 700₴ / 16.5$", callback_data="so2_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc),
        reply_markup=kb
    )

# ---------- МЕНЮ PUBG ----------
@dp.callback_query(F.data == "pubg_menu")
async def pubg_menu(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android (все читы)", callback_data="android_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png",
                             caption="🎯 <b>PUBG Mobile</b>\n\nВыберите платформу:"),
        reply_markup=kb
    )

# ---------- ANDROID МЕНЮ (ВСЕ ЧИТЫ) ----------
@dp.callback_query(F.data == "android_menu")
async def android_menu(call: types.CallbackQuery):
    await call.answer()
    desc = "🤖 <b>PUBG Mobile - Android</b>\n\nВыберите чит:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Zolo Cheat", callback_data="pubg_zolo")],
        [InlineKeyboardButton(text="⚡ Impact VIP", callback_data="pubg_impact")],
        [InlineKeyboardButton(text="👑 King Mod", callback_data="pubg_king")],
        [InlineKeyboardButton(text="💥 Inferno", callback_data="pubg_inferno")],
        [InlineKeyboardButton(text="🎮 Zolo CIS", callback_data="pubg_zolo_cis")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="pubg_menu")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=desc),
        reply_markup=kb
    )

# ---------- ФУНКЦИЯ ДЛЯ ОПИСАНИЙ ЧИТОВ ----------
def get_pubg_description(cheat: str) -> str:
    desc = {
        "zolo": "🔥 <b>Zolo Cheat</b>\n\n"
                "🛡️ <b>Функции:</b>\n"
                "• Aimbot\n• Wallhack\n• Радар\n• Без Root\n\n"
                "📱 Android 7+",
        
        "impact": "⚡ <b>Impact VIP</b>\n\n"
                  "🚀 <b>Элитные функции:</b>\n"
                  "• Улучшенный Aimbot\n• ESP\n• Без банов\n\n"
                  "💎 Премиум качество",
        
        "king": "👑 <b>King Mod</b>\n\n"
                "👑 <b>Особенности:</b>\n"
                "• Премиум Aimbot\n• Полный ESP\n• Скин-чейнджер",
        
        "inferno": "💥 <b>Inferno Cheat</b>\n\n"
                   "🔥 <b>Уникально:</b>\n"
                   "• Имба-режим\n• Невидимость\n• Авто-стрельба",
        
        "zolo_cis": "🎮 <b>Zolo CIS Edition</b>\n\n"
                    "⚙️ <b>Для СНГ:</b>\n"
                    "• Оптимизация\n• Низкие требования\n• Стабильность"
    }
    return desc.get(cheat, "Описание временно отсутствует")

# ---------- ОБРАБОТЧИКИ ДЛЯ PUBG ЧИТОВ ----------
@dp.callback_query(F.data == "pubg_zolo")
async def pubg_zolo(call: types.CallbackQuery):
    await call.answer()
    desc = get_pubg_description("zolo")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 85₴", callback_data="pay_bank_zolo_1"),
         InlineKeyboardButton(text="3 дня - 180₴", callback_data="pay_bank_zolo_3")],
        [InlineKeyboardButton(text="7 дней - 325₴", callback_data="pay_bank_zolo_7"),
         InlineKeyboardButton(text="14 дней - 400₴", callback_data="pay_bank_zolo_14")],
        [InlineKeyboardButton(text="30 дней - 690₴", callback_data="pay_bank_zolo_30"),
         InlineKeyboardButton(text="60 дней - 1000₴", callback_data="pay_bank_zolo_60")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="android_menu")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/opz3nu.png", caption=desc),
        reply_markup=kb
    )

@dp.callback_query(F.data == "pubg_impact")
async def pubg_impact(call: types.CallbackQuery):
    await call.answer()
    desc = get_pubg_description("impact")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 115₴", callback_data="pay_bank_impact_1"),
         InlineKeyboardButton(text="7 дней - 480₴", callback_data="pay_bank_impact_7")],
        [InlineKeyboardButton(text="30 дней - 1170₴", callback_data="pay_bank_impact_30")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="android_menu")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/9ztxkj.png", caption=desc),
        reply_markup=kb
    )

@dp.callback_query(F.data == "pubg_king")
async def pubg_king(call: types.CallbackQuery):
    await call.answer()
    desc = get_pubg_description("king")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 100₴", callback_data="pay_bank_king_1"),
         InlineKeyboardButton(text="7 дней - 425₴", callback_data="pay_bank_king_7")],
        [InlineKeyboardButton(text="30 дней - 1060₴", callback_data="pay_bank_king_30")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="android_menu")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/vyhlec.png", caption=desc),
        reply_markup=kb
    )

@dp.callback_query(F.data == "pubg_inferno")
async def pubg_inferno(call: types.CallbackQuery):
    await call.answer()
    desc = get_pubg_description("inferno")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 80₴", callback_data="pay_bank_inferno_1"),
         InlineKeyboardButton(text="3 дня - 200₴", callback_data="pay_bank_inferno_3")],
        [InlineKeyboardButton(text="7 дней - 350₴", callback_data="pay_bank_inferno_7"),
         InlineKeyboardButton(text="15 дней - 530₴", callback_data="pay_bank_inferno_15")],
        [InlineKeyboardButton(text="30 дней - 690₴", callback_data="pay_bank_inferno_30"),
         InlineKeyboardButton(text="60 дней - 950₴", callback_data="pay_bank_inferno_60")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="android_menu")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/5vtpq1.png", caption=desc),
        reply_markup=kb
    )

@dp.callback_query(F.data == "pubg_zolo_cis")
async def pubg_zolo_cis(call: types.CallbackQuery):
    await call.answer()
    desc = get_pubg_description("zolo_cis")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день - 70₴", callback_data="pay_bank_zolo_cis_1"),
         InlineKeyboardButton(text="3 дня - 150₴", callback_data="pay_bank_zolo_cis_3")],
        [InlineKeyboardButton(text="7 дней - 250₴", callback_data="pay_bank_zolo_cis_7"),
         InlineKeyboardButton(text="14 дней - 350₴", callback_data="pay_bank_zolo_cis_14")],
        [InlineKeyboardButton(text="30 дней - 700₴", callback_data="pay_bank_zolo_cis_30"),
         InlineKeyboardButton(text="60 дней - 900₴", callback_data="pay_bank_zolo_cis_60")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="android_menu")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/deicc2.png", caption=desc),
        reply_markup=kb
    )

# ---------- ОБРАБОТЧИКИ ОПЛАТЫ (ДЛЯ ВСЕХ ЧИТОВ) ----------
@dp.callback_query(F.data.startswith("pay_bank_"))
async def handle_payment(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    parts = call.data.replace("pay_bank_", "").split("_")
    product = parts[0]  # zolo, impact, king, inferno, zolo_cis, so2
    days = parts[1]
    
    await state.update_data(product=product, days=days, method="bank")
    
    # Определяем цену
    if product == "so2":
        price = SO2_PRICES[days]['uah']
    else:
        price = PUBG_PRICES[product][days]
    
    cap = (f"💳 <b>Оплата банковской картой</b>\n\n"
           f"💰 <b>Сумма:</b> {price} грн\n"
           f"💳 <b>Карта:</b> <code>{CARD}</code>\n"
           f"❗ <b>Комментарий:</b> За цифрові товари\n\n"
           f"📸 После оплаты пришлите скриншот")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="send_receipt")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=cap),
        reply_markup=kb
    )

# ---------- ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (ЧЕКИ, АДМИНКА) ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ ----------
# ... (весь остальной код с обработкой чеков, админ-командами и т.д.)
