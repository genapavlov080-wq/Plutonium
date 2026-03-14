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

# --- ЦЕНЫ ---
PRICES = {
    "7": {"uah": 150, "usd": 3.5},
    "30": {"uah": 300, "usd": 7},
    "90": {"uah": 700, "usd": 16.5}
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
    waiting_for_payment_method = State()

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

def get_payment_methods_keyboard(days):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 Укр банк (карта)", callback_data=f"bank_{days}")],
        [InlineKeyboardButton(text="💎 CryptoBot (USDT/ТОН)", callback_data=f"crypto_{days}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="plut_info")]
    ])
    return kb

# --- ФУНКЦИИ CRYPTOBOT ---
async def create_crypto_invoice(user_id, amount, days):
    url = f"{CRYPTO_API}/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    data = {
        "asset": "USDT",
        "amount": amount,
        "description": f"Plutonium - {days} дней",
        "paid_btn_name": "openBot",
        "paid_btn_url": f"https://t.me/{(await bot.get_me()).username}",
        "payload": f"{user_id}|{days}"
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

# --- ХЕНДЛЕРЫ ---

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
    await message.answer_photo(photo="https://files.catbox.moe/916cwt.png", caption=caption, reply_markup=get_main_keyboard())

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
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=caption), reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "check_status")
async def check_status(call: types.CallbackQuery):
    await call.answer()
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=f"📊 <b>Статус ПО:</b> {status}"), reply_markup=kb)

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
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=cap), 
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]]))

@dp.callback_query(F.data == "show_reviews")
async def reviews_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Канал с отзывами", url="https://t.me/plutoniumrewiews")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐ <b>Наши отзывы</b>"), reply_markup=kb)

@dp.callback_query(F.data == "buy_key")
async def buy_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔫 Standoff 2", callback_data="so2_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выбор игры</b>"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Plutonium Non Root", callback_data="plut_info")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="⚙️ <b>Выберите версию</b>"), reply_markup=kb)

@dp.callback_query(F.data == "plut_info")
async def plut_info_callback(call: types.CallbackQuery):
    await call.answer()
    desc = "🔴 <b>Plutonium модификация</b>\n\n🦾 Чит без рута"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Plutonium - 7 дней", callback_data="select_7")],
        [InlineKeyboardButton(text="Plutonium - 30 дней", callback_data="select_30")],
        [InlineKeyboardButton(text="Plutonium - 90 дней", callback_data="select_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=kb)

@dp.callback_query(F.data.startswith("select_"))
async def select_period(call: types.CallbackQuery):
    await call.answer()
    days = call.data.replace("select_", "")
    
    desc = (f"🦾 <b>Plutonium APK</b>\n\n"
            f"💰 <b>Цены:</b>\n"
            f"├ 7 дней: 3.5$ / 150 грн\n"
            f"├ 30 дней: 7$ / 300 грн\n"
            f"└ 90 дней: 16.5$ / 700 грн\n\n"
            f"💳 <b>Выберите способ оплаты:</b>")
    
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), 
                                  reply_markup=get_payment_methods_keyboard(days))

@dp.callback_query(F.data.startswith("bank_"))
async def bank_payment(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    days = call.data.replace("bank_", "")
    await state.update_data(days=days, method="bank")
    
    cap = (f"💳 <b>Оплата картой</b>\n\n"
           f"💰 <b>Сумма:</b> {PRICES[days]['uah']} грн\n"
           f"💳 <b>Карта:</b> <code>{CARD}</code>\n"
           f"❗ <b>Комментарий:</b> За цифрові товари\n\n"
           f"📸 После оплаты пришлите скриншот")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="send_receipt")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=cap), reply_markup=kb)

