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

# --- БАЗА ДАННЫХ ---
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
@dp.callback_query(F.data == "pay_method")
async def pay_method(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 Оплата на карту (УкрБанк)", callback_data="pay_bank")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nonroot_menu")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="Выберите способ оплаты:"), reply_markup=kb)

@dp.callback_query(F.data == "pay_bank")
async def pay_bank(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = (f"💳 <b>Оплата на карту:</b>\n<code>{CARD}</code>\n"
            f"Сумма: {data['price']} грн\n❗️Комментарий: За цифрові товари\n\n"
            "После оплаты отправьте фото чека:")
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
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"🔔 <b>Новый заказ!</b>\n{data['item']}\nЦена: {data['price']} грн\nЮзер: @{message.from_user.username}", 
                         reply_markup=kb, parse_mode="HTML")
    await message.answer("✅ Чек отправлен админу!")
    await state.clear()

# --- АДМИНКА (Подтверждение) ---
@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(call: types.CallbackQuery):
    action, user_id = call.data.split("_")[1], call.data.split("_")[2]
    if action == "ok":
        await bot.send_message(user_id, "✅ Ваш заказ подтвержден! Админ сейчас напишет вам.")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🟢 Оплачено")
    else:
        await bot.send_message(user_id, "❌ Ваш платеж отклонен. Свяжитесь с поддержкой.")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 Отклонено")

# --- РАССЫЛКА (Исправленная) ---
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
    
