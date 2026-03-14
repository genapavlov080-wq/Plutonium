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

# --- БАЗА ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry_date TEXT, product_name TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
conn.commit()

class OrderState(StatesGroup):
    waiting_for_receipt = State()
    waiting_for_admin_file = State()
    waiting_for_admin_key = State()
    broadcast_text = State()

# --- КЛАВИАТУРЫ (2 кнопки в ряд + 1 внизу) ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key"), InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💬 Наши отзывы", callback_data="show_reviews"), InlineKeyboardButton(text="📊 Статус ПО", callback_data="check_status")],
        [InlineKeyboardButton(text="🆘 Техническая поддержка (Гарант)", url="https://t.me/IllyaGarant")]
    ])

def buy_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔫 Standoff 2", callback_data="so2_menu")],
        [InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="start")]
    ])

def plut_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней - 150 грн", callback_data="pay_7"), InlineKeyboardButton(text="30 дней - 300 грн", callback_data="pay_30")],
        [InlineKeyboardButton(text="90 дней - 700 грн", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад к выбору", callback_data="buy_key")]
    ])

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    cap = (f"<b>🔥 Plutonium Store — Качество превыше всего!</b>\n\n"
           f"📈 <b>Текущий статус ПО:</b> {status}\n\n"
           f"Добро пожаловать в элитный магазин модификаций для Standoff 2. "
           f"Мы обеспечиваем максимальную скрытность, постоянные обновления и 24/7 поддержку. "
           f"Выбирай лучший софт для доминирования в игре.")
    
    if isinstance(event, types.CallbackQuery): await event.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=cap), reply_markup=main_kb())
    else: await event.answer_photo(photo="https://files.catbox.moe/916cwt.png", caption=cap, reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def profile_handler(call: types.CallbackQuery):
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (call.from_user.id,))
    res = cursor.fetchone()
    cap = (f"👤 <b>Личный кабинет пользователя</b>\n\n"
           f"🆔 <b>Ваш ID:</b> <code>{call.from_user.id}</code>\n"
           f"📦 <b>Купленный товар:</b> {res[1] if res and res[1] else 'Отсутствует'}\n"
           f"⏳ <b>Действие подписки:</b> {res[0] if res and res[0] else 'Нет активной подписки'}")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=cap), reply_markup=main_kb())

@dp.callback_query(F.data == "buy_key")
async def buy_handler(call: types.CallbackQuery):
    cap = ("🎮 <b>Выбор дисциплины</b>\n\n"
           "Plutonium поддерживает современные версии Standoff 2. "
           "Выберите игру из списка ниже, чтобы ознакомиться с функционалом и тарифами.")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption=cap), reply_markup=buy_kb())

@dp.callback_query(F.data == "so2_menu")
async def so2_handler(call: types.CallbackQuery):
    desc = ("🔴 <b>Обновление Plutonium (Non Root)</b>\n\n"
            "<blockquote>🖥 <b>Функционал:</b>\n"
            "• Анти-краш и обход защиты\n"
            "• Мгновенная победа (с хостом/без)\n"
            "• Скин-редактор и визуальные эффекты\n"
            "• Полная невидимость на записи</blockquote>\n\n"
            "Выберите срок аренды ключа для активации:")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=plut_kb())

@dp.callback_query(F.data.startswith("pay_"))
async def pay_handler(call: types.CallbackQuery, state: FSMContext):
    days = call.data.split("_")[1]
    price = {"7": "150", "30": "300", "90": "700"}[days]
    await state.update_data(days=days, price=price)
    cap = (f"💳 <b>Реквизиты для оплаты</b>\n\n"
           f"💰 <b>Цена:</b> {price} грн\n"
           f"💳 <b>Карта:</b> <code>{CARD}</code>\n"
           f"❗️ <b>КОММЕНТАРИЙ ПРИ ПЕРЕВОДЕ:</b> <code>За цифрові товари</code>\n\n"
           f"Нажмите кнопку ниже, когда перевод будет выполнен, чтобы прикрепить фото чека.")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="send_receipt"), InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=cap), reply_markup=kb)

# --- ЛОГИКА ЧЕКОВ (УСИЛЕННАЯ) ---
@dp.callback_query(F.data == "send_receipt")
async def start_receipt(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 <b>Отправьте скриншот чека в этот чат одним сообщением.</b>\nАдминистратор получит его мгновенно.")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>НОВЫЙ ЧЕК</b>\nОт: @{message.from_user.username} (ID: {message.from_user.id})\nТариф: {data['days']} дней", reply_markup=adm_kb)
    await message.answer("✅ <b>Чек успешно отправлен администратору!</b>\nОжидайте выдачи файла и ключа в этом диалоге.")
    await state.clear()

# --- АДМИНКА (ВЫДАЧА) ---
@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    if parts[1] == "ok":
        await state.update_data(target_id=parts[2], days=parts[3])
        await call.message.answer("Введите ФАЙЛ (или ссылку):")
        await state.set_state(OrderState.waiting_for_admin_file)
    else:
        await bot.send_message(parts[2], "❌ Ваша оплата была отклонена администратором.")
        await call.message.delete()

@dp.message(OrderState.waiting_for_admin_file)
async def admin_get_file(message: types.Message, state: FSMContext):
    await state.update_data(file=message.document.file_id if message.document else message.text)
    await message.answer("Введите КЛЮЧ:")
    await state.set_state(OrderState.waiting_for_admin_key)

@dp.message(OrderState.waiting_for_admin_key)
async def admin_get_key(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expiry = (datetime.now() + timedelta(days=int(data['days']))).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('UPDATE users SET expiry_date = ?, product_name = "Plutonium" WHERE user_id = ?', (expiry, data['target_id']))
    conn.commit()
    await bot.send_message(data['target_id'], f"📂 <b>Файл:</b> {data['file']}\n💎 <b>КЛЮЧ:</b> <code>{message.text}</code>")
    await message.answer("✅ Ключ успешно выдан.")
    await state.clear()

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
                         
