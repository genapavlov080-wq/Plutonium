import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CARD = "4441111008011946"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# БД
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
conn.commit()

class OrderState(StatesGroup):
    waiting_for_receipt = State()

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="💬 Отзывы", callback_data="reviews")],
        [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/IllyaGarant")]
    ])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_handler(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (user_id,))
    conn.commit()
    
    caption = "<b>Welcome to Plut.</b>\nГлавное меню:"
    photo = "https://files.catbox.moe/5h6fr0.png"
    
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_media(media=InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"), reply_markup=main_kb())
    else:
        await event.answer_photo(photo=photo, caption=caption, reply_markup=main_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    text = f"👤 <b>Ваш профиль</b>\n🆔 ID: <code>{call.from_user.id}</code>\nСтатус: Активный"
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=text, parse_mode="HTML"), reply_markup=main_kb())

@dp.callback_query(F.data == "reviews")
async def show_reviews(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Канал с отзывами", url="https://t.me/plutoniumrewiews")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐️ Наши отзывы:", parse_mode="HTML"), reply_markup=kb)

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Standoff 2", callback_data="so2_menu")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 Выберите дисциплину:"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Non Root", callback_data="nonroot_info")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="📱 Выберите тип установки:"), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_info")
async def nonroot_info(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Plutonium", callback_data="plut_desc")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="🔧 Non Root версия\nРаботает полностью без рут прав."), reply_markup=kb)

@dp.callback_query(F.data == "plut_desc")
async def plut_desc(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Plutonium - 7 days", callback_data="pay_7")],
        [InlineKeyboardButton(text="Plutonium - 30 days", callback_data="pay_30")],
        [InlineKeyboardButton(text="Plutonium - 90 days", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nonroot_info")]
    ])
    text = "💎 <b>Plutonium</b>\nЛучший чит для Standoff 2.\n- Без рут прав\n- Обход бана\n- Функционал премиум класса."
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=text, parse_mode="HTML"), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def pay_confirm(call: types.CallbackQuery, state: FSMContext):
    prices = {"pay_7": "150", "pay_30": "300", "pay_90": "700"}
    item = call.data.replace("pay_", "") + " days"
    price = prices[call.data]
    await state.update_data(item=item, price=price)
    
    text = f"💳 <b>Оплата: {item}</b>\nЦена: {price} грн\nРеквизиты: <code>{CARD}</code>\n❗️ Коммент: За цифрові товари"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Я оплатил", callback_data="upload_check")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="plut_desc")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=text, parse_mode="HTML"), reply_markup=kb)

@dp.callback_query(F.data == "upload_check")
async def upload_check(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 Скиньте скриншот чека в чат:")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def get_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"adm_ok_{message.from_user.id}")]])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>Заказ от @{message.from_user.username}</b>\n{data['item']} - {data['price']} грн", reply_markup=kb, parse_mode="HTML")
    await message.answer("✅ Чек отправлен админу!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
