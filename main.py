import os
import sqlite3
import json
import logging
import urllib.request
import time
import requests
from datetime import datetime, timedelta

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CARD = "4441111008011946"
WEBAPP_URL = "https://rocket-online.vercel.app"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# CryptoBot API
CRYPTO_TOKEN = "466345:AADMm3mzlC6KGJmwt3r771bUPIx40CMEKhQ"
CRYPTO_API = "https://pay.crypt.bot/api"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- СБРОС ВЕБХУКА ---
try:
    urllib.request.urlopen(f"{API_URL}/deleteWebhook?drop_pending_updates=true", timeout=5)
    print("✅ Webhook сброшен")
except:
    pass

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('users.db', timeout=30, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        expiry_date TEXT,
        product_name TEXT,
        subscribed_at TEXT,
        banned INTEGER DEFAULT 0,
        ban_reason TEXT,
        last_key TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS crypto_payments (
        payment_id TEXT PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        days TEXT,
        product TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT
    )
''')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings VALUES ("cheat_status", "🟢 UNDETECTED")')
conn.commit()

# --- ФУНКЦИИ API ---
def api(method, data=None):
    url = f"{API_URL}/{method}"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode() if data else None,
            headers={'Content-Type': 'application/json'} if data else {},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"API error: {e}")
        return {'ok': False}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api("sendMessage", data)

def send_photo(chat_id, photo, caption=None, reply_markup=None):
    data = {"chat_id": chat_id, "photo": photo, "parse_mode": "HTML"}
    if caption:
        data["caption"] = caption
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api("sendPhoto", data)

def edit_message_caption(chat_id, message_id, caption, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "caption": caption, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api("editMessageCaption", data)

def get_updates(offset=None, timeout=30):
    data = {"timeout": timeout}
    if offset is not None:
        data["offset"] = offset
    return api("getUpdates", data)

def answer_callback(callback_id, text=None, show_alert=False):
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    if show_alert:
        data["show_alert"] = True
    return api("answerCallbackQuery", data)

# --- ФУНКЦИЯ ДЛЯ ЭМОДЗИ (как в файловом боте) ---
def em(emoji_id, char):
    return f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'

# --- ХРАНИЛИЩА ---
waiting = {}

# --- КНОПКИ ---
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Купить ключ", "callback_data": "buy_key", "icon_custom_emoji_id": "5156877291397055163"},
             {"text": "Мой профиль", "callback_data": "profile", "icon_custom_emoji_id": "5904630315946611415"}],
            [{"text": "Наши отзывы", "callback_data": "show_reviews", "icon_custom_emoji_id": "5938252440926163756"},
             {"text": "Статус ПО", "callback_data": "check_status", "icon_custom_emoji_id": "5208846279714560254"}],
            [{"text": "Plutonium Store", "url": WEBAPP_URL, "icon_custom_emoji_id": "5339472242529045815"}],
            [{"text": "Техподдержка", "url": "https://t.me/IllyaGarant", "icon_custom_emoji_id": "5208539876747662991"}]
        ]
    }

def get_back_button(target):
    return {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": target}]]}

# --- ЦЕНЫ ---
PRICES = {
    "so2": {"7": ("150 грн", "3.5$"), "30": ("300 грн", "7$"), "90": ("700 грн", "16.5$")},
    "zolo": {"1": "85 грн", "3": "180 грн", "7": "325 грн", "14": "400 грн", "30": "690 грн", "60": "1000 грн"},
    "impact": {"1": "115 грн", "7": "480 грн", "30": "1170 грн"},
    "king": {"1": "100 грн", "7": "425 грн", "30": "1060 грн"},
    "inferno": {"1": "80 грн", "3": "200 грн", "7": "350 грн", "15": "530 грн", "30": "690 грн", "60": "950 грн"},
    "zolo_cis": {"1": "70 грн", "3": "150 грн", "7": "250 грн", "14": "350 грн", "30": "700 грн", "60": "900 грн"}
}

CHEAT_NAMES = {
    "so2": "🦾 Plutonium APK",
    "zolo": "🔥 Zolo Cheat",
    "impact": "⚡ Impact VIP",
    "king": "👑 King Mod",
    "inferno": "💥 Inferno Cheat",
    "zolo_cis": "🎮 Zolo CIS Edition"
}

CHEAT_PHOTOS = {
    "so2": "https://files.catbox.moe/eqco0i.png",
    "zolo": "https://files.catbox.moe/opz3nu.png",
    "impact": "https://files.catbox.moe/9ztxkj.png",
    "king": "https://files.catbox.moe/vyhlec.png",
    "inferno": "https://files.catbox.moe/5vtpq1.png",
    "zolo_cis": "https://files.catbox.moe/deicc2.png"
}

# --- ОБРАБОТЧИКИ ---
def handle_start(chat_id, user_id, username, first_name):
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Вы заблокированы")
        return
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, subscribed_at) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?))
    ''', (user_id, username, first_name, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    status = cursor.execute('SELECT value FROM settings WHERE key="cheat_status"').fetchone()['value']
    
    text = (f"{em('5339472242529045815', '🔥')} <b>Plutonium Store</b>\n\n"
            f"{em('5208846279714560254', '📈')} Статус ПО: {status}\n\n"
            f"{em('5208657859499282838', '👋')} Добро пожаловать!")
    
    send_photo(chat_id, "https://files.catbox.moe/916cwt.png", text, get_main_keyboard())

def handle_profile(chat_id, user_id, message_id, username, first_name):
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Вы заблокированы")
        return
    
    user = cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    res = cursor.execute('SELECT expiry_date, product_name, last_key FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    time_left = "Нет активной подписки"
    product = "Нет"
    last_key = ""
    
    if res and res['expiry_date']:
        try:
            expiry = datetime.strptime(res['expiry_date'], '%Y-%m-%d %H:%M:%S')
            diff = expiry - datetime.now()
            if diff.total_seconds() > 0:
                days = diff.days
                hours = diff.seconds // 3600
                time_left = f"{days} дн. {hours} ч." if days > 0 else f"{hours} ч."
                product = res['product_name'] if res['product_name'] else "Plutonium"
                last_key = res['last_key'] if res['last_key'] else ""
            else:
                time_left = "❌ Истекла"
                product = res['product_name'] if res['product_name'] else "Plutonium"
        except:
            pass
    
    user_name = user['first_name'] if user and user['first_name'] else str(user_id)
    user_username = user['username'] if user and user['username'] else "Нет"
    
    text = (f"{em('5904630315946611415', '👤')} <b>Личный кабинет</b>\n\n"
            f"{em('6032693626394382504', '🆔')} <b>ID:</b> <code>{user_id}</code>\n"
            f"{em('5879770735999717115', '📛')} <b>Имя:</b> {user_name}\n"
            f"{em('5814247475141153332', '🔖')} <b>Username:</b> @{user_username}\n"
            f"{em('6041730074376410123', '📦')} <b>Товар:</b> {product}\n"
            f"{em('5891211339170326418', '⏳')} <b>Осталось:</b> {time_left}")
    
    if last_key:
        text += f"\n{em('6048733173171359488', '🔑')} <b>Ваш ключ:</b> <code>{last_key}</code>"
    
    edit_message_caption(chat_id, message_id, text, get_back_button("start"))

def handle_status(chat_id, message_id):
    status = cursor.execute('SELECT value FROM settings WHERE key="cheat_status"').fetchone()['value']
    text = f"{em('5208846279714560254', '📊')} <b>Статус ПО:</b> {status}"
    edit_message_caption(chat_id, message_id, text, get_back_button("start"))

def handle_reviews(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [{"text": "Канал с отзывами", "url": "https://t.me/plutoniumrewiews", "icon_custom_emoji_id": "6028171274939797252"}],
            [{"text": "⬅️ Назад", "callback_data": "start"}]
        ]
    }
    text = f"{em('5938252440926163756', '⭐')} <b>Наши отзывы</b>"
    edit_message_caption(chat_id, message_id, text, kb)

def handle_buy_key(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [{"text": "Standoff 2", "callback_data": "game_so2", "icon_custom_emoji_id": "5393134637667094112"}],
            [{"text": "PUBG Mobile", "callback_data": "game_pubg", "icon_custom_emoji_id": "6073605466221451561"}],
            [{"text": "⬅️ Назад", "callback_data": "start"}]
        ]
    }
    text = f"{em('5938413566624272793', '🎮')} <b>Выберите игру:</b>"
    edit_message_caption(chat_id, message_id, text, kb)

def handle_so2_menu(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [{"text": "Plutonium", "callback_data": "cheat_so2", "icon_custom_emoji_id": "5339472242529045815"}],
            [{"text": "⬅️ Назад", "callback_data": "buy_key"}]
        ]
    }
    text = (f"{em('5393134637667094112', '⚙️')} <b>Standoff 2</b>\n"
            f"{em('5938413566624272793', '🎮')} Выберите чит:")
    edit_message_caption(chat_id, message_id, text, kb)

