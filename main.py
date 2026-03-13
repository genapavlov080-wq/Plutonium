import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

# --- КОНФИГ ---
TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CHANNEL_ID = "@OfficialPlutonium"
DB_FILE = "users.txt"

# Ссылки на фото
IMG_MAIN = "https://files.catbox.moe/5h6fr0.png" 
IMG_REVIEWS = "https://files.catbox.moe/3z96th.png"
IMG_SO2 = "https://files.catbox.moe/1u2tb9.png"
IMG_NONROOT = "https://files.catbox.moe/w5b4rw.png"
IMG_PRODUCT = "https://files.catbox.moe/eqco0i.png"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ (ФАЙЛ) ---
def add_user(user_id):
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: pass
    with open(DB_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(DB_FILE, "a") as f:
            f.write(str(user_id) + "\n")

def get_all_users():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r") as f:
        return list(set(f.read().splitlines()))

# --- ПРОВЕРКА ПОДПИСКИ ---
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status != 'left'
    except: return False

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="buy_key")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), 
         InlineKeyboardButton(text="💬 Отзывы", callback_data="reviews")],
        [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/IllyaGarant")]
    ])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    if not await is_subscribed(message.from_user.id):
        await message.answer(f"❌ Для работы подпишись на канал: {CHANNEL_ID}")
        return
    await message.answer_photo(photo=IMG_MAIN, caption="<b>Welcome to Plut.</b>\nВыберите раздел:", 
                               reply_markup=main_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "start")
async def back_to_start(call: types.CallbackQuery):
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_MAIN, caption="<b>Welcome to Plut.</b>"), reply_markup=main_kb())

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    text = f"👤 <b>ID:</b> <code>{call.from_user.id}</code>\nСтатус: Активен"
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_MAIN, caption=text, parse_mode="HTML"), reply_markup=main_kb())

@dp.callback_query(F.data == "reviews")
async def show_reviews(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Канал с отзывами", url="https://t.me/plutoniumrewiews")],
                                               [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_REVIEWS, caption="⭐️ Отзывы наших клиентов:"), reply_markup=kb)

@dp.callback_query(F.data == "buy_key")
async def shop_so2(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Standoff 2", callback_data="type_nonroot")],
                                               [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]])
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_SO2, caption="🎮 Выберите игру:"), reply_markup=kb)

@dp.callback_query(F.data == "type_nonroot")
async def shop_nonroot(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Plutonium (150 грн)", callback_data="prod_plut")],
                                               [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_key")]])
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_NONROOT, caption="📱 Выберите версию:"), reply_markup=kb)

@dp.callback_query(F.data == "prod_plut")
async def show_product(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Купить", url="https://t.me/IllyaGarant")],
                                               [InlineKeyboardButton(text="⬅️ Назад", callback_data="type_nonroot")]])
    await call.message.edit_media(media=InputMediaPhoto(media=IMG_PRODUCT, caption="💎 <b>Plutonium</b>\nПолный обход бана, без рут прав.\nНапишите в поддержку для оплаты."), reply_markup=kb, parse_mode="HTML")

# --- РАССЫЛКА ---
@dp.message(Command("send_all"), F.from_user.id == ADMIN_ID)
async def broadcast(message: types.Message):
    text = message.text.replace("/send_all ", "")
    users = get_all_users()
    for user_id in users:
        try: await bot.send_message(user_id, text)
        except: continue
    await message.answer("✅ Рассылка завершена.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
         
