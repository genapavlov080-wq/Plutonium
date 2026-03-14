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

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry_date TEXT, product_name TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
conn.commit()

class OrderState(StatesGroup):
    waiting_for_receipt = State()
    waiting_for_file = State()
    waiting_for_key = State()

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
    cap = "<b>Plutonium Store — Официальный дистрибьютор ПО.</b>\n\nМы предлагаем только проверенные и безопасные модификации для Standoff 2. Выберите нужный раздел:"
    if isinstance(event, types.CallbackQuery): await event.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=cap), reply_markup=main_kb())
    else: await event.answer_photo(photo="https://files.catbox.moe/916cwt.png", caption=cap, reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (call.from_user.id,))
    res = cursor.fetchone()
    text = (f"👤 <b>Ваш профиль</b>\n🆔 ID: <code>{call.from_user.id}</code>\n📦 Продукт: <b>{res[1] if res and res[1] else '—'}</b>\n⏳ Подписка: {get_time_left(res[0]) if res and res[0] else '—'}")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=text), reply_markup=main_kb())

@dp.callback_query(F.data == "show_reviews")
async def show_reviews(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Перейти в канал с отзывами", url="https://t.me/plutoniumrewiews")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐️ <b>Отзывы о Plutonium</b>\n\nНас выбирают тысячи игроков. Ознакомьтесь с реальными результатами и отзывами наших клиентов в официальном канале."), reply_markup=kb)

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔫 Standoff 2", callback_data="so2_menu")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выберите дисциплину:</b>\nОфициальная поддержка игры Standoff 2."), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📱 Non Root", callback_data="nonroot_info")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="⚙️ <b>Выберите тип установки:</b>\nНаша команда предоставляет только надежные решения."), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_info")
async def nonroot_info(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💎 Plutonium", callback_data="plut_desc")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="🔧 <b>Доступные модификации:</b>\nСтабильная версия без Root прав."), reply_markup=kb)

@dp.callback_query(F.data == "plut_desc")
async def plut_desc(call: types.CallbackQuery):
    desc = ("🔴 <b>Обновление Plutonium!</b>\n\n<blockquote>Функционал:\n• Краш игроков\n• Анти-краш\n• Авто-победа\n• Скрытие на записи\n• Невидимость</blockquote>")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=plut_kb())

# --- ОПЛАТА И АДМИНКА ---
@dp.callback_query(F.data.startswith("pay_"))
async def pre_pay(call: types.CallbackQuery, state: FSMContext):
    days = call.data.split("_")[1]
    price = {"7": "150", "30": "300", "90": "700"}[days]
    await state.update_data(days=int(days), item=f"Plutonium {days} days", price=price)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Я оплатил", callback_data="confirm_send")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="plut_desc")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💳 <b>Карта:</b> <code>{CARD}</code>\n❗ <b>КОММЕНТАРИЙ:</b> <code>За цифрові товари</code>\n💰 <b>Цена:</b> {price} грн\n\nОфициальная оплата. Пришлите чек после перевода."), reply_markup=kb)

@dp.callback_query(F.data == "confirm_send")
async def ask_photo(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 <b>Отправьте чек (скриншот):</b>")
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
        await state.update_data(target_id=user_id, days=parts[3])
        await call.message.answer("Введите ФАЙЛ (или ссылку) для выдачи:")
        await state.set_state(OrderState.waiting_for_file)
    else:
        await bot.send_message(user_id, "❌ <b>Оплата отклонена.</b>")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 <b>ОТКЛОНЕНО</b>")

@dp.message(OrderState.waiting_for_file)
async def get_file(message: types.Message, state: FSMContext):
    await state.update_data(file=message.document.file_id if message.document else message.text, is_doc=bool(message.document))
    await call.message.answer("Введите КЛЮЧ для выдачи:")
    await state.set_state(OrderState.waiting_for_key)

@dp.message(OrderState.waiting_for_key)
async def final_delivery(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    expiry = (datetime.now() + timedelta(days=int(data['days']))).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', (expiry, "Plutonium", data['target_id']))
    conn.commit()
    
    if data.get('is_doc'): await bot.send_document(data['target_id'], data['file'])
    else: await bot.send_message(data['target_id'], f"📂 Файл/Ссылка: {data['file']}")
    await bot.send_message(data['target_id'], f"💎 <b>Ваш ключ:</b> <code>{message.text}</code>")
    await message.answer("✅ Успешно выдано.")
    await state.clear()

@dp.callback_query(F.data == "check_status")
async def check_status(call: types.CallbackQuery):
    await call.answer(f"Статус: {get_cheat_status()}", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
