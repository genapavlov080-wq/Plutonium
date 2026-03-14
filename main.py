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

# --- ПОЛНАЯ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry_date TEXT, product_name TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
conn.commit()

# --- ВСЕ СОСТОЯНИЯ ---
class OrderState(StatesGroup):
    waiting_for_receipt = State()
    waiting_for_admin_file = State()
    waiting_for_admin_key = State()
    broadcast_text = State()

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key"), InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💬 Наши отзывы", callback_data="show_reviews"), InlineKeyboardButton(text="📊 Статус ПО", callback_data="check_status")],
        [InlineKeyboardButton(text="🆘 Техническая поддержка (Гарант)", url="https://t.me/IllyaGarant")]
    ])
    return kb

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (int(message.from_user.id),))
    conn.commit()
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    caption = f"🔥 <b>Plutonium Store — Официальный дистрибьютор</b>\n\n📈 Статус ПО: {status}\n\nДобро пожаловать в наш магазин модификаций."
    await message.answer_photo(photo="https://files.catbox.moe/916cwt.png", caption=caption, reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "start")
async def start_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    caption = f"🔥 <b>Plutonium Store — Официальный дистрибьютор</b>\n\n📈 Статус ПО: {status}\n\nДобро пожаловать в наш магазин."
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=caption), reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "profile")
async def profile_callback(call: types.CallbackQuery):
    await call.answer()
    user_id = int(call.from_user.id)
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    
    time_left = "Нет активной подписки"
    if res and res[0]:
        try:
            expiry_date = datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S')
            diff = expiry_date - datetime.now()
            if diff.total_seconds() > 0:
                time_left = f"{diff.days} дн. {diff.seconds // 3600} ч. {(diff.seconds % 3600) // 60} мин."
            else:
                time_left = "Истекла"
        except Exception as e:
            time_left = "Ошибка вычисления"
    
    cap = f"👤 <b>Личный кабинет пользователя</b>\n\n🆔 ID: <code>{user_id}</code>\n📦 Товар: {res[1] if res and res[1] else 'Нет'}\n⏳ Осталось времени: <b>{time_left}</b>"
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=cap), 
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]]))

@dp.callback_query(F.data == "show_reviews")
async def reviews_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Канал с отзывами", url="https://t.me/plutoniumrewiews")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐ <b>Наши отзывы:</b> Подтверждение качества."), reply_markup=kb)

@dp.callback_query(F.data == "buy_key")
async def buy_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔫 Standoff 2", callback_data="so2_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выбор дисциплины:</b> Выберите нужную игру."), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_callback(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Plutonium Non Root", callback_data="plut_info")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="⚙️ <b>Выберите версию установки:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "plut_info")
async def plut_info_callback(call: types.CallbackQuery):
    await call.answer()
    desc = ("🔴 <b>Масштабное обновление Plutonium модификации!</b>\n\n"
            "<blockquote>🖥 <b>Журнал обновлений:</b>\n"
            "[+] Функция краша игроков\n"
            "[+] Функция анти-краша\n"
            "[+] Мгновенная победа\n"
            "[+] Автоматическая победа\n"
            "[+] Улучшение скин-редактора\n"
            "[+] Скрытие на записи\n"
            "[+] Улучшение визуала\n"
            "[+] Исправлена невидимость</blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дн - 150 грн", callback_data="pay_7"), InlineKeyboardButton(text="30 дн - 300 грн", callback_data="pay_30")],
        [InlineKeyboardButton(text="90 дн - 700 грн", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def pay_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    days = call.data.split("_")[1]
    await state.update_data(days=days)
    cap = f"💳 <b>Карта:</b> <code>{CARD}</code>\n❗ <b>Комментарий:</b> За цифрові товари\n\nПришлите чек одним сообщением."
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="send_receipt"), InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=cap), reply_markup=kb)

@dp.callback_query(F.data == "send_receipt")
async def receipt_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("📸 <b>Отправьте скриншот чека одним сообщением:</b>")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 <b>Чек от пользователя:</b> {message.from_user.id}\nТариф: {data['days']} дней", reply_markup=adm_kb)
    await message.answer("✅ Чек успешно отправлен!")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    if parts[1] == "ok":
        await state.update_data(target_id=int(parts[2]), days=parts[3])
        await call.message.answer("Введите ФАЙЛ:")
        await state.set_state(OrderState.waiting_for_admin_file)
    else:
        await bot.send_message(int(parts[2]), "❌ Ваша оплата была отклонена.")
        await call.message.delete()

@dp.message(OrderState.waiting_for_admin_file)
async def admin_file_input(message: types.Message, state: FSMContext):
    await state.update_data(file=message.document.file_id if message.document else message.text)
    await message.answer("Введите КЛЮЧ:")
    await state.set_state(OrderState.waiting_for_admin_key)

@dp.message(OrderState.waiting_for_admin_key)
async def admin_key_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expiry = (datetime.now() + timedelta(days=int(data['days']))).strftime('%Y-%m-%d %H:%M:%S')
    target_id = int(data['target_id'])
    
    cursor.execute('INSERT OR REPLACE INTO users (user_id, expiry_date, product_name) VALUES (?, ?, ?)', (target_id, expiry, "Plutonium"))
    conn.commit()
    
    success_text = (f"💎 <b>Ваш заказ успешно активирован!</b>\n\n"
                    f"📂 <b>Ваш файл:</b> {data['file']}\n"
                    f"🔑 <b>Ваш ключ:</b> <code>{message.text}</code>\n\n"
                    f"Благодарим за покупку в Plutonium Store!")
    
    await bot.send_message(target_id, success_text)
    await message.answer("✅ Успешно выдано пользователю.")
    await state.clear()

@dp.message(Command("set_status"))
async def set_status(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute('UPDATE settings SET value = ? WHERE key = "cheat_status"', (message.text.replace("/set_status ", ""),))
    conn.commit()
    await message.answer("✅ Статус обновлен.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
