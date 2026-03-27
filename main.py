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
from aiogram.types import WebAppInfo

WEBAPP_URL = "https://rocket-online.vercel.app"
TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CARD = "4441111008011946"

# CryptoBot API
CRYPTO_TOKEN = "466345:AADMm3mzlC6KGJmwt3r771bUPIx40CMEKhQ"
CRYPTO_API = "https://pay.crypt.bot/api"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- ФУНКЦИЯ ДЛЯ TG PREMIUM ЭМОДЗИ (как в Bot API) ---
def tg_emoji(emoji_id: str, char: str = "●") -> str:
    """Вставляет TG Premium эмодзи через HTML тег"""
    return f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'

# --- КНОПКИ С TG PREMIUM ---
def btn(text: str, callback: str, emoji_id: str = None):
    if emoji_id:
        # Для кнопок используем icon_custom_emoji_id
        return InlineKeyboardButton(text=text, callback_data=callback, icon_custom_emoji_id=emoji_id)
    return InlineKeyboardButton(text=text, callback_data=callback)

def url_btn(text: str, url: str, emoji_id: str = None):
    if emoji_id:
        return InlineKeyboardButton(text=text, url=url, icon_custom_emoji_id=emoji_id)
    return InlineKeyboardButton(text=text, url=url)

# --- ЦЕНЫ ---
PRICES = {
    "so2": {"7": ("150 грн", "3.5$"), "30": ("300 грн", "7$"), "90": ("700 грн", "16.5$")},
    "zolo": {"1": "85 грн", "3": "180 грн", "7": "325 грн", "14": "400 грн", "30": "690 грн", "60": "1000 грн"},
    "impact": {"1": "115 грн", "7": "480 грн", "30": "1170 грн"},
    "king": {"1": "100 грн", "7": "425 грн", "30": "1060 грн"},
    "inferno": {"1": "80 грн", "3": "200 грн", "7": "350 грн", "15": "530 грн", "30": "690 грн", "60": "950 грн"},
    "zolo_cis": {"1": "70 грн", "3": "150 грн", "7": "250 грн", "14": "350 грн", "30": "700 грн", "60": "900 грн"}
}

# --- USD ЦЕНЫ ДЛЯ CRYPTOBOT ---
USD_PRICES = {
    "so2": {"7": 3.5, "30": 7, "90": 16.5}
}

# --- НАЗВАНИЯ ЧИТОВ ---
CHEAT_NAMES = {
    "so2": "🦾 Plutonium APK",
    "zolo": "🔥 Zolo Cheat",
    "impact": "⚡ Impact VIP",
    "king": "👑 King Mod",
    "inferno": "💥 Inferno Cheat",
    "zolo_cis": "🎮 Zolo CIS Edition"
}

# --- ФОТО ЧИТОВ ---
CHEAT_PHOTOS = {
    "so2": "https://files.catbox.moe/eqco0i.png",
    "zolo": "https://files.catbox.moe/opz3nu.png",
    "impact": "https://files.catbox.moe/9ztxkj.png",
    "king": "https://files.catbox.moe/vyhlec.png",
    "inferno": "https://files.catbox.moe/5vtpq1.png",
    "zolo_cis": "https://files.catbox.moe/deicc2.png"
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
        ban_reason TEXT,
        last_key TEXT
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

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("Купить ключ", "buy_key", "5156877291397055163"),
         btn("Мой профиль", "profile", "5904630315946611415")],
        [btn("Наши отзывы", "show_reviews", "5938252440926163756"),
         btn("Статус ПО", "check_status", "5208846279714560254")],
        [url_btn("Plutonium Store", WEBAPP_URL, "5339472242529045815")],
        [url_btn("Техподдержка", "https://t.me/IllyaGarant", "5208539876747662991")]
    ])

def get_back_button(target: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=target)]
    ])

# --- ФУНКЦИИ CRYPTOBOT ---
async def create_crypto_invoice(user_id, amount, days, product):
    url = f"{CRYPTO_API}/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    data = {
        "asset": "USDT",
        "amount": amount,
        "description": f"{CHEAT_NAMES[product]} - {days} дней",
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

