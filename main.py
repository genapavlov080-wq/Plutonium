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

# Таблица пользователей с подписками
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiry_date TEXT,
        product_name TEXT,
        subscribed_at TEXT
    )
''')

# Таблица настроек
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("total_users", "0")')
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
    user_id = int(message.from_user.id)
    
    # Добавляем пользователя если его нет
    cursor.execute('INSERT OR IGNORE INTO users (user_id, subscribed_at) VALUES (?, ?)', 
                  (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
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

@dp.callback_query(F.data == "check_status")
async def check_status(call: types.CallbackQuery):
    await call.answer()
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/916cwt.png", caption=f"📊 <b>Текущий статус ПО:</b> {status}"), reply_markup=kb)

@dp.callback_query(F.data == "profile")
async def profile_callback(call: types.CallbackQuery):
    await call.answer()
    user_id = int(call.from_user.id)
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    
    time_left = "Нет активной подписки"
    product = "Нет"
    
    if res and res[0]:
        try:
            expiry_date = datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S')
            diff = expiry_date - datetime.now()
            if diff.total_seconds() > 0:
                days = diff.days
                hours = diff.seconds // 3600
                minutes = (diff.seconds % 3600) // 60
                time_left = f"{days} дн. {hours} ч. {minutes} мин."
                product = res[1] if res[1] else "Plutonium"
            else:
                time_left = "Истекла"
                # Можно автоматически очистить истекшую подписку
                cursor.execute('UPDATE users SET expiry_date = NULL, product_name = NULL WHERE user_id = ?', (user_id,))
                conn.commit()
        except Exception as e:
            time_left = "Ошибка формата"
    
    cap = f"👤 <b>Личный кабинет пользователя</b>\n\n🆔 ID: <code>{user_id}</code>\n📦 Товар: {product}\n⏳ Осталось времени: <b>{time_left}</b>"
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
    await message.answer("✅ Чек успешно отправлен администратору! Ожидайте подтверждения.")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔️ Доступ запрещен")
        return
    
    parts = call.data.split("_")
    if parts[1] == "ok":
        await state.update_data(target_id=int(parts[2]), days=parts[3])
        await call.message.answer("📎 <b>Отправьте файл для пользователя:</b>")
        await state.set_state(OrderState.waiting_for_admin_file)
        await call.answer("✅ Одобрено")
    else:
        await bot.send_message(int(parts[2]), "❌ Ваша оплата была отклонена администратором.")
        await call.message.delete()
        await call.answer("❌ Отклонено")

@dp.message(OrderState.waiting_for_admin_file)
async def admin_file_input(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    file_id = None
    file_text = None
    
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_text = message.text
    
    await state.update_data(file=file_id, file_text=file_text)
    await message.answer("🔑 <b>Введите ключ для пользователя:</b>")
    await state.set_state(OrderState.waiting_for_admin_key)

@dp.message(OrderState.waiting_for_admin_key)
async def admin_key_input(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    data = await state.get_data()
    target_id = int(data['target_id'])
    days = int(data['days'])
    
    # Вычисляем дату окончания подписки
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Сохраняем подписку в базу данных
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, expiry_date, product_name, subscribed_at) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?))
    ''', (target_id, expiry_date, "Plutonium", target_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    # Формируем сообщение пользователю
    success_text = f"💎 <b>Ваш заказ успешно активирован!</b>\n\n📅 <b>Подписка действует до:</b> {expiry_date}\n\n"
    
    if data.get('file'):
        if data['file_text']:
            await bot.send_message(target_id, success_text + f"📝 <b>Инструкция:</b>\n{data['file_text']}")
            await bot.send_message(target_id, f"🔑 <b>Ваш ключ:</b> <code>{message.text}</code>")
        else:
            await bot.send_document(target_id, data['file'], caption=success_text)
            await bot.send_message(target_id, f"🔑 <b>Ваш ключ:</b> <code>{message.text}</code>")
    else:
        await bot.send_message(target_id, success_text + f"🔑 <b>Ваш ключ:</b> <code>{message.text}</code>")
    
    await message.answer("✅ Готово! Подписка активирована и сохранена в базе.")
    await state.clear()

@dp.message(Command("set_status"))
async def set_status(message: types.Message):
    if message.from_user.id != ADMIN_ID: 
        await message.answer("⛔️ Доступ запрещен")
        return
    
    new_status = message.text.replace("/set_status ", "").strip()
    cursor.execute('UPDATE settings SET value = ? WHERE key = "cheat_status"', (new_status,))
    conn.commit()
    await message.answer(f"✅ Статус обновлен на: {new_status}")

@dp.message(Command("broadcast"))
async def broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Доступ запрещен")
        return
    
    await message.answer("📢 <b>Отправь сообщение для рассылки всем пользователям</b>\n(текст, фото, видео или документ)")
    await state.set_state(OrderState.broadcast_text)

@dp.message(OrderState.broadcast_text)
async def broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    
    if not users:
        await message.answer("📭 Нет пользователей в базе")
        await state.clear()
        return
    
    success = 0
    fail = 0
    
    status_msg = await message.answer(f"⏳ Начинаю рассылку {len(users)} пользователям...")
    
    for (user_id,) in users:
        try:
            if message.text:
                await bot.send_message(user_id, message.text)
            elif message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await bot.send_video(user_id, message.video.file_id, caption=message.caption)
            elif message.document:
                await bot.send_document(user_id, message.document.file_id, caption=message.caption)
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            fail += 1
    
    await status_msg.edit_text(f"✅ Рассылка завершена!\n✅ Успешно: {success}\n❌ Ошибок: {fail}")
    await state.clear()

@dp.message(Command("users"))
async def users_count(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cursor.execute('SELECT COUNT(*) FROM users')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date IS NOT NULL AND expiry_date > ?', 
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
    active = cursor.fetchone()[0]
    
    await message.answer(f"👥 Всего пользователей: {total}\n✅ С активной подпиской: {active}")

@dp.message(Command("status"))
async def get_status(message: types.Message):
    cursor.execute('SELECT value FROM settings WHERE key="cheat_status"')
    status = cursor.fetchone()[0]
    await message.answer(f"📊 Текущий статус: {status}")

@dp.message(Command("check_subs"))
async def check_subs(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cursor.execute('SELECT user_id, expiry_date, product_name FROM users WHERE expiry_date IS NOT NULL')
    subs = cursor.fetchall()
    
    if not subs:
        await message.answer("📭 Нет активных подписок")
        return
    
    text = "📋 <b>Активные подписки:</b>\n\n"
    for uid, exp, prod in subs[:10]:  # показываем только первые 10
        text += f"👤 ID: <code>{uid}</code>\n📦 {prod}\n📅 до: {exp}\n\n"
    
    await message.answer(text)

async def main():
    print("🚀 Бот запущен!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("✅ Подписки сохраняются в базе данных")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
