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

# Фото
IMG_MAIN = "https://files.catbox.moe/5h6fr0.png"
IMG_REVIEWS = "https://files.catbox.moe/3z96th.png"
IMG_SO2 = "https://files.catbox.moe/1u2tb9.png"
IMG_NONROOT = "https://files.catbox.moe/w5b4rw.png"
IMG_PRODUCT = "https://files.catbox.moe/eqco0i.png"

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
async def start(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (user_id,))
    conn.commit()
    
    text = "<b>Welcome to Plut.</b>\nВыберите действие:"
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_media(media=InputMediaPhoto(media=IMG_MAIN, caption=text, parse_mode="HTML"), reply_markup=main_kb())
    else:
        await event.answer_photo(photo=IMG_MAIN, caption=text, reply_markup=main_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    text = f"👤 <b>Профиль</b>\nID: <code>{call.from_user.id}</code>\nСтатус: Покупатель"
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_MAIN, caption=text, parse_mode="HTML"), reply_markup=main_kb())

@dp.callback_query(F.data == "reviews")
async def show_reviews(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➡️ Перейти в канал", url="https://t.me/plutoniumrewiews")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_REVIEWS, caption="⭐️ Отзывы наших клиентов:"), reply_markup=kb)

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Standoff 2", callback_data="so2_menu")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_SO2, caption="🎮 Выберите игру:"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Non Root", callback_data="nonroot_menu")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]])
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_SO2, caption="📱 Выберите тип установки:"), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_menu")
async def nonroot_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Plutonium - 7 days", callback_data="pay_7")],
        [InlineKeyboardButton(text="Plutonium - 30 days", callback_data="pay_30")],
        [InlineKeyboardButton(text="Plutonium - 90 days", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_NONROOT, caption="💎 Выберите тариф:"), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def pay_menu(call: types.CallbackQuery, state: FSMContext):
    data = {"pay_7": ("Plutonium - 7 days", "150"), "pay_30": ("Plutonium - 30 days", "300"), "pay_90": ("Plutonium - 90 days", "700")}
    item, price = data[call.data]
    await state.update_data(item=item, price=price)
    
    text = (f"💳 <b>Оплата: {item}</b>\nЦена: {price} грн\n\n"
            f"Реквизиты: <code>{CARD}</code>\n"
            "❗️Комментарий: За цифрові товари")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил (скинуть чек)", callback_data="send_receipt")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_PRODUCT, caption=text, parse_mode="HTML"), reply_markup=kb)

@dp.callback_query(F.data == "send_receipt")
async def request_receipt(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 Отправьте фото вашего чека (скриншот) прямо сюда:")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def get_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ Чек получен, админ скоро свяжется с вами!")
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>Новый заказ!</b>\n{data['item']}\nСумма: {data['price']} грн\nЮзер: @{message.from_user.username}")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