@dp.callback_query(F.data.startswith("crypto_"))
async def crypto_payment(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    days = call.data.replace("crypto_", "")
    amount = PRICES[days]['usd']
    
    invoice = await create_crypto_invoice(call.from_user.id, amount, days)
    
    if not invoice:
        await call.message.edit_text("❌ Ошибка создания платежа")
        return
    
    cursor.execute('''
        INSERT INTO crypto_payments (payment_id, user_id, amount, days, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (str(invoice["invoice_id"]), call.from_user.id, amount, days, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    cap = (f"💎 <b>Оплата CryptoBot</b>\n\n"
           f"💰 <b>Сумма:</b> {amount}$\n"
           f"📅 <b>Тариф:</b> {days} дней")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Оплатить", url=invoice["pay_url"])],
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_crypto_{invoice['invoice_id']}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=cap), reply_markup=kb)

@dp.callback_query(F.data.startswith("check_crypto_"))
async def check_crypto_payment_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    payment_id = int(call.data.replace("check_crypto_", ""))
    
    payment_info = await check_crypto_payment(payment_id)
    
    if payment_info and payment_info.get("status") == "paid":
        cursor.execute('SELECT days FROM crypto_payments WHERE payment_id = ?', (str(payment_id),))
        res = cursor.fetchone()
        
        if res:
            days = res[0]
            target_id = call.from_user.id
            expiry_date = (datetime.now() + timedelta(days=int(days))).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?
            ''', (expiry_date, "Plutonium", target_id))
            cursor.execute('UPDATE crypto_payments SET status = "paid" WHERE payment_id = ?', (str(payment_id),))
            conn.commit()
            
            await call.message.edit_text(
                f"✅ <b>Оплата подтверждена!</b>\n\n📅 Подписка до {expiry_date}"
            )
            
            await bot.send_message(
                ADMIN_ID,
                f"💰 <b>Новый крипто-платёж</b>\n👤 {target_id}\n📅 {days} дней\n💵 {PRICES[days]['usd']}$"
            )
    else:
        await call.message.answer("⏳ Платёж ещё не подтверждён")

@dp.callback_query(F.data == "send_receipt")
async def receipt_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("📸 <b>Отправьте скриншот чека</b>")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    file_id = None
    file_type = None
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
        file_id = message.document.file_id
        file_type = "document"
    else:
        await message.answer("❌ Отправьте изображение")
        return
    
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    
    caption = f"🔔 <b>Чек от {message.from_user.id}</b>\nТариф: {data['days']} дней"
    
    if file_type == "photo":
        await bot.send_photo(ADMIN_ID, file_id, caption=caption, reply_markup=adm_kb)
    else:
        await bot.send_document(ADMIN_ID, file_id, caption=caption, reply_markup=adm_kb)
    
    await message.answer("✅ Чек отправлен!")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔️ Доступ запрещен")
        return
    
    parts = call.data.split("_")
    if parts[1] == "ok":
        await state.update_data(target_id=int(parts[2]), days=parts[3])
        await call.message.answer("📎 <b>Отправьте файл</b>")
        await state.set_state(OrderState.waiting_for_admin_file)
        await call.answer("✅ Одобрено")
    else:
        await bot.send_message(int(parts[2]), "❌ Оплата отклонена")
        await call.message.delete()
        await call.answer("❌ Отклонено")

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
    ''', (target_id, expiry_date, "Plutonium", target_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    success_text = f"💎 <b>Заказ активирован!</b>\n\n📅 До: {expiry_date}\n\n"
    
    try:
        if data.get('file'):
            if data['file_text']:
                await bot.send_message(target_id, success_text + f"📝 {data['file_text']}")
                await bot.send_message(target_id, f"🔑 <b>Ключ:</b> <code>{message.text}</code>")
            else:
                await bot.send_document(target_id, data['file'], caption=success_text)
                await bot.send_message(target_id, f"🔑 <b>Ключ:</b> <code>{message.text}</code>")
        else:
            await bot.send_message(target_id, success_text + f"🔑 <b>Ключ:</b> <code>{message.text}</code>")
        
        await message.answer("✅ Готово!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()

# --- АДМИН-КОМАНДЫ ---
@dp.message(Command("ban"))
async def ban_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ /ban [id] [причина]")
        return
    
    parts = args[1].split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажите причину")
        return
    
    target_id = int(parts[0])
    reason = parts[1]
    
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
        await message.answer("❌ Использование: /unban [id]")
        return
    
    target_id = int(args[1])
    
    cursor.execute('UPDATE users SET banned = 0, ban_reason = NULL WHERE user_id = ?', (target_id,))
    conn.commit()
    
    try:
        await bot.send_message(target_id, f"✅ <b>Вы разблокированы</b>\nМожете снова пользоваться ботом.")
    except Exception as e:
        pass
    
    await message.answer(f"✅ Пользователь <code>{target_id}</code> разблокирован")


@dp.message(Command("revoke"))
async def revoke_subscription(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Использование: /revoke [id] [причина]")
        return
    
    parts = args[1].split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажите причину аннулирования")
        return
    
    target_id = int(parts[0])
    reason = parts[1]
    
    cursor.execute('''
        UPDATE users 
        SET banned = 1, 
            ban_reason = ?, 
            expiry_date = NULL, 
            product_name = NULL 
        WHERE user_id = ?
    ''', (reason, target_id))
    conn.commit()
    
    try:
        await bot.send_message(target_id, f"⛔️ <b>Подписка аннулирована</b>\nПричина: {reason}")
    except Exception as e:
        pass
    
    await message.answer(f"✅ Подписка пользователя <code>{target_id}</code> аннулирована\nПричина: {reason}")


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
    
    await message.answer("📢 <b>Отправь сообщение для рассылки всем пользователям</b>\n(текст, фото, видео или документ)")
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
    
    success = 0
    fail = 0
    status_msg = await message.answer(f"⏳ Начинаю рассылку {len(users)} пользователям...")
    
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
        except Exception as e:
            fail += 1
    
    await status_msg.edit_text(f"✅ Рассылка завершена!\n✅ Успешно: {success}\n❌ Ошибок: {fail}")
    await state.clear()


@dp.message(Command("users"))
async def users_count(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cursor.execute('SELECT COUNT(*) FROM users')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1')
    banned = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date IS NOT NULL AND expiry_date > ?', 
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
    active = cursor.fetchone()[0]
    
    await message.answer(
        f"👥 <b>Статистика пользователей:</b>\n\n"
        f"📊 Всего: {total}\n"
        f"✅ С активной подпиской: {active}\n"
        f"⛔ Заблокировано: {banned}"
    )


@dp.message(Command("status"))
async def get_status(message: types.Message):
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    await message.answer(f"📊 Текущий статус ПО: {status}")


async def main():
    print("🚀 Бот запущен!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("✅ Команды: /ban, /unban, /revoke, /broadcast, /set_status, /users, /status")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main()) 
