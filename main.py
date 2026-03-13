import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# --- КОНФИГ ---
TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CHANNEL_ID = "@OfficialPlutonium" # ID канала для проверки подписки
MY_TON_WALLET = "UQATIzX89EOOTqfsr8KE64MXvVSa4CGybjwmkPv3-yHbI3ZE"
CARD_REQUISITES = "4441111008011946"
PROFILE_PHOTO = "https://files.catbox.moe/glswza.jpg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class States(StatesGroup):
    waiting_for_receipt = State()
    waiting_for_broadcast = State()

# --- ПРОВЕРКА ПОДПИСКИ ---
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status != "left"
    except:
        return True # Если бот не админ в канале, пропускаем

# --- КЛАВИАТУРЫ ---
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Купить ключ", callback_data="category_so2")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="💬 Отзывы", url="https://t.me/plutoniumrewiews")],
        [InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me/IllyaGarant")]
    ])

def sub_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url="https://t.me/OfficialPlutonium")],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="start")]
    ])

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
@dp.callback_query(F.data == "start")
async def start_cmd(event: Message | types.CallbackQuery):
    user_id = event.from_user.id if isinstance(event, Message) else event.message.chat.id
    
    if not await check_sub(user_id):
        text = "❌ <b>Доступ ограничен!</b>\nДля использования бота подпишитесь на наш канал."
        if isinstance(event, Message):
            await event.answer(text, reply_markup=sub_kb(), parse_mode="HTML")
        else:
            await event.message.edit_text(text, reply_markup=sub_kb(), parse_mode="HTML")
        return

    text = (
        "<b>Welcome to Plut.</b>\n\n"
        "- Единственный рабочий чит без рут прав и без бана.\n"
        "- Огромное кол-во полезных функций.\n"
        "- Лучший скинченжер на рынке.\n\n"
        "Выберите нужное действие ниже 👇"
    )
    if isinstance(event, Message):
        await event.answer(text, reply_markup=main_kb(), parse_mode="HTML")
    else:
        # Пытаемся удалить старое сообщение с фото профиля, если оно было
        try: await event.message.delete()
        except: pass
        await event.bot.send_message(event.from_user.id, text, reply_markup=main_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "profile")
async def profile_cmd(call: types.CallbackQuery):
    text = (
        f"👤 <b>Ваш профиль:</b>\n"
        f"🆔 ID: <code>{call.from_user.id}</code>\n"
        f"🏷 Имя: {call.from_user.first_name}\n\n"
        f"Статус: Пользователь\n"
        f"Ключи: отсутствуют"
    )
    await call.message.delete()
    await call.message.answer_photo(photo=PROFILE_PHOTO, caption=text, reply_markup=main_kb(), parse_mode="HTML")

# --- ЛОГИКА ОПЛАТЫ (ОБНОВЛЕННАЯ) ---
@dp.callback_query(F.data == "category_so2")
async def shop_menu(call: types.CallbackQuery):
    # Тут твоя логика выбора тарифов из прошлых ответов
    # Для краткости вызову сразу выбор метода оплаты
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗓 7 Days - 150 грн", callback_data="pay_bank_7_150")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    await call.message.edit_text("<b>Выберите тариф Standoff 2:</b>", reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("pay_bank_"))
async def pay_bank(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split("_")
    await state.update_data(amount=data[3], item=data[2])
    text = f"💳 <b>Оплата на карту:</b>\n<code>{CARD_REQUISITES}</code>\nСумма: {data[3]} грн\n\nОтправьте скриншот чека:"
    await call.message.edit_text(text, parse_mode="HTML")
    await state.set_state(States.waiting_for_receipt)

@dp.message(States.waiting_for_receipt, F.photo)
async def get_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ Чек получен! Ожидайте проверки админом.")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"adm_confirm_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_decline_{message.from_user.id}")]
    ])
    
    await bot.send_photo(
        ADMIN_ID, 
        photo=message.photo[-1].file_id,
        caption=f"💰 <b>Новый чек!</b>\nТовар: {data['item']} дней\nСумма: {data['amount']} грн\nЮзер: @{message.from_user.username}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.clear()

# --- КНОПКИ ДЛЯ АДМИНА ---
@dp.callback_query(F.data.startswith("adm_"))
async def admin_action(call: types.CallbackQuery):
    action = call.data.split("_")[1]
    user_id = call.data.split("_")[2]
    
    if action == "confirm":
        await bot.send_message(user_id, "✅ <b>Оплата принята!</b>\nВы успешно приобрели Plutonium. Скоро админ напишет вам для выдачи ключа и инструкции.", parse_mode="HTML")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🟢 ПОДТВЕРЖДЕНО")
    else:
        await bot.send_message(user_id, "❌ <b>Оплата отклонена.</b>\nВаш чек не прошел проверку. Свяжитесь с поддержкой.")
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔴 ОТКЛОНЕНО")

# --- РАССЫЛКА ---
@dp.message(Command("send"), F.from_user.id == ADMIN_ID)
async def start_broadcast(message: Message, state: FSMContext):
    await message.answer("Введите текст для рассылки всем пользователям:")
    await state.set_state(States.waiting_for_broadcast)

@dp.message(States.waiting_for_broadcast)
async def do_broadcast(message: Message, state: FSMContext):
    # Тут нужна БД для рассылки всем, но пока отправим тебе для теста
    await message.answer(f"📢 Рассылка запущена (в полной версии здесь будет цикл по БД)")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
                              
