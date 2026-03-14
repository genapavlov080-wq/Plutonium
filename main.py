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

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CARD = "4441111008011946"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry_date TEXT, product_name TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
conn.commit()

class OrderState(StatesGroup):
    waiting_for_receipt = State()
    waiting_for_broadcast = State()
    waiting_for_file = State()
    waiting_for_key_delivery = State()

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

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📊 Статус", callback_data="check_status")],
        [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/IllyaGarant")]
    ])

# --- ОСНОВНЫЕ ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    photo = "https://files.catbox.moe/916cwt.png"
    cap = "<b>Welcome to Plutonium Store.</b>\n\nВыберите нужный раздел в меню ниже 👇"
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_media(media=InputMediaPhoto(media=photo, caption=cap), reply_markup=main_kb())
    else:
        await event.answer_photo(photo=photo, caption=cap, reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (call.from_user.id,))
    res = cursor.fetchone()
    text = (f"👤 <b>Ваш профиль</b>\n\n🆔 ID: <code>{call.from_user.id}</code>\n"
            f"📦 Продукт: <b>{res[1] if res and res[1] else '—'}</b>\n"
            f"⏳ Подписка: {get_time_left(res[0]) if res and res[0] else '—'}")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=text), reply_markup=main_kb())

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔫 Standoff 2", callback_data="so2_menu")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 Выберите дисциплину:"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📱 Non Root", callback_data="nonroot_info")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="⚙️ Тип установки:"), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_info")
async def nonroot_info(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💎 Plutonium", callback_data="plut_desc")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="<b>📱 Non Root:</b> Без Root прав, полная безопасность."), reply_markup=kb)

@dp.callback_query(F.data == "plut_desc")
async def plut_desc(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="7 дней - 150 грн", callback_data="pay_7")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="nonroot_info")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption="🔴 <b>Plutonium Update!</b>\n\nФункционал: краш игроков, авто-победа, невидимость."), reply_markup=kb)

# --- ЛОГИКА ОПЛАТЫ И ВЫДАЧИ ---

@dp.callback_query(F.data.startswith("pay_"))
async def pre_pay(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(item="Plutonium", days=7)
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💳 Карта: <code>{CARD}</code>\n❗ <b>КОММЕНТАРИЙ:</b> <code>За цифрові товари</code>"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Я оплатил", callback_data="confirm_send")]]))

@dp.callback_query(F.data == "confirm_send")
async def ask_photo(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 Пришлите чек:")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>Чек от @{message.from_user.username}</b>",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}")]]))
    await message.answer("✅ Чек принят!")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_ok_"))
async def adm_ok(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(target_id=call.data.split("_")[2])
    await call.message.answer("Введите ФАЙЛ:")
    await state.set_state(OrderState.waiting_for_file)

@dp.message(OrderState.waiting_for_file)
async def get_file(message: types.Message, state: FSMContext):
    await state.update_data(cheat_file=message.document.file_id if message.document else message.text, is_doc=bool(message.document))
    await message.answer("Введите КЛЮЧ:")
    await state.set_state(OrderState.waiting_for_key_delivery)

@dp.message(OrderState.waiting_for_key_delivery)
async def final_delivery(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    # Продление в БД
    expiry = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', (expiry, "Plutonium", data['target_id']))
    conn.commit()
    
    # Отправка юзеру
    if data.get('is_doc'): await bot.send_document(data['target_id'], data['cheat_file'])
    else: await bot.send_message(data['target_id'], f"📂 Ссылка: {data['cheat_file']}")
    await bot.send_message(data['target_id'], f"💎 Ключ: <code>{message.text}</code>")
    await message.answer("✅ Выдано и подписка продлена.")
    await state.clear()

@dp.callback_query(F.data == "check_status")
async def check_status(call: types.CallbackQuery):
    await call.answer(f"Статус: {get_cheat_status()}", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
