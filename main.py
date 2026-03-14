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
# Начальный статус чита
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
conn.commit()

class OrderState(StatesGroup):
    waiting_for_receipt = State()
    waiting_for_broadcast = State()
    waiting_for_key_delivery = State()

# --- ФУНКЦИИ ---
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
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), 
         InlineKeyboardButton(text="💬 Отзывы", callback_data="show_reviews")],
        [InlineKeyboardButton(text="📊 Статус чита", callback_data="check_status")],
        [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/IllyaGarant")]
    ])

# --- ОСНОВНЫЕ ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_handler(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    photo = "https://files.catbox.moe/916cwt.png"
    cap = "<b>Welcome to Plut.</b>\n\nВыберите нужный раздел:"
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_media(media=InputMediaPhoto(media=photo, caption=cap), reply_markup=main_kb())
    else:
        await event.answer_photo(photo=photo, caption=cap, reply_markup=main_kb())

@dp.callback_query(F.data == "check_status")
async def status_callback(call: types.CallbackQuery):
    status = get_cheat_status()
    await call.answer(f"Текущий статус:\n{status}", show_alert=True)

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (call.from_user.id,))
    res = cursor.fetchone()
    status = "Админ" if call.from_user.id == ADMIN_ID else ("Покупатель" if res and res[0] else "Пользователь")
    text = (f"👤 <b>Ваш профиль</b>\n🆔 ID: <code>{call.from_user.id}</code>\n"
            f"👑 Статус: <b>{status}</b>\n📦 Продукт: <b>{res[1] if res and res[1] else '—'}</b>\n"
            f"⏳ Подписка: {get_time_left(res[0]) if res and res[0] else '—'}")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=text), reply_markup=main_kb())

# --- АДМИН-КОМАНДЫ (СТАТУС И РАССЫЛКА) ---

@dp.message(Command("setstatus"))
async def cmd_setstatus(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    new_status = message.text.replace("/setstatus ", "")
    if not new_status or new_status == "/setstatus":
        return await message.answer("Пример: <code>/setstatus 🟢 UNDETECTED</code>")
    cursor.execute('UPDATE settings SET value = ? WHERE key = "cheat_status"', (new_status,))
    conn.commit()
    await message.answer(f"✅ Статус изменен на: {new_status}")

@dp.message(Command("send_all"))
async def cmd_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Перешлите мне сообщение (пост), которое хотите разослать всем.")
    await state.set_state(OrderState.waiting_for_broadcast)

@dp.message(OrderState.waiting_for_broadcast)
async def process_broadcast_msg(message: types.Message, state: FSMContext):
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    count = 0
    for row in users:
        try:
            await message.copy_to(row[0])
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await message.answer(f"✅ Рассылка завершена! Получили: {count} чел.")
    await state.clear()

# --- ОСТАЛЬНАЯ ЛОГИКА ПОКУПКИ (БЕЗ ИЗМЕНЕНИЙ ПУТЕЙ) ---

@dp.callback_query(F.data == "show_reviews")
async def reviews_handler(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Канал", url="https://t.me/plutoniumrewiews")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐️ <b>Отзывы:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Standoff 2", callback_data="so2_menu")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выберите игру:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Non Root", callback_data="nonroot_info")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="📱 <b>Тип установки:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_info")
async def nonroot_info(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Plutonium", callback_data="plut_desc")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="🔧 <b>Non Root версия</b>"), reply_markup=kb)

@dp.callback_query(F.data == "plut_desc")
async def plut_desc(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="7 days", callback_data="pay_7")],[InlineKeyboardButton(text="30 days", callback_data="pay_30")],[InlineKeyboardButton(text="90 days", callback_data="pay_90")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="nonroot_info")]])
    desc = "🔴 <b>Обновление Plutonium!</b>\n[+] Краш игроков\n[+] Невидимость"
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def pre_pay(call: types.CallbackQuery, state: FSMContext):
    days = call.data.split("_")[1]
    price = {"7": "150", "30": "300", "90": "700"}[days]
    await state.update_data(item=f"Plutonium - {days} days", price=price, days=int(days))
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇺🇦 Карта", callback_data="go_rekv")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="plut_desc")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💎 Срок: {days} дн.\n💰 Цена: {price} грн"), reply_markup=kb)

@dp.callback_query(F.data == "go_rekv")
async def rekv(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Оплатил", callback_data="send_cheque")],[InlineKeyboardButton(text="❌ Отмена", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💳 Карта: <code>{CARD}</code>\nСумма в гривнах."), reply_markup=kb)

@dp.callback_query(F.data == "send_cheque")
async def start_up(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 Пришлите скриншот чека:")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def get_cheque(message: types.Message, state: FSMContext):
    data = await state.get_data()
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Одобрить и Выдать", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")],[InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 Заказ: {data['item']}\nОт: @{message.from_user.username}", reply_markup=adm_kb)
    await message.answer("✅ <b>Заявка на проверке!</b>\nАдмин выдаст ключ после подтверждения.")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_"))
async def adm_proc(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    action, user_id = parts[1], parts[2]
    if action == "ok":
        days = int(parts[3])
        expiry = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', (expiry, f"Plutonium ({days} дн.)", user_id))
        conn.commit()
        await state.update_data(target_user=user_id)
        await call.message.answer(f"Оплата одобрена. Теперь ПРИШЛИТЕ КЛЮЧ для пользователя (ID: {user_id}):")
        await state.set_state(OrderState.waiting_for_key_delivery)
    else:
        await bot.send_message(user_id, "❌ Оплата отклонена.")
        await call.message.edit_caption(caption="🔴 ОТКЛОНЕНО")

@dp.message(OrderState.waiting_for_key_delivery)
async def deliver_key(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    target_user = data['target_user']
    await bot.send_message(target_user, f"💎 <b>Ваш ключ:</b>\n<code>{message.text}</code>\n\nПриятной игры!")
    await message.answer(f"✅ Ключ успешно доставлен пользователю {target_user}")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
      
                              
