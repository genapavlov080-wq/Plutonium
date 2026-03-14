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

# --- КОНФИГУРАЦИЯ ---
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
    waiting_for_broadcast = State()
    waiting_for_key_delivery = State()

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
        return f"<b>{diff.days}</b> дн. <b>{diff.seconds // 3600}</b> час."
    except: return "—"

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), 
         InlineKeyboardButton(text="💬 Отзывы", callback_data="show_reviews")],
        [InlineKeyboardButton(text="📊 Статус чита", callback_data="check_status")],
        [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/IllyaGarant")]
    ])

# --- ОСНОВНЫЕ ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    
    photo = "https://files.catbox.moe/916cwt.png"
    cap = "<b>Welcome to Plutonium Store.</b>\n\nВыберите нужный раздел в меню ниже 👇"
    
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_media(media=InputMediaPhoto(media=photo, caption=cap), reply_markup=main_kb())
    else:
        await event.answer_photo(photo=photo, caption=cap, reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    cursor.execute('SELECT expiry_date, product_name FROM users WHERE user_id = ?', (call.from_user.id,))
    res = cursor.fetchone()
    status = "Админ" if call.from_user.id == ADMIN_ID else ("Покупатель" if res and res[0] else "Пользователь")
    
    text = (f"👤 <b>Ваш профиль</b>\n\n🆔 ID: <code>{call.from_user.id}</code>\n"
            f"👑 Статус: <b>{status}</b>\n📦 Продукт: <b>{res[1] if res and res[1] else '—'}</b>\n"
            f"⏳ Подписка: {get_time_left(res[0]) if res and res[0] else '—'}")
    
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=text), reply_markup=main_kb())

# --- ЛОГИКА ПОКУПКИ ---

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔫 Standoff 2", callback_data="so2_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выберите дисциплину:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Non Root", callback_data="nonroot_info")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="⚙️ <b>Выберите тип установки:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_info")
async def nonroot_info(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Plutonium", callback_data="plut_desc")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="🔧 <b>Доступные модификации:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "plut_desc")
async def plut_desc(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Plutonium - 7 days", callback_data="pay_7")],
        [InlineKeyboardButton(text="Plutonium - 30 days", callback_data="pay_30")],
        [InlineKeyboardButton(text="Plutonium - 90 days", callback_data="pay_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nonroot_info")]
    ])
    
    desc = (
        "🔴 <b>Масштабное обновление Plutonium модификации!</b>\n\n"
        "<b>Самый мощный функционал на рынке уже доступен к покупке.</b>\n\n"
        "<blockquote>"
        "🖥 <b>Журнал обновлений:</b>\n"
        "• Функция краша/выкидывания игроков\n"
        "• Функция предотвращения краша\n"
        "• Мгновенная победа (с хостом)\n"
        "• Автоматическая победа (без хоста)\n"
        "• Улучшение скин-редактора\n"
        "• Скрытие на записи экрана\n"
        "• Улучшение визуальных эффектов меню\n"
        "• Исправлена и улучшена невидимость"
        "</blockquote>"
    )
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def pre_pay(call: types.CallbackQuery, state: FSMContext):
    days = call.data.split("_")[1]
    price = {"7": "150", "30": "300", "90": "700"}[days]
    item_name = f"Plutonium - {days} days"
    
    await state.update_data(item=item_name, price=price, days=int(days))
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 Оплата на карту (UkrBank)", callback_data="go_rekv")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="plut_desc")]
    ])
    
    cap = (
        f"💳 <b>Оформление подписки</b>\n\n"
        f"📦 <b>Товар:</b> <code>{item_name}</code>\n"
        f"💰 <b>Цена:</b> <code>{price} грн</code>\n\n"
        f"После оплаты вы получите ключ доступа и подробную инструкцию по установке."
    )
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=cap), reply_markup=kb)

@dp.callback_query(F.data == "go_rekv")
async def show_rekv(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="confirm_send")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
    ])
    cap = (
        f"⚠️ <b>Оплата по реквизитам</b>\n\n"
        f"Для активации <b>{data['item']}</b> переведите <b>{data['price']} грн</b> на карту:\n"
        f"💳 <code>{CARD}</code>\n\n"
        f"❗ <b>ОБЯЗАТЕЛЬНЫЙ КОММЕНТАРИЙ:</b>\n"
        f"<blockquote>За цифрові товари</blockquote>\n\n"
        f"После перевода нажмите кнопку ниже и пришлите чек."
    )
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=cap), reply_markup=kb)

@dp.callback_query(F.data == "confirm_send")
async def ask_photo(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 <b>Пожалуйста, отправьте скриншот чека в чат:</b>")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выдать ключ", callback_data=f"adm_ok_{message.from_user.id}_{data['days']}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    
    await bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"🔔 <b>Новый заказ!</b>\nТовар: {data['item']}\nЮзер: @{message.from_user.username}", 
        reply_markup=adm_kb
    )
    
    await message.answer("✅ <b>Чек принят!</b>\nАдминистратор проверяет платеж. Ожидайте выдачи ключа.")
    await state.clear()

# --- АДМИН-ФУНКЦИИ ---

@dp.callback_query(F.data.startswith("adm_"))
async def admin_action(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    action, user_id = parts[1], parts[2]
    
    if action == "ok":
        days = int(parts[3])
        await state.update_data(target_id=user_id, target_days=days)
        await call.message.answer(f"Введите ключ для пользователя {user_id}:")
        await state.set_state(OrderState.waiting_for_key_delivery)
    else:
        await bot.send_message(user_id, "❌ <b>Оплата отклонена.</b>")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 <b>ОТКЛОНЕНО</b>")

@dp.message(OrderState.waiting_for_key_delivery)
async def process_key_input(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    target_id = data['target_id']
    days = data['target_days']
    
    expiry = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', 
                   (expiry, f"Plutonium ({days} дн.)", target_id))
    conn.commit()
    
    await bot.send_message(target_id, f"💎 <b>Ваш ключ активирован!</b>\n\nКлюч: <code>{message.text}</code>\n\nПриятной игры!")
    await message.answer(f"✅ Ключ выдан пользователю {target_id}")
    await state.clear()

@dp.message(Command("setstatus"))
async def cmd_setstatus(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    new_status = message.text.replace("/setstatus ", "")
    cursor.execute('UPDATE settings SET value = ? WHERE key = "cheat_status"', (new_status,))
    conn.commit()
    await message.answer(f"✅ Статус обновлен на: {new_status}")

@dp.message(Command("send_all"))
async def cmd_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Перешлите пост для рассылки (с фото, текстом и кнопками):")
    await state.set_state(OrderState.waiting_for_broadcast)

@dp.message(OrderState.waiting_for_broadcast)
async def process_broadcast_msg(message: types.Message, state: FSMContext):
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    count = 0
    for row in users:
        try:
            await message.copy_to(row[0])
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await message.answer(f"✅ Рассылка завершена. Получили: {count}")
    await state.clear()

# --- ДОПОЛНИТЕЛЬНЫЕ КНОПКИ ---

@dp.callback_query(F.data == "check_status")
async def check_cheat_status(call: types.CallbackQuery):
    status = get_cheat_status()
    await call.answer(f"Статус ПО: {status}", show_alert=True)

@dp.callback_query(F.data == "show_reviews")
async def reviews_handler(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Канал с отзывами", url="https://t.me/plutoniumrewiews")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐️ <b>Отзывы клиентов:</b>"), reply_markup=kb)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
        
