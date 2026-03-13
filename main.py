import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiocryptopay import AioCryptoPay, Networks

# --- КОНФИГ ---
TOKEN = "8222233131:AAF0FMDqGv7dLK1doTa6GrMOHB_nkZBbphk"
ADMIN_ID = 1471307057
CRYPTO_TOKEN = "338748:AAcBI08cRpvDBk6mb9V2hPo3zRX0miDxdyc"
CARD_REQUISITES = "4441111008011946"

bot = Bot(token=TOKEN)
dp = Dispatcher()
crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET)

class OrderProcess(StatesGroup):
    waiting_for_receipt = State()

# --- КЛАВИАТУРЫ ---
def main_kb():
    kb = [
        [InlineKeyboardButton(text="🎮 Standoff 2", callback_data="category_so2")],
        [InlineKeyboardButton(text="📝 Отзывы", url="https://t.me/plutoniumrewiews")],
        [InlineKeyboardButton(text="📢 Канал", url="https://t.me/OfficialPlutonium")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def root_choice_kb():
    kb = [
        [InlineKeyboardButton(text="📱 Non Root", callback_data="type_nonroot")],
        [InlineKeyboardButton(text="🔓 Root", callback_data="type_root")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def tariffs_kb():
    kb = [
        [InlineKeyboardButton(text="🗓 7 Days - 150 UAH", callback_data="buy_7")],
        [InlineKeyboardButton(text="🗓 30 Days - 300 UAH", callback_data="buy_30")],
        [InlineKeyboardButton(text="🗓 90 Days - 700 UAH", callback_data="buy_90")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="type_nonroot")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def payment_method_kb(days, price):
    kb = [
        [InlineKeyboardButton(text="💎 CryptoBot (USDT/TON)", callback_data=f"pay_crypto_{days}_{price}")],
        [InlineKeyboardButton(text="💳 Укр Банки (UAH)", callback_data=f"pay_bank_{days}_{price}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="type_nonroot")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_cmd(event: Message | types.CallbackQuery):
    text = (
        "<b>Welcome to Plut.</b>\n\n"
        "• Единственный рабочий чит без рут прав и без бана.\n"
        "• Огромное кол-во реально полезных функций.\n"
        "• Лучший скинченжер на рынке модификаций с сохранением в облаке."
    )
    photo_url = "https://i.imgur.com/your_image.jpg" # ЗАМЕНИ НА СВОЮ ССЫЛКУ
    
    if isinstance(event, Message):
        await event.answer_photo(photo=photo_url, caption=text, reply_markup=main_kb(), parse_mode="HTML")
    else:
        await event.message.edit_caption(caption=text, reply_markup=main_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "category_so2")
async def choose_type(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption="<b>Выбирете товар</b>\n\nВыберите тариф или категорию из списка ниже 👇",
        reply_markup=root_choice_kb(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "type_nonroot")
async def non_root_tariffs(call: types.CallbackQuery):
    text = (
        "<b>Модификация No ban последней версии</b>\n\n"
        "- Данная модификация полностью без бана и без рут прав\n"
        "- Наш чит полностью безопасен, мы разработали уникальный обход!\n"
        "- Очень легкая установка и инструкция после оплаты\n"
        "- Подойдет на все версии Android.\n\n"
        "Выберите тариф из списка ниже 👇"
    )
    await call.message.edit_caption(caption=text, reply_markup=tariffs_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def choose_pay_method(call: types.CallbackQuery):
    days = call.data.split("_")[1]
    prices = {"7": 150, "30": 300, "90": 700}
    price = prices[days]
    await call.message.edit_caption(
        caption=f"<b>Оплата Plutonium - {days} дней</b>\nЦена: {price} грн.\n\nВыберите способ оплаты:",
        reply_markup=payment_method_kb(days, price),
        parse_mode="HTML"
    )

# --- ОПЛАТА БАНК ---
@dp.callback_query(F.data.startswith("pay_bank_"))
async def bank_pay(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split("_")
    await state.update_data(item=f"Plutonium {data[2]} days")
    
    text = (
        f"🇺🇦 <b>Реквизиты для оплаты:</b>\n"
        f"<code>{CARD_REQUISITES}</code>\n"
        f"Сумма: <b>{data[3]} грн</b>\n\n"
        f"❗️ <b>Комментарий обязательно:</b> За цифрові товари\n\n"
        "После оплаты отправьте <b>ФОТО ЧЕКА</b> сюда боту."
    )
    await call.message.edit_caption(caption=text, parse_mode="HTML")
    await state.set_state(OrderProcess.waiting_for_receipt)

@dp.message(OrderProcess.waiting_for_receipt, F.photo)
async def handle_receipt(message: Message, state: FSMContext):
    user_data = await state.get_data()
    await message.answer("✅ Чек отправлен админу. Ожидайте подтверждения.")
    
    # Пересылка админу
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"🔔 <b>Новый заказ!</b>\nТовар: {user_data['item']}\nЮзер: @{message.from_user.username}\nID: {message.from_user.id}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{message.from_user.id}")]
        ]),
        parse_mode="HTML"
    )
    await state.clear()

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
