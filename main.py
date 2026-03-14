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
    waiting_for_admin_file = State()
    waiting_for_admin_key = State()
    waiting_for_broadcast = State()

def get_cheat_status():
    cursor.execute('SELECT value FROM settings WHERE key = "cheat_status"')
    res = cursor.fetchone()
    return res[0] if res else "Неизвестно"

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key"), InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💬 Отзывы", callback_data="show_reviews"), InlineKeyboardButton(text="📊 Статус ПО", callback_data="check_status")],
        [InlineKeyboardButton(text="🆘 Официальная поддержка", url="https://t.me/IllyaGarant")]
    ])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    cap = f"<b>Plutonium Store — Официальный дистрибьютор.</b>\nСтатус ПО: {get_cheat_status()}\n\nДобро пожаловать в официальный магазин."
    if isinstance(event, types.CallbackQuery): await event.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=cap), reply_markup=main_kb())
    else: await event.answer_photo(photo="https://files.catbox.moe/916cwt.png", caption=cap, reply_markup=main_kb())

@dp.callback_query(F.data == "check_status")
async def check_status_handler(call: types.CallbackQuery):
    await call.answer(f"Текущий статус: {get_cheat_status()}", show_alert=True)

@dp.callback_query(F.data == "buy_key")
async def buy_key_handler(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔫 Standoff 2", callback_data="so2_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выберите игру для покупки:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu_handler(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Non Root Версия", callback_data="plut_desc")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="⚙️ <b>Тип установки для Standoff 2:</b>\nВыберите подходящий вариант."), reply_markup=kb)

@dp.callback_query(F.data == "plut_desc")
async def plut_desc_handler(call: types.CallbackQuery):
    desc = ("🔴 <b>Масштабное обновление Plutonium модификации!</b>\n\n"
            "<blockquote>🖥 <b>Журнал обновлений:</b>\n"
            "• Функция краша/выкидывания игроков\n"
            "• Функция предотвращения краша\n"
            "• Мгновенная победа(с хостом)\n"
            "• Автоматическая победа (без хоста)\n"
            "• Улучшение скин-редактора\n"
            "• Скрытие на записи экрана\n"
            "• Улучшение визуальных эффектов меню\n"
            "• Исправлена и улучшена функция невидимости</blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дн - 150 грн", callback_data="pay_7"), InlineKeyboardButton(text="30 дн - 300 грн", callback_data="pay_30")],
        [InlineKeyboardButton(text="90 дн - 700 грн", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=kb)

# --- ПРОФИЛЬ, ОТЗЫВЫ, ОПЛАТА, АДМИНКА (без изменений в логике) ---
@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (call.from_user.id,))
    res = cursor.fetchone()
    text = (f"👤 <b>Ваш профиль</b>\n\n📦 Продукт: <b>{res[1] if res and res[1] else '—'}</b>\n"
            f"⏳ Подписка до: {res[0] if res and res[0] else 'Нет активной подписки'}")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=text), reply_markup=main_kb())

@dp.callback_query(F.data == "show_reviews")
async def show_reviews(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Канал с отзывами", url="https://t.me/plutoniumrewiews")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐ <b>Наши отзывы</b>\nБолее тысячи довольных клиентов."), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def pay_handler(call: types.CallbackQuery, state: FSMContext):
    days = call.data.split("_")[1]
    await state.update_data(days=int(days))
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💳 <b>Карта:</b> <code>{CARD}</code>\n❗ <b>Комментарий:</b> За цифрові товари"), 
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Я оплатил", callback_data="send_receipt")]]))

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")], [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>Чек от @{message.from_user.username}</b> (ID: {message.from_user.id})", reply_markup=adm_kb)
    await message.answer("✅ Чек отправлен админу!")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_"))
async def admin_process(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    action, user_id = parts[1], parts[2]
    if action == "ok":
        await state.update_data(target_id=user_id, days=parts[3])
        await call.message.answer("Введите ФАЙЛ:")
        await state.set_state(OrderState.waiting_for_admin_file)
    else:
        await bot.send_message(user_id, "❌ Ваш чек был отклонен.")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 <b>ОТКЛОНЕНО</b>")

@dp.message(OrderState.waiting_for_admin_file)
async def admin_file(message: types.Message, state: FSMContext):
    await state.update_data(file=message.document.file_id if message.document else message.text)
    await message.answer("Введите КЛЮЧ:")
    await state.set_state(OrderState.waiting_for_admin_key)

@dp.message(OrderState.waiting_for_admin_key)
async def admin_key(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(data['target_id'], f"📂 Файл: {data['file']}\n💎 Ключ: <code>{message.text}</code>")
    await message.answer("✅ Успешно выдано.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
