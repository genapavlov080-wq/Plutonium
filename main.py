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

# Инициализация БД
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
conn.commit()

class OrderState(StatesGroup):
    waiting_for_receipt = State()

# --- ГЛАВНОЕ МЕНЮ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), 
         InlineKeyboardButton(text="💬 Отзывы", callback_data="reviews")],
        [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/IllyaGarant")]
    ])

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_handler(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (user_id,))
    conn.commit()
    
    caption = "<b>Welcome to Plut.</b>\n\nВыберите нужный раздел в меню ниже 👇"
    photo = "https://files.catbox.moe/5h6fr0.png"
    
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_media(media=InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"), reply_markup=main_kb())
    else:
        await event.answer_photo(photo=photo, caption=caption, reply_markup=main_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    text = f"👤 <b>Ваш профиль</b>\n\n🆔 ID: <code>{call.from_user.id}</code>\n🏷 Имя: {call.from_user.first_name}\nСтатус: Пользователь"
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/5h6fr0.png", caption=text, parse_mode="HTML"), reply_markup=main_kb())

@dp.callback_query(F.data == "reviews")
async def show_reviews(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Перейти в канал", url="https://t.me/plutoniumrewiews")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/3z96th.png", caption="⭐️ <b>Наши отзывы:</b>\n\nОзнакомьтесь с отзывами наших клиентов в официальном канале.", parse_mode="HTML"), reply_markup=kb)

@dp.callback_query(F.data == "buy_key")
async def buy_key(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Standoff 2", callback_data="so2_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/1u2tb9.png", caption="🎮 <b>Выберите дисциплину:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "so2_menu")
async def so2_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Non Root", callback_data="nonroot_info")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]
    ])
    # Новое фото для выбора Non Root
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/ljpeoi.png", caption="📱 <b>Выберите тип установки:</b>"), reply_markup=kb)

@dp.callback_query(F.data == "nonroot_info")
async def nonroot_info(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Plutonium", callback_data="plut_desc")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="so2_menu")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/w5b4rw.png", caption="🔧 <b>Non Root версия</b>\n\nМодификация работает полностью без рут прав на любом устройстве."), reply_markup=kb)

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
        "🖥 <b>Журнал обновлений:</b>\n"
        "[+] Функция краша игроков/выкидывания игроков\n"
        "[+] Функция предотвращения краша/выкидывания игроков\n"
        "[+] Мгновенная победа (с хостом)\n"
        "[+] Автоматическая победа (без хоста)\n"
        "[+] Улучшение скин-редактора\n"
        "[+] Скрытие на записи экрана\n"
        "[+] Улучшение визуальных эффектов меню\n"
        "[+] Исправлена и улучшена функция невидимости"
    )
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=desc, parse_mode="HTML"), reply_markup=kb)

@dp.callback_query(F.data.startswith("pay_"))
async def pay_method_choice(call: types.CallbackQuery, state: FSMContext):
    prices = {"pay_7": "150", "pay_30": "300", "pay_90": "700"}
    item_name = {"pay_7": "7 days", "pay_30": "30 days", "pay_90": "90 days"}[call.data]
    price = prices[call.data]
    await state.update_data(item=f"Plutonium - {item_name}", price=price)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 Оплата на карту (УкрБанк)", callback_data="do_pay_bank")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="plut_desc")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=f"💎 <b>Выбрано: Plutonium - {item_name}</b>\nЦена: {price} грн\n\nВыберите способ оплаты:"), reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "do_pay_bank")
async def do_pay_bank(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = (
        f"💳 <b>Реквизиты для оплаты (УкрБанк):</b>\n"
        f"Карта: <code>{CARD}</code>\n"
        f"Сумма: <b>{data['price']} грн</b>\n\n"
        f"❗️ <b>Комментарий обязательно:</b> За цифрові товари\n\n"
        "После перевода нажмите кнопку ниже и отправьте скриншот чека."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил (скинуть чек)", callback_data="confirm_payment")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
    ])
    await call.message.edit_media(media=InputMediaPhoto(media="https://files.catbox.moe/eqco0i.png", caption=text, parse_mode="HTML"), reply_markup=kb)

@dp.callback_query(F.data == "confirm_payment")
async def confirm_payment(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📸 Пожалуйста, отправьте скриншот чека в чат:")
    await state.set_state(OrderState.waiting_for_receipt)

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Кнопки для тебя (админа)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"adm_ok_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    
    await bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"🔔 <b>Новый заказ!</b>\nТовар: {data['item']}\nСумма: {data['price']} грн\nЮзер: @{message.from_user.username} (ID: {message.from_user.id})",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await message.answer("✅ Чек отправлен на проверку. Ожидайте подтверждения от администратора!")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(call: types.CallbackQuery):
    action, user_id = call.data.split("_")[1], call.data.split("_")[2]
    if action == "ok":
        await bot.send_message(user_id, "✅ <b>Ваша оплата подтверждена!</b>\nВы успешно приобрели Plutonium. Админ свяжется с вами в ближайшее время для выдачи ключа.", parse_mode="HTML")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🟢 <b>СТАТУС: ПОДТВЕРЖДЕНО</b>", parse_mode="HTML")
    else:
        await bot.send_message(user_id, "❌ <b>Оплата отклонена.</b>\nВаш чек не прошел проверку. Пожалуйста, свяжитесь с поддержкой.", parse_mode="HTML")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 <b>СТАТУС: ОТКЛОНЕНО</b>", parse_mode="HTML")

# --- РАССЫЛКА ---
@dp.message(Command("send_all"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    broadcast_text = message.text.replace("/send_all ", "")
    if not broadcast_text or broadcast_text == "/send_all":
        await message.answer("Введите текст после команды. Пример: <code>/send_all Всем привет!</code>", parse_mode="HTML")
        return

    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    
    count = 0
    for row in users:
        try:
            await bot.send_message(row[0], broadcast_text)
            count += 1
            await asyncio.sleep(0.05) # Защита от спам-фильтра
        except:
            continue
    
    await message.answer(f"📢 Рассылка завершена!\nСообщение получили <b>{count}</b> пользователей.", parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
