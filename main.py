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

# --- ЦЕНЫ ДЛЯ СТАНДОФФ ---
SO2_PRICES = {
    "7": {"uah": 150, "usd": 3.5},
    "30": {"uah": 300, "usd": 7},
    "90": {"uah": 700, "usd": 16.5}
}

# --- ЦЕНЫ ДЛЯ PUBG ЧИТОВ ---
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

# --- ФУНКЦИИ CRYPTOBOT ---
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

# ---------- ГЛАВНОЕ МЕНЮ ----------
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

# ---------- СТАТУС ----------
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

# ---------- STANDOFF 2 ----------
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
        [InlineKeyboardButton(text="7 дней - 150₴ / 3.5$", callback_data="pay_bank_so2_7"),
         InlineKeyboardButton(text="30 дней - 300₴ / 7$", callback_data="pay_bank_so2_30")],
        [InlineKeyboardButton(text="90 дней - 700₴ / 16.5$", callback_data="pay_bank_so2_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]
    ])
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc),
        reply_markup=kb
    )

# ---------- PUBG ----------
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

# ---------- ANDROID МЕНЮ ----------
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

# ---------- ФУНКЦИЯ ОПИСАНИЙ ----------
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

# ---------- ZOLO ----------
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

# ---------- IMPACT ----------
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

# ---------- KING ----------
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

# ---------- INFERNO ----------
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

# ---------- ZOLO CIS ----------
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

# ---------- ОБРАБОТЧИК ОПЛАТЫ ----------
@dp.callback_query(F.data.startswith("pay_bank_"))
async def handle_payment(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    parts = call.data.replace("pay_bank_", "").split("_")
    product = parts[0]
    days = parts[1]
    
    await state.update_data(product=product, days=days, method="bank")
    
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

# ---------- ОТПРАВКА ЧЕКА ----------
@dp.callback_query(F.data == "send_receipt")
async def receipt_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("📸 <b>Отправьте скриншот чека</b>")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    if not message.photo:
        await message.answer("❌ Отправьте фото чека")
        return
    
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}_{data['product']}_{data['days']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    
    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"🔔 <b>Чек от {message.from_user.id}</b>\nТовар: {data['product']}\nТариф: {data['days']} дней",
        reply_markup=adm_kb
    )
    
    await message.answer("✅ Чек отправлен!")
    await state.clear()

# ---------- РЕШЕНИЕ АДМИНА ----------
@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔️ Доступ запрещен")
        return
    
    parts = call.data.split("_")
    if parts[1] == "ok":
        await state.update_data(target_id=int(parts[2]), product=parts[3], days=parts[4])
        await call.message.answer("📎 <b>Отправьте файл</b>")
        await state.set_state(OrderState.waiting_for_admin_file)
        await call.answer("✅ Одобрено")
    else:
        await bot.send_message(int(parts[2]), "❌ Оплата отклонена")
        await call.message.delete()
        await call.answer("❌ Отклонено")

# ---------- ФАЙЛ ОТ АДМИНА ----------
@dp.message(OrderState.waiting_for_admin_file)
async def admin_file_input(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    file_id = None
    file_text = None
    
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_text = message.text
    
    await state.update_data(file=file_id, file_text=file_text)
    await message.answer("🔑 <b>Введите ключ</b>")
    await state.set_state(OrderState.waiting_for_admin_key)

# ---------- КЛЮЧ ОТ АДМИНА ----------
@dp.message(OrderState.waiting_for_admin_key)
async def admin_key_input(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    data = await state.get_data()
    target_id = int(data['target_id'])
    days = int(data['days'])
    
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, expiry_date, product_name, subscribed_at, banned) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?), 0)
    ''', (target_id, expiry_date, data['product'], target_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    text = f"💎 <b>Заказ активирован!</b>\n\n📅 До: {expiry_date}\n🔑 Ключ: <code>{message.text}</code>"
    
    try:
        if data.get('file'):
            await bot.send_document(target_id, data['file'], caption=text)
        else:
            await bot.send_message(target_id, text)
        
        await message.answer("✅ Готово!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()

# ---------- АДМИН-КОМАНДЫ ----------
@dp.message(Command("set_status"))
async def set_status(message: types.Message):
    if message.from_user.id != ADMIN_ID: 
        return
    
    new_status = message.text.replace("/set_status ", "").strip()
    cursor.execute('UPDATE settings SET value = ? WHERE key = "cheat_status"', (new_status,))
    conn.commit()
    await message.answer(f"✅ Статус обновлен на: {new_status}")

@dp.message(Command("broadcast"))
async def broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.answer("📢 <b>Отправь сообщение для рассылки</b>")
    await state.set_state(OrderState.broadcast_text)

@dp.message(OrderState.broadcast_text)
async def broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    cursor.execute('SELECT user_id FROM users WHERE banned = 0')
    users = cursor.fetchall()
    
    if not users:
        await message.answer("📭 Нет пользователей")
        await state.clear()
        return
    
    status = await message.answer(f"⏳ Рассылка {len(users)} пользователям...")
    
    success = 0
    for (user_id,) in users:
        try:
            if message.text:
                await bot.send_message(user_id, message.text)
            elif message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await bot.send_video(user_id, message.video.file_id, caption=message.caption)
            elif message.document:
                await bot.send_document(user_id, message.document.file_id, caption=message.caption)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    await status.edit_text(f"✅ Разослано: {success}/{len(users)}")
    await state.clear()

@dp.message(Command("ban"))
async def ban_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ /ban [id] [причина]")
        return
    
    parts = args[1].split(maxsplit=1)
    target_id = int(parts[0])
    reason = parts[1] if len(parts) > 1 else "Нарушение правил"
    
    cursor.execute('UPDATE users SET banned = 1, ban_reason = ? WHERE user_id = ?', (reason, target_id))
    conn.commit()
    
    try:
        await bot.send_message(target_id, f"⛔️ <b>Вы заблокированы</b>\nПричина: {reason}")
    except:
        pass
    
    await message.answer(f"✅ Пользователь {target_id} заблокирован")

@dp.message(Command("unban"))
async def unban_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ /unban [id]")
        return
    
    target_id = int(args[1])
    
    cursor.execute('UPDATE users SET banned = 0, ban_reason = NULL WHERE user_id = ?', (target_id,))
    conn.commit()
    
    try:
        await bot.send_message(target_id, f"✅ <b>Вы разблокированы</b>")
    except:
        pass
    
    await message.answer(f"✅ Пользователь {target_id} разблокирован")

@dp.message(Command("users"))
async def users_count(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cursor.execute('SELECT COUNT(*) FROM users')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1')
    banned = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', 
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
    active = cursor.fetchone()[0]
    
    await message.answer(f"👥 Всего: {total}\n✅ Активных: {active}\n⛔ Забанено: {banned}")

# ---------- ЗАПУСК ----------
async def main():
    print("🚀 Бот запущен!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