# ---------- СТАРТ ----------
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
    
    caption = (f"{tg_emoji('5339472242529045815', '🔥')} <b>Plutonium Store</b>\n\n"
               f"{tg_emoji('5208846279714560254', '📈')} Статус ПО: {status}\n\n"
               f"{tg_emoji('5208657859499282838', '👋')} Добро пожаловать!")
    
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
    
    caption = (f"{tg_emoji('5339472242529045815', '🔥')} <b>Plutonium Store</b>\n\n"
               f"{tg_emoji('5208846279714560254', '📈')} Статус ПО: {status}\n\n"
               f"{tg_emoji('5208657859499282838', '👋')} Добро пожаловать!")
    
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
    
    cursor.execute('SELECT expiry_date, product_name, last_key FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    
    time_left = "Нет активной подписки"
    product = "Нет"
    last_key = ""
    
    if res and res[0] and res[0] is not None:
        try:
            expiry_date = datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S')
            diff = expiry_date - datetime.now()
            
            if diff.total_seconds() > 0:
                days = diff.days
                hours = diff.seconds // 3600
                minutes = (diff.seconds % 3600) // 60
                
                if days > 0:
                    time_left = f"{days} дн. {hours} ч."
                else:
                    time_left = f"{hours} ч. {minutes} мин."
                
                product = res[1] if res[1] else "Plutonium"
                last_key = res[2] if res[2] else ""
            else:
                time_left = "❌ Истекла"
                product = res[1] if res[1] else "Plutonium"
        except Exception as e:
            print(f"Error parsing date: {e}")
            time_left = "Ошибка формата"
            product = res[1] if res[1] else "Plutonium"
    
    cap = (f"{tg_emoji('5904630315946611415', '👤')} <b>Личный кабинет</b>\n\n"
           f"{tg_emoji('6032693626394382504', '🆔')} <b>ID:</b> <code>{user_id}</code>\n"
           f"{tg_emoji('5879770735999717115', '📛')} <b>Имя:</b> {call.from_user.first_name}\n"
           f"{tg_emoji('5814247475141153332', '🔖')} <b>Username:</b> @{call.from_user.username or 'Нет'}\n"
           f"{tg_emoji('6041730074376410123', '📦')} <b>Товар:</b> {product}\n"
           f"{tg_emoji('5891211339170326418', '⏳')} <b>Осталось:</b> {time_left}")
    
    if last_key:
        cap += f"\n{tg_emoji('6048733173171359488', '🔑')} <b>Ваш ключ:</b> <code>{last_key}</code>"
    
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=cap), 
        reply_markup=get_back_button("start")
    )

# ---------- СТАТУС ----------
@dp.callback_query(F.data == "check_status")
async def check_status(call: types.CallbackQuery):
    await call.answer()
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    
    cap = f"{tg_emoji('5208846279714560254', '📊')} <b>Статус ПО:</b> {status}"
    
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=cap), 
        reply_markup=get_back_button("start")
    )

# ---------- ОТЗЫВЫ ----------
@dp.callback_query(F.data == "show_reviews")
async def reviews_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [url_btn("Канал с отзывами", "https://t.me/plutoniumrewiews", "6028171274939797252")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    cap = f"{tg_emoji('5938252440926163756', '⭐')} <b>Наши отзывы</b>"
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption=cap), 
        reply_markup=kb
    )

# ---------- МЕНЮ ПОКУПКИ ----------
@dp.callback_query(F.data == "buy_key")
async def buy_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Standoff 2", "game_so2", "5393134637667094112")],
        [btn("PUBG Mobile", "game_pubg", "6073605466221451561")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    cap = f"{tg_emoji('5938413566624272793', '🎮')} <b>Выберите игру:</b>"
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption=cap),
        reply_markup=kb
    )

# ---------- STANDOFF 2 ----------
@dp.callback_query(F.data == "game_so2")
async def so2_menu(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Plutonium", "cheat_so2", "5339472242529045815")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    cap = (f"{tg_emoji('5393134637667094112', '⚙️')} <b>Standoff 2</b>\n"
           f"{tg_emoji('5938413566624272793', '🎮')} Выберите чит:")
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption=cap),
        reply_markup=kb
    )