def handle_pubg_menu(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [{"text": "Zolo", "callback_data": "cheat_zolo", "icon_custom_emoji_id": "5451653043089070124"}],
            [{"text": "Impact VIP", "callback_data": "cheat_impact", "icon_custom_emoji_id": "5276079251089547977"}],
            [{"text": "King Mod", "callback_data": "cheat_king", "icon_custom_emoji_id": "6172520285330214110"}],
            [{"text": "Inferno", "callback_data": "cheat_inferno", "icon_custom_emoji_id": "5296273418516187626"}],
            [{"text": "Zolo CIS", "callback_data": "cheat_zolo_cis", "icon_custom_emoji_id": "5451841459009379088"}],
            [{"text": "⬅️ Назад", "callback_data": "buy_key"}]
        ]
    }
    text = f"{em('6073605466221451561', '🎯')} <b>PUBG Mobile</b>\nВыберите чит:"
    edit_message_caption(chat_id, message_id, text, kb)

def show_cheat(chat_id, message_id, cheat):
    desc = f"{CHEAT_NAMES[cheat]}\n\n💰 <b>Цены:</b>\n"
    for days, price in PRICES[cheat].items():
        days_text = f"{days} дн." if days != "1" else "1 день"
        if cheat == "so2":
            uah, usd = price
            desc += f"├ {days_text}: {usd} / {uah}\n"
        else:
            desc += f"├ {days_text}: {price}\n"
    desc += "\n💳 <b>Выберите период:</b>"
    
    buttons = []
    for days in PRICES[cheat].keys():
        days_text = f"{days} дн." if days != "1" else "1 день"
        buttons.append([{"text": days_text, "callback_data": f"period_{cheat}_{days}", "icon_custom_emoji_id": "5393330385096575682"}])
    
    game = "game_so2" if cheat == "so2" else "game_pubg"
    buttons.append([{"text": "⬅️ Назад", "callback_data": game}])
    
    edit_message_caption(chat_id, message_id, desc, {"inline_keyboard": buttons})

