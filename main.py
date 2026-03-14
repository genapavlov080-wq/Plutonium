import asyncio
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.enums import ParseMode # Добавили импорт для стилей

TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CARD = "4441111008011946"

# Настраиваем бота с поддержкой HTML по умолчанию
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, expiry_date TEXT, product_name TEXT)''')
conn.commit()

class OrderState(StatesGroup):
    waiting_for_receipt = State()

# --- ФУНКЦИИ ВРЕМЕНИ ---
def get_time_left(expiry_str):
    if not expiry_str: return "Отсутствует"
    try:
        expiry_dt = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        diff = expiry_dt - now
        if diff.total_seconds() <= 0: return "Истекла"
        days = diff.days
        hours = diff.seconds // 3600
        return f"<b>{days}</b> дн. <b>{hours}</b> час."
    except: return "Ошибка данных"

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), 
         InlineKeyboardButton(text="💬 Отзывы", callback_data="reviews")],
        [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/IllyaGarant")]
    ])

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_handler(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    
    caption = "<b>Welcome to Plut.</b>\n\nВыберите нужный раздел в меню ниже 👇"
    photo = "https://files.catbox.moe/916cwt.png"
    
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_media(media=InputMediaPhoto(media=photo, caption=caption), reply_markup=main_kb())
    else:
        await event.answer_photo(photo=photo, caption=caption, reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (call.from_user.id,))
    res = cursor.fetchone()
    
    status = "Админ" if call.from_user.id == ADMIN_ID else ("Покупатель" if res and res[0] else "Пользователь")
    product = res[1] if res and res[1] else "Нет активных ключей"
    time_left = get_time_left(res[0]) if res and res[0] else "—"

    text = (f"👤 <b>Ваш профиль</b>\n\n"
            f"🆔 ID: <code>{call.from_user.id}</code>\n"
            f"👑 Статус: <b>{status}</b>\n"
            f"📦 Продукт: <b>{product}</b>\n"
            f"⏳ Истекает через: {time_left}")
    
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=text), reply_markup=main_kb())

# --- ПОКУПКА (УКР БАНКИ) ---

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Standoff 2", callback_data="so2_menu")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выберите дисциплину:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Non Root", callback_data="nonroot_info")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="📱 <b>Выберите тип установки:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_info")
async def nonroot_info(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Plutonium", callback_data="plut_desc")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="🔧 <b>Non Root версия</b>\nРаботает без рут прав."), reply_markup=kb)

@dp.callback_query(F.data == "plut_desc")
async def plut_desc(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Plutonium - 7 days", callback_data="pay_7")],
        [InlineKeyboardButton(text="Plutonium - 30 days", callback_data="pay_30")],
        [InlineKeyboardButton(text="Plutonium - 90 days", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nonroot_info")]
    ])
    desc = (
        "🔴 <b>Обновление Plutonium!</b>\n\n"
        "[+] Функция краша игроков\n"
        "[+] Скрытие на записи экрана\n"
        "[+] Исправлена невидимость"
    )
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def choose_pay_method(call: types.CallbackQuery, state: FSMContext):
    days = call.data.split("_")[1]
    price = {"7": "150", "30": "300", "90": "700"}[days]
    await state.update_data(item=f"Plutonium - {days} days", price=price, days=int(days))
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 Оплата на карту (УкрБанк)", callback_data="bank_transfer")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="plut_desc")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💎 <b>Товар:</b> Plutonium {days} дн.\n💰 <b>Цена:</b> {price} грн\n\nВыберите способ оплаты:"), reply_markup=kb)

@dp.callback_query(F.data == "bank_transfer")
async def bank_transfer(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = (f"💳 <b>Реквизиты:</b>\n<code>{CARD}</code>\n"
            f"💰 <b>Сумма:</b> {data['price']} грн\n"
            f"❗️ <b>Комментарий:</b> За цифрові товари\n\n"
            "Скиньте фото чека после оплаты:")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=text), reply_markup=None)
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def get_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>Заказ!</b>\nТовар: {data['item']}\nЮзер: @{message.from_user.username}", reply_markup=kb)
    await message.answer("✅ Чек отправлен на проверку!")
    await state.clear()

# --- АДМИНКА ---
@dp.callback_query(F.data.startswith("adm_"))
async def admin_action(call: types.CallbackQuery):
    parts = call.data.split("_")
    action, user_id = parts[1], parts[2]
    
    if action == "ok":
        days = int(parts[3])
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', 
                       (expiry_date, f"Plutonium ({days} дн.)", user_id))
        conn.commit()
        
        await bot.send_message(user_id, f"✅ <b>Ваша оплата одобрена!</b>\nКлюч активирован на {days} дней. Проверьте <b>Профиль</b>.")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🟢 <b>ОДОБРЕНО</b>")
    else:
        await bot.send_message(user_id, "❌ <b>Ваша оплата отклонена.</b>")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 <b>ОТКЛОНЕНО</b>")

# --- РАССЫЛКА ---
@dp.message(Command("send_all"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/send_all ", "")
    cursor.execute('SELECT user_id FROM users')
    count = 0
    for row in cursor.fetchall():
        try:
            await bot.send_message(row[0], text)
            count += 1
        except: continue
    await message.answer(f"✅ Рассылка завершена. Получили: {count} чел.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