# ---------- PUBG ----------
@dp.callback_query(F.data == "game_pubg")
async def pubg_menu(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Zolo", "cheat_zolo", "5451653043089070124")],
        [btn("Impact VIP", "cheat_impact", "5276079251089547977")],
        [btn("King Mod", "cheat_king", "6172520285330214110")],
        [btn("Inferno", "cheat_inferno", "5296273418516187626")],
        [btn("Zolo CIS", "cheat_zolo_cis", "5451841459009379088")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    cap = f"{tg_emoji('6073605466221451561', '🎯')} <b>PUBG Mobile</b>\nВыберите чит:"
    await call.message.edit_media(
        media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption=cap),
        reply_markup=kb
    )

# ---------- ПОКАЗ ЧИТА ----------
async def show_cheat(call: types.CallbackQuery, cheat: str):
    await call.answer()
    
    desc = f"{CHEAT_NAMES[cheat]}\n\n💰 <b>Цены:</b>\n"
    
    for days, price in PRICES[cheat].items():
        days_text = f"{days} дн." if days != "1" else "1 день"
        if cheat == "so2":
            uah, usd = price
            desc += f"├ {days_text}: {usd} / {uah}\n"
        else:
            desc += f"├ {days_text}: {price}\n"
    
    desc += "\n💳 <b>Выберите период:</b>"
    
    buttons = []
    for days in PRICES[cheat].keys():
        days_text = f"{days} дн." if days != "1" else "1 день"
        buttons.append([btn(days_text, f"period_{cheat}_{days}", "5393330385096575682")])
    
    game = "game_so2" if cheat == "so2" else "game_pubg"
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=game)])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await call.message.edit_media(
        media=InputMediaPhoto(media=CHEAT_PHOTOS[cheat], caption=desc),
        reply_markup=kb
    )

# ---------- ОБРАБОТЧИКИ ЧИТОВ ----------
@dp.callback_query(F.data == "cheat_so2")
async def cheat_so2(call: types.CallbackQuery): await show_cheat(call, "so2")
@dp.callback_query(F.data == "cheat_zolo")
async def cheat_zolo(call: types.CallbackQuery): await show_cheat(call, "zolo")
@dp.callback_query(F.data == "cheat_impact")
async def cheat_impact(call: types.CallbackQuery): await show_cheat(call, "impact")
@dp.callback_query(F.data == "cheat_king")
async def cheat_king(call: types.CallbackQuery): await show_cheat(call, "king")
@dp.callback_query(F.data == "cheat_inferno")
async def cheat_inferno(call: types.CallbackQuery): await show_cheat(call, "inferno")
@dp.callback_query(F.data == "cheat_zolo_cis")
async def cheat_zolo_cis(call: types.CallbackQuery): await show_cheat(call, "zolo_cis")

# ---------- ВЫБОР ПЕРИОДА ----------
@dp.callback_query(F.data.startswith("period_"))
async def select_period(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    parts = call.data.split("_")
    cheat = parts[1]
    days = parts[2]
    
    await state.update_data(product=cheat, days=days)
    
    desc = f"{CHEAT_NAMES[cheat]}\n\n📅 {days} дн.\n"
    
    if cheat == "so2":
        uah, usd = PRICES[cheat][days]
        desc += f"💰 {usd} / {uah}"
    else:
        desc += f"💰 {PRICES[cheat][days]}"
    
    desc += "\n\n💳 <b>Выберите способ оплаты:</b>"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Укр Банк", f"bank_{cheat}_{days}", "5393576224729633040")],
        [btn("CryptoBot", f"crypto_{cheat}_{days}", "5390816416184174666")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cheat_{cheat}")]
    ])
    
    await call.message.edit_media(
        media=InputMediaPhoto(media=CHEAT_PHOTOS[cheat], caption=desc),
        reply_markup=kb
    )

# ---------- ОПЛАТА БАНКОМ ----------
@dp.callback_query(F.data.startswith("bank_"))
async def bank_payment(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    parts = call.data.split("_")
    cheat = parts[1]
    days = parts[2]
    
    await state.update_data(product=cheat, days=days, method="bank")
    
    if cheat == "so2":
        uah, _ = PRICES[cheat][days]
        price = uah
    else:
        price = PRICES[cheat][days]
    
    cap = (f"{tg_emoji('5890848474563352982', '💳')} <b>Оплата банковской картой</b>\n\n"
           f"{tg_emoji('5890848474563352982', '💰')} <b>Сумма:</b> {price}\n"
           f"{tg_emoji('5890848474563352982', '💳')} <b>Карта:</b> <code>{CARD}</code>\n"
           f"{tg_emoji('5891105528356018797', '❗')} <b>Комментарий:</b> За цифрові товари\n\n"
           f"{tg_emoji('5769126056262898415', '📸')} После оплаты нажмите кнопку ниже и пришлите скриншот")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Я оплатил", "send_receipt", "5258205968025525531")],
        [btn("Отмена", "start", "5208480322731137426")]
    ])
    
    await call.message.edit_media(
        media=InputMediaPhoto(media=CHEAT_PHOTOS[cheat], caption=cap),
        reply_markup=kb
    )