def handle_select_period(chat_id, message_id, cheat, days):
    waiting[f"{chat_id}_product"] = cheat
    waiting[f"{chat_id}_days"] = days
    
    desc = f"{CHEAT_NAMES[cheat]}\n\n📅 {days} дн.\n"
    if cheat == "so2":
        uah, usd = PRICES[cheat][days]
        desc += f"💰 {usd} / {uah}"
    else:
        desc += f"💰 {PRICES[cheat][days]}"
    desc += "\n\n💳 <b>Выберите способ оплаты:</b>"
    
    kb = {
        "inline_keyboard": [
            [{"text": "Укр Банк", "callback_data": f"bank_{cheat}_{days}", "icon_custom_emoji_id": "5393576224729633040"}],
            [{"text": "CryptoBot", "callback_data": f"crypto_{cheat}_{days}", "icon_custom_emoji_id": "5390816416184174666"}],
            [{"text": "⬅️ Назад", "callback_data": f"cheat_{cheat}"}]
        ]
    }
    edit_message_caption(chat_id, message_id, desc, kb)

def handle_bank_payment(chat_id, message_id, cheat, days):
    waiting[f"{chat_id}_product"] = cheat
    waiting[f"{chat_id}_days"] = days
    
    price = PRICES[cheat][days][0] if cheat == "so2" else PRICES[cheat][days]
    
    text = (f"{em('5890848474563352982', '💳')} <b>Оплата банковской картой</b>\n\n"
            f"{em('5890848474563352982', '💰')} <b>Сумма:</b> {price}\n"
            f"{em('5890848474563352982', '💳')} <b>Карта:</b> <code>{CARD}</code>\n"
            f"{em('5891105528356018797', '❗')} <b>Комментарий:</b> За цифрові товари\n\n"
            f"{em('5769126056262898415', '📸')} После оплаты нажмите кнопку ниже и пришлите скриншот")
    
    kb = {
        "inline_keyboard": [
            [{"text": "Я оплатил", "callback_data": "send_receipt", "icon_custom_emoji_id": "5258205968025525531"}],
            [{"text": "Отмена", "callback_data": "start", "icon_custom_emoji_id": "5208480322731137426"}]
        ]
    }
    edit_message_caption(chat_id, message_id, text, kb)

