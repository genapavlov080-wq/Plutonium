import asyncio
import sqlite3
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

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- БАЗА ДАННЫХ (SQLite) ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry_date TEXT, product_name TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
conn.commit()

# --- СОСТОЯНИЯ FSM ---
class OrderState(StatesGroup):
    waiting_for_receipt = State()
    waiting_for_file = State()
    waiting_for_key = State()
    waiting_for_broadcast = State()
    admin_input_file = State()
    admin_input_key = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_cheat_status():
    cursor.execute('SELECT value FROM settings WHERE key = "cheat_status"')
    return cursor.fetchone()[0]

def get_time_left(expiry_str):
    if not expiry_str: return "Отсутствует"
    try:
        expiry_dt = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
        diff = expiry_dt - datetime.now()
        if diff.total_seconds() <= 0: return "Истекла"
        return f"<b>{diff.days}</b> дн. <b>{diff.seconds // 3600}</b> час."
    except: return "—"

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key"), InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⭐ Отзывы", callback_data="show_reviews"), InlineKeyboardButton(text="📊 Статус чита", callback_data="check_status")],
        [InlineKeyboardButton(text="🆘 Официальная поддержка", url="https://t.me/IllyaGarant")]
    ])

def plut_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней - 150 грн", callback_data="pay_7"), InlineKeyboardButton(text="30 дней - 300 грн", callback_data="pay_30")],
        [InlineKeyboardButton(text="90 дней - 700 грн", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nonroot_info")]
    ])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (event.from_user.id,))
    conn.commit()
    cap = "<b>Plutonium Store — Официальный дистрибьютор.</b>\nМы предлагаем только безопасные модификации для Standoff 2."
    if isinstance(event, types.CallbackQuery): await event.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=cap), reply_markup=main_kb())
    else: await event.answer_photo(photo="https://files.catbox.moe/916cwt.png", caption=cap, reply_markup=main_kb())

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Введите текст рассылки:")
    await state.set_state(OrderState.waiting_for_broadcast)

@dp.message(OrderState.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    for row in users:
        try: await message.copy_to(row[0])
        except: pass
    await message.answer("Рассылка завершена.")
    await state.clear()

@dp.callback_query(F.data.startswith("pay_"))
async def pre_pay(call: types.CallbackQuery, state: FSMContext):
    days = call.data.split("_")[1]
    price = {"7": "150", "30": "300", "90": "700"}[days]
    await state.update_data(days=int(days), item=f"Plutonium {days} дней", price=price)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Я оплатил", callback_data="confirm_send")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="plut_desc")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💳 <b>Карта:</b> <code>{CARD}</code>\n💰 <b>К оплате:</b> {price} грн\n❗ <b>КОММЕНТАРИЙ:</b> <code>За цифрові товари</code>"), reply_markup=kb)

@dp.callback_query(F.data == "confirm_send")
async def ask_photo(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 <b>Отправьте скриншот чека в чат:</b>")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>Чек от @{message.from_user.username}</b> (ID: {message.from_user.id})\nТовар: {data['item']}", reply_markup=adm_kb)
    await message.answer("✅ <b>Чек принят!</b> Админ скоро его проверит.")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_"))
async def admin_control(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    action, user_id = parts[1], parts[2]
    if action == "ok":
        await state.update_data(target_id=user_id, days=int(parts[3]))
        await call.message.answer("Введите ФАЙЛ (или ссылку) для выдачи:")
        await state.set_state(OrderState.admin_input_file)
    else:
        await bot.send_message(user_id, "❌ <b>Ваш чек был отклонен.</b>")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 <b>ОТКЛОНЕНО</b>")

@dp.message(OrderState.admin_input_file)
async def get_file(message: types.Message, state: FSMContext):
    await state.update_data(file=message.document.file_id if message.document else message.text, is_doc=bool(message.document))
    await message.answer("Введите КЛЮЧ для выдачи:")
    await state.set_state(OrderState.admin_input_key)

@dp.message(OrderState.admin_input_key)
async def final_delivery(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expiry = (datetime.now() + timedelta(days=data['days'])).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', (expiry, "Plutonium", data['target_id']))
    conn.commit()
    
    if data.get('is_doc'): await bot.send_document(data['target_id'], data['file'])
    else: await bot.send_message(data['target_id'], f"📂 Ссылка: {data['file']}")
    await bot.send_message(data['target_id'], f"💎 <b>Ваш ключ:</b> <code>{message.text}</code>")
    await message.answer("✅ Успешно выдано.")
    await state.clear()

# Остальные функции (profile, check_status, show_reviews) остаются как были...
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
                                