# ---------- ОПЛАТА CRYPTO ----------
@dp.callback_query(F.data.startswith("crypto_"))
async def crypto_payment(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    parts = call.data.split("_")
    cheat = parts[1]
    days = parts[2]
    
    if cheat == "so2":
        _, usd = PRICES[cheat][days]
        amount = float(usd.replace("$", ""))
    else:
        price_str = PRICES[cheat][days].replace(" грн", "")
        amount = round(int(price_str) / 43, 2)
    
    invoice = await create_crypto_invoice(call.from_user.id, amount, days, cheat)
    
    if not invoice:
        await call.message.edit_text("❌ Ошибка создания платежа", reply_markup=get_back_button("start"))
        return
    
    cursor.execute('''
        INSERT INTO crypto_payments (payment_id, user_id, amount, days, product, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (str(invoice["invoice_id"]), call.from_user.id, amount, days, cheat, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    cap = (f"{tg_emoji('5390816416184174666', '💎')} <b>Оплата через CryptoBot</b>\n\n"
           f"💰 <b>Сумма:</b> {amount}$\n"
           f"📅 <b>Тариф:</b> {days} дней")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [url_btn("💎 Оплатить", invoice["pay_url"])],
        [btn("Проверить оплату", f"check_crypto_{invoice['invoice_id']}", "6039486778597970865")],
        [btn("Отмена", "start", "5208480322731137426")]
    ])
    
    await call.message.edit_media(
        media=InputMediaPhoto(media=CHEAT_PHOTOS[cheat], caption=cap),
        reply_markup=kb
    )

# -------# ---------- ПРОВЕРКА CRYPTO ПЛАТЕЖА ----------
@dp.callback_query(F.data.startswith("check_crypto_"))
async def check_crypto_payment_callback(call: types.CallbackQuery):
    await call.answer()
    payment_id = int(call.data.replace("check_crypto_", ""))
    
    payment_info = await check_crypto_payment(payment_id)
    
    if payment_info and payment_info.get("status") == "paid":
        cursor.execute('SELECT product, days FROM crypto_payments WHERE payment_id = ?', (str(payment_id),))
        res = cursor.fetchone()
        
        if res:
            product, days = res
            target_id = call.from_user.id
            expiry_date = (datetime.now() + timedelta(days=int(days))).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?
            ''', (expiry_date, CHEAT_NAMES[product], target_id))
            cursor.execute('UPDATE crypto_payments SET status = "paid" WHERE payment_id = ?', (str(payment_id),))
            conn.commit()
            
            await call.message.edit_text(
                f"{tg_emoji('5938252440926163756', '✅')} <b>Оплата подтверждена!</b>\n\n📅 Подписка до {expiry_date}",
                reply_markup=get_back_button("start")
            )
            
            await bot.send_message(
                ADMIN_ID,
                f"{tg_emoji('6039486778597970865', '💰')} <b>Новый крипто-платёж</b>\n👤 {target_id}\n📅 {days} дней\n💎 {CHEAT_NAMES[product]}"
            )
    else:
        await call.answer("⏳ Платёж ещё не подтверждён", show_alert=True)

# ---------- ОТПРАВКА ЧЕКА ----------
@dp.callback_query(F.data == "send_receipt")
async def receipt_callback(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get('product') or not data.get('days'):
        await call.message.edit_text(
            "❌ Ошибка: данные заказа утеряны. Начните заново.",
            reply_markup=get_back_button("start")
        )
        await state.clear()
        return
    
    await call.message.answer(f"{tg_emoji('5769126056262898415', '📸')} <b>Отправьте скриншот чека</b> (одним фото)")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    if not data.get('product') or not data.get('days'):
        await message.answer("❌ Ошибка: данные заказа не найдены. Начните заново.")
        await state.clear()
        return
    
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("Одобрить", f"adm_ok_{message.from_user.id}_{data['product']}_{data['days']}", "5208657859499282838")],
        [btn("Отклонить", f"adm_no_{message.from_user.id}", "5208480322731137426")]
    ])
    
    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"{tg_emoji('6039486778597970865', '🔔')} <b>Чек от {message.from_user.id}</b>\n"
                f"📦 Товар: {CHEAT_NAMES[data['product']]}\n"
                f"📅 Тариф: {data['days']} дней",
        reply_markup=adm_kb
    )
    
    await message.answer(f"{tg_emoji('5938252440926163756', '✅')} Чек отправлен администратору! Ожидайте подтверждения.")
    await state.clear()

