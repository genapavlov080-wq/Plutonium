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

# --- БАЗА ДАННЫХ: Полная структура ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry_date TEXT, product_name TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
conn.commit()

# --- СОСТОЯНИЯ (FSM) ---
class OrderState(StatesGroup):
    waiting_for_receipt = State()      # Ждем фото от юзера
    waiting_for_admin_file = State()   # Админ вводит файл
    waiting_for_admin_key = State()    # Админ вводит ключ
    waiting_for_broadcast = State()    # Админ вводит текст рассылки

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_cheat_status():
    cursor.execute('SELECT value FROM settings WHERE key = "cheat_status"')
    return cursor.fetchone()[0]

def get_time_left(expiry_str):
    if not expiry_str: return "Отсутствует"
    try:
        expiry_dt = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
        diff = expiry_dt - datetime.now()
        if diff.total_seconds() <= 0: return "Истекла"
        return f"{diff.days} дн. {diff.seconds // 3600} ч."
    except: return "—"

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
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (event.from_user.id,))
    conn.commit()
    cap = (f"<b>Plutonium Store — Официальный дистрибьютор.</b>\n"
           f"Статус ПО: {get_cheat_status()}\n\n"
           f"Мы предоставляем самые качественные и безопасные модификации для Standoff 2. "
           f"Выберите раздел для начала работы.")
    if isinstance(event, types.CallbackQuery): await event.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=cap), reply_markup=main_kb())
    else: await event.answer_photo(photo="https://files.catbox.moe/916cwt.png", caption=cap, reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (call.from_user.id,))
    res = cursor.fetchone()
    text = (f"👤 <b>Ваш профиль</b>\n\n"
            f"🆔 ID: <code>{call.from_user.id}</code>\n"
            f"📦 Продукт: <b>{res[1] if res and res[1] else '—'}</b>\n"
            f"⏳ Подписка до: {res[0] if res and res[0] else 'Нет активной подписки'}\n\n"
            f"Статус аккаунта: {'Администратор' if call.from_user.id == ADMIN_ID else 'Пользователь'}")
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=text), reply_markup=main_kb())

@dp.callback_query(F.data == "show_reviews")
async def show_reviews(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⭐️ Перейти в канал с отзывами", url="https://t.me/plutoniumrewiews")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐ <b>Отзывы о Plutonium</b>\n\nЗдесь собраны тысячи отзывов от наших довольных клиентов. Мы ценим качество и доверие, поэтому каждый отзыв реален."), reply_markup=kb)

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔫 Standoff 2", callback_data="so2_menu")], [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выбор дисциплины:</b>\nОфициальная поддержка игры Standoff 2. Выберите игру для получения списка доступных модификаций."), reply_markup=kb)

@dp.callback_query(F.data == "plut_desc")
async def plut_desc(call: types.CallbackQuery):
    desc = ("🔴 <b>Масштабное обновление Plutonium модификации!</b>\n\n"
            "<blockquote>🖥 <b>Журнал обновлений:</b>\n"
            "• Функция краша/выкидывания игроков\n"
            "• Функция предотвращения краша/выкидывания игроков, чтобы другие чит-инструменты не приводили к крашу\n"
            "• Мгновенная победа(с хостом)\n"
            "• Автоматическая победа (без хоста)\n"
            "• Улучшение скин-редактора\n"
            "• Скрытие на записи экрана\n"
            "• Улучшение визуальных эффектов меню\n"
            "• Исправлена и улучшена функция невидимости</blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дн - 150 грн", callback_data="pay_7"), InlineKeyboardButton(text="30 дн - 300 грн", callback_data="pay_30")],
        [InlineKeyboardButton(text="90 дн - 700 грн", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=kb)

# --- ЛОГИКА ОПЛАТЫ И АДМИНКИ ---
@dp.callback_query(F.data.startswith("pay_"))
async def pre_pay(call: types.CallbackQuery, state: FSMContext):
    days = call.data.split("_")[1]
    await state.update_data(days=int(days))
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💳 <b>Реквизиты карты:</b> <code>{CARD}</code>\n❗ <b>КОММЕНТАРИЙ:</b> <code>За цифрові товари</code>\n\nПришлите скриншот чека после оплаты."), 
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Я оплатил", callback_data="send_receipt")]]))

@dp.callback_query(F.data == "send_receipt")
async def ask_photo(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 <b>Отправьте скриншот чека в чат:</b>")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Отправляем админу полный чек с кнопками действия
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"🔔 <b>Чек от пользователя @{message.from_user.username}</b> (ID: <code>{message.from_user.id}</code>)\nТариф: {data['days']} дней", 
                         reply_markup=adm_kb)
    await message.answer("✅ <b>Чек отправлен админу!</b> Ожидайте подтверждения.")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_"))
async def admin_control(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    action, user_id = parts[1], parts[2]
    if action == "ok":
        await state.update_data(target_id=user_id, days=parts[3])
        await call.message.answer("Введите ФАЙЛ (или ссылку) для выдачи:")
        await state.set_state(OrderState.waiting_for_admin_file)
    else:
        await bot.send_message(user_id, "❌ <b>Ваш чек был отклонен.</b> Пожалуйста, обратитесь в поддержку за разъяснениями.")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 <b>ОТКЛОНЕНО</b>")

@dp.message(OrderState.waiting_for_admin_file)
async def get_admin_file(message: types.Message, state: FSMContext):
    await state.update_data(file=message.document.file_id if message.document else message.text, is_doc=bool(message.document))
    await message.answer("Введите КЛЮЧ для выдачи:")
    await state.set_state(OrderState.waiting_for_admin_key)

@dp.message(OrderState.waiting_for_admin_key)
async def final_delivery(message: types.Message, state: FSMContext):
    data = await state.get_data()
    expiry = (datetime.now() + timedelta(days=int(data['days']))).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', (expiry, "Plutonium", data['target_id']))
    conn.commit()
    
    if data.get('is_doc'): await bot.send_document(data['target_id'], data['file'])
    else: await bot.send_message(data['target_id'], f"📂 Ссылка: {data['file']}")
    await bot.send_message(data['target_id'], f"💎 <b>Ваш ключ активирован!</b>\n\nКлюч: <code>{message.text}</code>")
    await message.answer("✅ Успешно выдано.")
    await state.clear()

# --- РАССЫЛКА ---
@dp.message(Command("send_all"))
async def broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Введите текст для рассылки:")
    await state.set_state(OrderState.waiting_for_broadcast)

@dp.message(OrderState.waiting_for_broadcast)
async def broadcast_exec(message: types.Message, state: FSMContext):
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    count = 0
    for row in users:
        try:
            await message.copy_to(row[0])
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await message.answer(f"✅ Рассылка завершена. Успешно отправлено: {count} пользователям.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