def handle_crypto_payment(chat_id, message_id, cheat, days, user_id):
    if cheat == "so2":
        amount = float(PRICES[cheat][days][1].replace("$", ""))
    else:
        price_str = PRICES[cheat][days].replace(" грн", "")
        amount = round(int(price_str) / 43, 2)
    
    invoice = create_crypto_invoice(user_id, amount, days, cheat)
    if not invoice:
        edit_message_caption(chat_id, message_id, "❌ Ошибка создания платежа", get_back_button("start"))
        return
    
    cursor.execute('''
        INSERT INTO crypto_payments (payment_id, user_id, amount, days, product, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (str(invoice["invoice_id"]), user_id, amount, days, cheat, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    text = (f"{em('5390816416184174666', '💎')} <b>Оплата через CryptoBot</b>\n\n"
            f"💰 <b>Сумма:</b> {amount}$\n"
            f"📅 <b>Тариф:</b> {days} дней")
    
    kb = {
        "inline_keyboard": [
            [{"text": "💎 Оплатить", "url": invoice["pay_url"]}],
            [{"text": "Проверить оплату", "callback_data": f"check_crypto_{invoice['invoice_id']}", "icon_custom_emoji_id": "6039486778597970865"}],
            [{"text": "Отмена", "callback_data": "start", "icon_custom_emoji_id": "5208480322731137426"}]
        ]
    }
    edit_message_caption(chat_id, message_id, text, kb)

def handle_check_crypto(chat_id, message_id, payment_id, user_id):
    payment = check_crypto_payment(payment_id)
    
    if payment and payment.get("status") == "paid":
        res = cursor.execute('SELECT product, days FROM crypto_payments WHERE payment_id = ?', (str(payment_id),)).fetchone()
        if res:
            product, days = res
            expiry = (datetime.now() + timedelta(days=int(days))).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', (expiry, CHEAT_NAMES[product], user_id))
            cursor.execute('UPDATE crypto_payments SET status = "paid" WHERE payment_id = ?', (str(payment_id),))
            conn.commit()
            edit_message_caption(chat_id, message_id, 
                f"{em('5938252440926163756', '✅')} <b>Оплата подтверждена!</b>\n\n📅 Подписка до {expiry}",
                get_back_button("start"))
            send_message(ADMIN_ID, f"{em('6039486778597970865', '💰')} <b>Новый крипто-платёж</b>\n👤 {user_id}\n📅 {days} дней\n💎 {CHEAT_NAMES[product]}")
    else:
        answer_callback(payment_id, "⏳ Платёж ещё не подтверждён", True)

def handle_send_receipt(chat_id, message_id, user_id):
    waiting[f"{user_id}_waiting"] = "receipt"
    send_message(chat_id, f"{em('5769126056262898415', '📸')} <b>Отправьте скриншот чека</b> (одним фото)")

# --- CRYPTOBOT ---
def create_crypto_invoice(user_id, amount, days, product):
    url = f"{CRYPTO_API}/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    data = {
        "asset": "USDT",
        "amount": amount,
        "description": f"{CHEAT_NAMES[product]} - {days} дней",
        "paid_btn_name": "openBot",
        "paid_btn_url": f"https://t.me/plutoniumfilesBot",
        "payload": f"{user_id}|{days}|{product}"
    }
    try:
        r = requests.post(url, headers=headers, json=data)
        if r.status_code == 200 and r.json().get("ok"):
            return r.json()["result"]
    except Exception as e:
        print(f"CryptoBot error: {e}")
    return None

def check_crypto_payment(payment_id):
    url = f"{CRYPTO_API}/getInvoices"
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    params = {"invoice_ids": payment_id}
    try:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200 and r.json().get("ok"):
            items = r.json()["result"].get("items", [])
            if items:
                return items[0]
    except Exception as e:
        print(f"Check payment error: {e}")
    return None

# --- АДМИН-КОМАНДЫ ---
def handle_set_status(chat_id, text):
    new_status = text.replace("/set_status ", "").strip()
    cursor.execute('UPDATE settings SET value = ? WHERE key = "cheat_status"', (new_status,))
    conn.commit()
    send_message(chat_id, f"{em('5938252440926163756', '✅')} Статус обновлен на: {new_status}")

def handle_ban(chat_id, text):
    args = text.split(maxsplit=1)
    if len(args) < 2:
        send_message(chat_id, "❌ /ban [id] [причина]")
        return
    parts = args[1].split(maxsplit=1)
    target_id = int(parts[0])
    reason = parts[1] if len(parts) > 1 else "Нарушение правил"
    
    cursor.execute('UPDATE users SET banned = 1, ban_reason = ? WHERE user_id = ?', (reason, target_id))
    conn.commit()
    
    try:
        send_message(target_id, f"⛔️ <b>Вы заблокированы</b>\nПричина: {reason}")
    except:
        pass
    send_message(chat_id, f"{em('6030563507299160824', '✅')} Пользователь {target_id} забанен")

def handle_unban(chat_id, text):
    args = text.split()
    if len(args) < 2:
        send_message(chat_id, "❌ /unban [id]")
        return
    target_id = int(args[1])
    cursor.execute('UPDATE users SET banned = 0, ban_reason = NULL WHERE user_id = ?', (target_id,))
    conn.commit()
    try:
        send_message(target_id, f"✅ <b>Вы разблокированы</b>")
    except:
        pass
    send_message(chat_id, f"{em('6028205772117118673', '✅')} Пользователь {target_id} разблокирован")

def handle_users(chat_id):
    total = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    banned = cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1').fetchone()[0]
    active = cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0]
    send_message(chat_id, 
        f"{em('5904630315946611415', '👥')} <b>Статистика пользователей:</b>\n\n"
        f"{em('5208846279714560254', '📊')} Всего: {total}\n"
        f"{em('5938252440926163756', '✅')} Активных: {active}\n"
        f"{em('5208480322731137426', '⛔')} Забанено: {banned}")

def handle_broadcast(chat_id, user_id):
    waiting[f"{user_id}_broadcast"] = "waiting"
    send_message(chat_id, f"{em('5208846279714560254', '📢')} <b>Отправь сообщение для рассылки</b>")

# --- ГЛАВНЫЙ ЦИКЛ ---
def main():
    logger.info("🚀 Запуск Plutonium Store")
    logger.info(f"👑 Админ ID: {ADMIN_ID}")
    
    offset = 0
    while True:
        try:
            updates = get_updates(offset, timeout=30)
            if updates.get('ok') and updates.get('result'):
                for update in updates['result']:
                    offset = update['update_id'] + 1
                    
                    if 'callback_query' in update:
                        cb = update['callback_query']
                        cb_id = cb['id']
                        user_id = cb['from']['id']
                        username = cb['from'].get('username')
                        first_name = cb['from'].get('first_name')
                        chat_id = cb['message']['chat']['id']
                        message_id = cb['message']['message_id']
                        data = cb['data']
                        
                        if data == "start":
                            handle_start(chat_id, user_id, username, first_name)
                        elif data == "profile":
                            handle_profile(chat_id, user_id, message_id, username, first_name)
                        elif data == "check_status":
                            handle_status(chat_id, message_id)
                        elif data == "show_reviews":
                            handle_reviews(chat_id, message_id)
                        elif data == "buy_key":
                            handle_buy_key(chat_id, message_id)
                        elif data == "game_so2":
                            handle_so2_menu(chat_id, message_id)
                        elif data == "game_pubg":
                            handle_pubg_menu(chat_id, message_id)
                        elif data == "cheat_so2":
                            show_cheat(chat_id, message_id, "so2")
                        elif data == "cheat_zolo":
                            show_cheat(chat_id, message_id, "zolo")
                        elif data == "cheat_impact":
                            show_cheat(chat_id, message_id, "impact")
                        elif data == "cheat_king":
                            show_cheat(chat_id, message_id, "king")
                        elif data == "cheat_inferno":
                            show_cheat(chat_id, message_id, "inferno")
                        elif data == "cheat_zolo_cis":
                            show_cheat(chat_id, message_id, "zolo_cis")
                        elif data.startswith("period_"):
                            parts = data.split("_")
                            handle_select_period(chat_id, message_id, parts[1], parts[2])
                        elif data.startswith("bank_"):
                            parts = data.split("_")
                            handle_bank_payment(chat_id, message_id, parts[1], parts[2])
                        elif data.startswith("crypto_"):
                            parts = data.split("_")
                            handle_crypto_payment(chat_id, message_id, parts[1], parts[2], user_id)
                        elif data.startswith("check_crypto_"):
                            payment_id = int(data.replace("check_crypto_", ""))
                            handle_check_crypto(chat_id, message_id, payment_id, user_id)
                        elif data == "send_receipt":
                            handle_send_receipt(chat_id, message_id, user_id)
                        answer_callback(cb_id)
                    
                    elif 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        user_id = msg['from']['id']
                        username = msg['from'].get('username')
                        first_name = msg['from'].get('first_name')
                        text = msg.get('text', '')
                        
                        # /start
                        if text == "/start":
                            handle_start(chat_id, user_id, username, first_name)
                        
                        # Админ-команды
                        elif text.startswith("/set_status") and user_id == ADMIN_ID:
                            new_status = text.replace("/set_status ", "").strip()
                            cursor.execute('UPDATE settings SET value = ? WHERE key = "cheat_status"', (new_status,))
                            conn.commit()
                            send_message(chat_id, f"✅ Статус обновлен на: {new_status}")
                        
                        elif text.startswith("/ban") and user_id == ADMIN_ID:
                            args = text.split(maxsplit=1)
                            if len(args) >= 2:
                                parts = args[1].split(maxsplit=1)
                                target_id = int(parts[0])
                                reason = parts[1] if len(parts) > 1 else "Нарушение правил"
                                cursor.execute('UPDATE users SET banned = 1, ban_reason = ? WHERE user_id = ?', (reason, target_id))
                                conn.commit()
                                try:
                                    send_message(target_id, f"⛔️ <b>Вы заблокированы</b>\nПричина: {reason}")
                                except:
                                    pass
                                send_message(chat_id, f"✅ Пользователь {target_id} забанен")
                        
                        elif text.startswith("/unban") and user_id == ADMIN_ID:
                            args = text.split()
                            if len(args) >= 2:
                                target_id = int(args[1])
                                cursor.execute('UPDATE users SET banned = 0, ban_reason = NULL WHERE user_id = ?', (target_id,))
                                conn.commit()
                                try:
                                    send_message(target_id, f"✅ <b>Вы разблокированы</b>")
                                except:
                                    pass
                                send_message(chat_id, f"✅ Пользователь {target_id} разблокирован")
                        
                        elif text == "/users" and user_id == ADMIN_ID:
                            total = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
                            banned = cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1').fetchone()[0]
                            active = cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0]
                            send_message(chat_id, f"👥 Статистика:\nВсего: {total}\nАктивных: {active}\nЗабанено: {banned}")
                        
                        elif text == "/broadcast" and user_id == ADMIN_ID:
                            waiting[f"{user_id}_broadcast"] = "waiting"
                            send_message(chat_id, "📢 Отправь сообщение для рассылки")
                        
                        elif waiting.get(f"{user_id}_broadcast") == "waiting" and user_id == ADMIN_ID:
                            waiting[f"{user_id}_broadcast"] = None
                            users = cursor.execute('SELECT user_id FROM users WHERE banned = 0').fetchall()
                            if not users:
                                send_message(chat_id, "📭 Нет пользователей")
                            else:
                                sent = 0
                                for u in users:
                                    try:
                                        if 'text' in msg:
                                            send_message(u['user_id'], msg['text'])
                                        elif 'photo' in msg:
                                            send_photo(u['user_id'], msg['photo'][-1]['file_id'], msg.get('caption', ''))
                                        sent += 1
                                    except:
                                        pass
                                    time.sleep(0.05)
                                send_message(chat_id, f"✅ Рассылка завершена!\nОтправлено: {sent}")
                        
                        # Обработка чека
                        elif waiting.get(f"{user_id}_waiting") == "receipt" and 'photo' in msg:
                            waiting[f"{user_id}_waiting"] = None
                            product = waiting.get(f"{user_id}_product", "Unknown")
                            days = waiting.get(f"{user_id}_days", "0")
                            
                            adm_kb = {
                                "inline_keyboard": [
                                    [{"text": "Одобрить", "callback_data": f"adm_ok_{user_id}", "icon_custom_emoji_id": "5208657859499282838"}],
                                    [{"text": "Отклонить", "callback_data": f"adm_no_{user_id}", "icon_custom_emoji_id": "5208480322731137426"}]
                                ]
                            }
                            send_photo(
                                ADMIN_ID,
                                msg['photo'][-1]['file_id'],
                                f"🔔 <b>Чек от {user_id}</b>\n📦 Товар: {CHEAT_NAMES.get(product, 'Unknown')}\n📅 Тариф: {days} дней",
                                adm_kb
                            )
                            send_message(chat_id, "✅ Чек отправлен администратору!")
                        
                        # Отмена
                        elif text == "/cancel":
                            if waiting.get(f"{user_id}_waiting"):
                                waiting[f"{user_id}_waiting"] = None
                                send_message(chat_id, "✅ Операция отменена")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(5)

# ---------- ОБРАБОТКА АДМИН-РЕШЕНИЙ ----------
def handle_admin_decision(chat_id, data, user_id):
    parts = data.split("_")
    if parts[1] == "ok":
        target_id = int(parts[2])
        product = waiting.get(f"{target_id}_product", "Unknown")
        days = waiting.get(f"{target_id}_days", "0")
        
        waiting[f"admin_{target_id}_product"] = product
        waiting[f"admin_{target_id}_days"] = days
        waiting[f"admin_target"] = target_id
        
        send_message(chat_id, "📎 <b>Отправьте файл с читом</b> (или текст с инструкцией)")
        waiting[f"admin_{target_id}_waiting"] = "file"
    else:
        target_id = int(parts[2])
        send_message(target_id, "❌ Ваша оплата была отклонена администратором.")
        send_message(chat_id, "❌ Отклонено")

# ---------- ФАЙЛ ОТ АДМИНА ----------
def handle_admin_file(chat_id, user_id, msg):
    target_id = waiting.get(f"admin_target", 0)
    if not target_id:
        return
    
    file_id = None
    file_text = None
    
    if 'document' in msg:
        file_id = msg['document']['file_id']
    elif 'photo' in msg:
        file_id = msg['photo'][-1]['file_id']
    else:
        file_text = msg.get('text', '')
    
    waiting[f"admin_{target_id}_file"] = file_id
    waiting[f"admin_{target_id}_file_text"] = file_text
    waiting[f"admin_{target_id}_waiting"] = "key"
    send_message(chat_id, "🔑 <b>Введите ключ активации</b>")

# ---------- КЛЮЧ ОТ АДМИНА ----------
def handle_admin_key(chat_id, user_id, key):
    target_id = waiting.get(f"admin_target", 0)
    if not target_id:
        return
    
    product = waiting.get(f"admin_{target_id}_product", "Unknown")
    days = int(waiting.get(f"admin_{target_id}_days", "0"))
    file_id = waiting.get(f"admin_{target_id}_file")
    file_text = waiting.get(f"admin_{target_id}_file_text")
    
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    product_name = CHEAT_NAMES.get(product, "Plutonium")
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, expiry_date, product_name, subscribed_at, banned, last_key) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?), 0, ?)
    ''', (target_id, expiry_date, product_name, target_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), key))
    conn.commit()
    
    text = (f"✅ <b>Заказ активирован!</b>\n\n"
            f"📅 <b>Действует до:</b> {expiry_date}\n"
            f"🔑 <b>Ключ:</b> <code>{key}</code>\n\n"
            f"💜 Благодарим за покупку в Plutonium Store!")
    
    try:
        if file_id:
            send_document(target_id, file_id, text)
        elif file_text:
            send_message(target_id, text + f"\n\n📝 {file_text}")
        else:
            send_message(target_id, text)
        
        send_message(chat_id, "✅ Готово! Товар выдан пользователю.")
    except Exception as e:
        send_message(chat_id, f"❌ Ошибка при отправке: {e}")
    
    # Очищаем
    for k in list(waiting.keys()):
        if f"admin_{target_id}" in k or k == "admin_target":
            del waiting[k]

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    main()