# ---------- РЕШЕНИЕ АДМИНА ----------
@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔️ Доступ запрещен")
        return
    
    parts = call.data.split("_")
    if parts[1] == "ok":
        await state.update_data(
            target_id=int(parts[2]),
            product=parts[3],
            days=parts[4]
        )
        await call.message.answer(f"{tg_emoji('6037373985400819577', '📎')} <b>Отправьте файл с читом</b> (или текст с инструкцией)")
        await state.set_state(OrderState.waiting_for_admin_file)
        await call.answer("✅ Одобрено")
        await call.message.delete()
    else:
        await bot.send_message(int(parts[2]), f"{tg_emoji('5208480322731137426', '❌')} Ваша оплата была отклонена администратором.")
        await call.message.delete()
        await call.answer("❌ Отклонено")

# ---------- ФАЙЛ ОТ АДМИНА ----------
@dp.message(OrderState.waiting_for_admin_file)
async def admin_file_input(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    data = await state.get_data()
    
    file_id = None
    file_text = None
    
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_text = message.text
    
    await state.update_data(file=file_id, file_text=file_text)
    await message.answer(f"{tg_emoji('6048733173171359488', '🔑')} <b>Введите ключ активации</b>")
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
    
    product_name = CHEAT_NAMES.get(data['product'], "Plutonium")
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, expiry_date, product_name, subscribed_at, banned, last_key) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?), 0, ?)
    ''', (target_id, expiry_date, product_name, target_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message.text))
    conn.commit()
    
    text = (f"{tg_emoji('5938252440926163756', '✅')} <b>Заказ активирован!</b>\n\n"
            f"{tg_emoji('5208474816583063829', '📅')} <b>Действует до:</b> {expiry_date}\n"
            f"{tg_emoji('6048733173171359488', '🔑')} <b>Ключ:</b> <code>{message.text}</code>\n\n"
            f"{tg_emoji('5413879192267805083', '💜')} Благодарим за покупку в Plutonium Store!")
    
    try:
        if data.get('file'):
            await bot.send_document(target_id, data['file'], caption=text)
        elif data.get('file_text'):
            await bot.send_message(target_id, text + f"\n\n{tg_emoji('6039348811363520645', '📝')} {data['file_text']}")
        else:
            await bot.send_message(target_id, text)
        
        await message.answer(f"{tg_emoji('5208422125924275090', '✅')} Готово! Товар выдан пользователю.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}")
    
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
    
    await message.answer(f"{tg_emoji('5208846279714560254', '📢')} <b>Отправь сообщение для рассылки</b> (текст, фото, видео или документ)")
    await state.set_state(OrderState.broadcast_text)

@dp.message(OrderState.broadcast_text)
async def broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    cursor.execute('SELECT user_id FROM users WHERE banned = 0')
    users = cursor.fetchall()
    
    if not users:
        await message.answer("📭 Нет пользователей в базе")
        await state.clear()
        return
    
    status = await message.answer(f"⏳ Начинаю рассылку {len(users)} пользователям...")
    
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
            if success % 10 == 0:
                await status.edit_text(f"⏳ Прогресс: {success}/{len(users)}")
            await asyncio.sleep(0.05)
        except:
            pass
    
    await status.edit_text(f"{tg_emoji('5938252440926163756', '✅')} Рассылка завершена!\n✅ Успешно: {success}\n❌ Ошибок: {len(users)-success}")
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
    
    await message.answer(
        f"👥 <b>Статистика пользователей:</b>\n\n"
        f"📊 Всего: {total}\n"
        f"✅ Активных: {active}\n"
        f"⛔ Забанено: {banned}"
    )

# ---------- ЗАПУСК ----------
async def main():
    print("🚀 Plutonium Store запущен!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"💰 Доступно читов: {len(PRICES)}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
