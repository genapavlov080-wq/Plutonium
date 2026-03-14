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

# Создаем бота с правильными настройками для новых версий aiogram
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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

# --- ГЛАВНОЕ МЕНЮ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), 
         InlineKeyboardButton(text="💬 Отзывы", callback_data="show_reviews")], # Исправлено имя
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

@dp.callback_query(F.data == "show_reviews") # Кнопка Отзывы
async def reviews_handler(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Перейти в канал", url="https://t.me/plutoniumrewiews")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐️ <b>Наши отзывы:</b>"), reply_markup=kb)

# --- ЛОГИКА ПОКУПКИ ---

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Standoff 2", callback_data="so2_menu")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выберите игру:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Non Root", callback_data="nonroot_info")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="📱 <b>Тип установки:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_info")
async def nonroot_info(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Plutonium", callback_data="plut_desc")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="🔧 <b>Non Root версия</b>"), reply_markup=kb)

@dp.callback_query(F.data == "plut_desc")
async def plut_desc(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Plutonium - 7 days", callback_data="pay_7")],
        [InlineKeyboardButton(text="Plutonium - 30 days", callback_data="pay_30")],
        [InlineKeyboardButton(text="Plutonium - 90 days", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nonroot_info")]
    ])
    desc = "🔴 <b>Обновление Plutonium!</b>\n\n[+] Краш игроков\n[+] Скрытие записи\n[+] Новая невидимость"
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def choose_bank(call: types.CallbackQuery, state: FSMContext):
    days = call.data.split("_")[1]
    price = {"7": "150", "30": "300", "90": "700"}[days]
    await state.update_data(item=f"Plutonium - {days} days", price=price, days=int(days))
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 Оплата на карту (УкрБанк)", callback_data="go_to_rekvizity")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="plut_desc")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💎 <b>Срок:</b> {days} дн.\n💰 <b>Цена:</b> {price} грн"), reply_markup=kb)

@dp.callback_query(F.data == "go_to_rekvizity")
async def show_rekvizity(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = (f"💳 <b>Реквизиты:</b>\n<code>{CARD}</code>\n"
            f"💰 <b>Сумма:</b> {data['price']} грн\n"
            f"❗️ <b>Комментарий:</b> За цифрові товары")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="send_cheque")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=text), reply_markup=kb)

@dp.callback_query(F.data == "send_cheque")
async def start_upload(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 <b>Отправьте скриншот чека одним сообщением:</b>")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Сообщение админу
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"🔔 <b>Новый заказ!</b>\nТовар: {data['item']}\nЮзер: @{message.from_user.username}", 
                         reply_markup=adm_kb)
    
    # Сообщение клиенту
    await message.answer("✅ <b>Ваша заявка уже на проверке!</b>\nПожалуйста, подождите, администратор скоро подтвердит оплату.")
    await state.clear()

# --- АДМИНКА ---
@dp.callback_query(F.data.startswith("adm_"))
async def admin_process(call: types.CallbackQuery):
    parts = call.data.split("_")
    action, user_id = parts[1], parts[2]
    
    if action == "ok":
        days = int(parts[3])
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', 
                       (expiry_date, f"Plutonium ({days} дн.)", user_id))
        conn.commit()
        await bot.send_message(user_id, "✅ <b>Оплата подтверждена!</b>\nКлюч активирован. Проверьте <b>Профиль</b>.")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🟢 <b>ОДОБРЕНО</b>")
    else:
        await bot.send_message(user_id, "❌ <b>Оплата отклонена.</b>\nСвяжитесь с поддержкой.")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 <b>ОТКЛОНЕНО</b>")

@dp.message(Command("send_all"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/send_all ", "")
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    count = 0
    for row in users:
        try:
            await bot.send_message(row[0], text)
            count += 1
        except: continue
    await message.answer(f"✅ Рассылка завершена. Получили: {count}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
                              
