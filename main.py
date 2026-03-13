import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

# --- КОНФИГ ---
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

# --- SQLite БАЗА ---
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

def tariffs_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней - 150 грн", callback_data="pay_7")],
        [InlineKeyboardButton(text="30 дней - 300 грн", callback_data="pay_30")],
        [InlineKeyboardButton(text="90 дней - 700 грн", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.from_user.id,))
    conn.commit()
    await message.answer_photo(photo=IMG_MAIN, caption="Welcome to Plut.", reply_markup=main_kb())

@dp.callback_query(F.data == "buy_key")
async def choose_game(call: types.CallbackQuery):
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_SO2, caption="Выберите игру:"), 
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                      [InlineKeyboardButton(text="Standoff 2", callback_data="tariffs")],
                                      [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]]))

@dp.callback_query(F.data == "tariffs")
async def show_tariffs(call: types.CallbackQuery):
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_NONROOT, caption="Выберите тариф:"), reply_markup=tariffs_kb())

@dp.callback_query(F.data.startswith("pay_"))
async def process_pay(call: types.CallbackQuery, state: FSMContext):
    price = {"pay_7": "150", "pay_30": "300", "pay_90": "700"}[call.data]
    days = {"pay_7": "7", "pay_30": "30", "pay_90": "90"}[call.data]
    await state.update_data(days=days, price=price)
    
    text = (f"💳 <b>Оплата на карту:</b>\n<code>{CARD}</code>\n"
            f"Сумма: {price} грн\n❗️Комментарий: За цифрові товари\n\n"
            "После оплаты скиньте фото чека:")
    await call.message.edit_caption(caption=text, reply_markup=None, parse_mode="HTML")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def get_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ Чек отправлен на проверку!")
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"Новый заказ: {data['days']} дней ({data['price']} грн)\nОт: @{message.from_user.username}")
    await state.clear()

# --- РАССЫЛКА ---
@dp.message(Command("send_all"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/send_all ", "")
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    for row in users:
        try: await bot.send_message(row[0], text)
        except: continue
    await message.answer("Рассылка завершена.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
