import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types  # ВОТ ТУТ ОШИБКА БЫЛА
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

# --- КНОПКИ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="💬 Отзывы", callback_data="reviews")],
        [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/IllyaGarant")]
    ])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.from_user.id,))
    conn.commit()
    await message.answer_photo(photo="https://files.catbox.moe/5h6fr0.png", caption="Welcome to Plut.", reply_markup=main_kb())

@dp.callback_query(F.data == "start")
async def back_to_start(call: types.CallbackQuery):
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption="Welcome to Plut."), reply_markup=main_kb())

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Standoff 2", callback_data="so2_menu")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 Выберите игру:"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Non Root", callback_data="nonroot_menu")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="📱 Выберите тип установки:"), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_menu")
async def nonroot_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Plutonium - 7 days", callback_data="pay_7")],
        [InlineKeyboardButton(text="Plutonium - 30 days", callback_data="pay_30")],
        [InlineKeyboardButton(text="Plutonium - 90 days", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="💎 Выберите тариф:"), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def pay_menu(call: types.CallbackQuery, state: FSMContext):
    data = {"pay_7": ("Plutonium - 7 days", "150"), "pay_30": ("Plutonium - 30 days", "300"), "pay_90": ("Plutonium - 90 days", "700")}
    item, price = data[call.data]
    await state.update_data(item=item, price=price)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇺🇦 Оплата на карту", callback_data="do_pay")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="nonroot_menu")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"Выбрано: {item}\nЦена: {price} грн.\nВыберите способ оплаты:"), reply_markup=kb)

@dp.callback_query(F.data == "do_pay")
async def do_pay(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = f"💳 Реквизиты: <code>{CARD}</code>\nСумма: {data['price']} грн\n❗️Комментарий: За цифрові товари\n\nСкиньте фото чека:"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=text, parse_mode="HTML"), reply_markup=kb)
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def get_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"adm_ok_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>Новый заказ!</b>\n{data['item']}\nЦена: {data['price']} грн\nЮзер: @{message.from_user.username}", reply_markup=kb, parse_mode="HTML")
    await message.answer("✅ Чек отправлен админу!")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(call: types.CallbackQuery):
    action, user_id = call.data.split("_")[1], call.data.split("_")[2]
    status = "подтвержден" if action == "ok" else "отклонен"
    await bot.send_message(user_id, f"Ваш заказ {status}!")
    await call.message.edit_caption(caption=call.message.caption + f"\n\nСтатус: {status.upper()}")

@dp.message(Command("send_all"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/send_all ", "")
    cursor.execute('SELECT user_id FROM users')
    for row in cursor.fetchall():
        try: await bot.send_message(row[0], text)
        except: continue
    await message.answer("✅ Рассылка завершена.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
