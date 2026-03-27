import os
import sqlite3
import json
import logging
import urllib.request
import time
import threading
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
        last_name TEXT,
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

def send_document(chat_id, document, caption=None):
    data = {"chat_id": chat_id, "document": document, "parse_mode": "HTML"}
    if caption:
        data["caption"] = caption
    return api("sendDocument", data)

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

# --- ХРАНИЛИЩА ---
waiting = {}
processed = set()

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

def get_ban_kb(target_id):
    return {
        "inline_keyboard": [
            [{"text": "🔒 ЗАБАНИТЬ", "callback_data": f"ban_do_{target_id}", "icon_custom_emoji_id": "6030563507299160824"}],
            [{"text": "🔓 РАЗБАНИТЬ", "callback_data": f"unban_do_{target_id}", "icon_custom_emoji_id": "6028205772117118673"}],
            [{"text": "❌ Отмена", "callback_data": "a_ban", "icon_custom_emoji_id": "5774022692642492953"}]
        ]
    }

# --- ЦЕНЫ ---
PRICES = {
    "so2": {"7": ("150 грн", "3.5$"), "30": ("300 грн", "7$"), "90": ("700 грн", "16.5$")},
    "zolo": {"1": "85 грн", "3": "180 грн", "7": "325 грн", "14": "400 грн", "30": "690 грн", "60": "1000 грн"},
    "impact": {"1": "115 грн", "7": "480 грн", "30": "1170 грн"},
    "king": {"1": "100 грн", "7": "425 грн", "30": "1060 грн"},
    "inferno": {"1": "80 грн", "3": "200 грн", "7": "350 грн", "15": "530 грн", "30": "690 грн", "60": "950 грн"},
    "zolo_cis": {"1": "70 грн", "3": "150 грн", "7": "250 грн", "14": "350 грн", "30": "700 грн", "60": "900 грн"}
}

# --- НАЗВАНИЯ ЧИТОВ ---
CHEAT_NAMES = {
    "so2": "🦾 Plutonium APK",
    "zolo": "🔥 Zolo Cheat",
    "impact": "⚡ Impact VIP",
    "king": "👑 King Mod",
    "inferno": "💥 Inferno Cheat",
    "zolo_cis": "🎮 Zolo CIS Edition"
}

# --- ФОТО ЧИТОВ ---
CHEAT_PHOTOS = {
    "so2": "https://files.catbox.moe/eqco0i.png",
    "zolo": "https://files.catbox.moe/opz3nu.png",
    "impact": "https://files.catbox.moe/9ztxkj.png",
    "king": "https://files.catbox.moe/vyhlec.png",
    "inferno": "https://files.catbox.moe/5vtpq1.png",
    "zolo_cis": "https://files.catbox.moe/deicc2.png"
}

# --- ФУНКЦИИ CRYPTOBOT ---
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

# ---------- СТАРТ ----------
def handle_start(chat_id, user_id, username=None, first_name=None):
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Вы заблокированы")
        return
    
    # Сохраняем или обновляем пользователя
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, subscribed_at) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?))
    ''', (user_id, username, first_name, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    status = cursor.execute('SELECT value FROM settings WHERE key="cheat_status"').fetchone()['value']
    
    text = (f"<tg-emoji emoji-id=\"5339472242529045815\">🔥</tg-emoji> <b>Plutonium Store</b>\n\n"
            f"<tg-emoji emoji-id=\"5208846279714560254\">📈</tg-emoji> Статус ПО: {status}\n\n"
            f"<tg-emoji emoji-id=\"5208657859499282838\">👋</tg-emoji> Добро пожаловать!")
    
    send_photo(chat_id, "https://files.catbox.moe/916cwt.png", text, get_main_keyboard())

# ---------- ПРОФИЛЬ ----------
def handle_profile(chat_id, user_id, message_id, username=None, first_name=None):
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Вы заблокированы")
        return
    
    # Получаем данные пользователя
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
                if days > 0:
                    time_left = f"{days} дн. {hours} ч."
                else:
                    time_left = f"{hours} ч."
                product = res['product_name'] if res['product_name'] else "Plutonium"
                last_key = res['last_key'] if res['last_key'] else ""
            else:
                time_left = "❌ Истекла"
                product = res['product_name'] if res['product_name'] else "Plutonium"
        except:
            pass
    
    user_name = user['first_name'] if user and user['first_name'] else str(user_id)
    user_username = user['username'] if user and user['username'] else "Нет"
    
    text = (f"<tg-emoji emoji-id=\"5904630315946611415\">👤</tg-emoji> <b>Личный кабинет</b>\n\n"
            f"<tg-emoji emoji-id=\"6032693626394382504\">🆔</tg-emoji> <b>ID:</b> <code>{user_id}</code>\n"
            f"<tg-emoji emoji-id=\"5879770735999717115\">📛</tg-emoji> <b>Имя:</b> {user_name}\n"
            f"<tg-emoji emoji-id=\"5814247475141153332\">🔖</tg-emoji> <b>Username:</b> @{user_username}\n"
            f"<tg-emoji emoji-id=\"6041730074376410123\">📦</tg-emoji> <b>Товар:</b> {product}\n"
            f"<tg-emoji emoji-id=\"5891211339170326418\">⏳</tg-emoji> <b>Осталось:</b> {time_left}")
    
    if last_key:
        text += f"\n<tg-emoji emoji-id=\"6048733173171359488\">🔑</tg-emoji> <b>Ваш ключ:</b> <code>{last_key}</code>"
    
    edit_message_caption(chat_id, message_id, text, get_back_button("start"))

# ---------- СТАТУС ----------
def handle_status(chat_id, message_id):
    status = cursor.execute('SELECT value FROM settings WHERE key="cheat_status"').fetchone()['value']
    text = f"<tg-emoji emoji-id=\"5208846279714560254\">📊</tg-emoji> <b>Статус ПО:</b> {status}"
    edit_message_caption(chat_id, message_id, text, get_back_button("start"))

# ---------- ОТЗЫВЫ ----------
def handle_reviews(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [{"text": "Канал с отзывами", "url": "https://t.me/plutoniumrewiews", "icon_custom_emoji_id": "6028171274939797252"}],
            [{"text": "⬅️ Назад", "callback_data": "start"}]
        ]
    }
    text = f"<tg-emoji emoji-id=\"5938252440926163756\">⭐</tg-emoji> <b>Наши отзывы</b>"
    edit_message_caption(chat_id, message_id, text, kb)

# ---------- МЕНЮ ПОКУПКИ ----------
def handle_buy_key(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [{"text": "Standoff 2", "callback_data": "game_so2", "icon_custom_emoji_id": "5393134637667094112"}],
            [{"text": "PUBG Mobile", "callback_data": "game_pubg", "icon_custom_emoji_id": "6073605466221451561"}],
            [{"text": "⬅️ Назад", "callback_data": "start"}]
        ]
    }
    text = f"<tg-emoji emoji-id=\"5938413566624272793\">🎮</tg-emoji> <b>Выберите игру:</b>"
    edit_message_caption(chat_id, message_id, text, kb)

# ---------- STANDOFF 2 ----------
def handle_so2_menu(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [{"text": "Plutonium", "callback_data": "cheat_so2", "icon_custom_emoji_id": "5339472242529045815"}],
            [{"text": "⬅️ Назад", "callback_data": "buy_key"}]
        ]
    }
    text = (f"<tg-emoji emoji-id=\"5393134637667094112\">⚙️</tg-emoji> <b>Standoff 2</b>\n"
            f"<tg-emoji emoji-id=\"5938413566624272793\">🎮</tg-emoji> Выберите чит:")
    edit_message_caption(chat_id, message_id, text, kb)

# ---------- PUBG ----------
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
    text = f"<tg-emoji emoji-id=\"6073605466221451561\">🎯</tg-emoji> <b>PUBG Mobile</b>\nВыберите чит:"
    edit_message_caption(chat_id, message_id, text, kb)

# ---------- ПОКАЗ ЧИТА ----------
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
    
    kb = {"inline_keyboard": buttons}
    edit_message_caption(chat_id, message_id, desc, kb)

# ---------- ВЫБОР ПЕРИОДА ----------
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

# ---------- ОПЛАТА БАНКОМ ----------
def handle_bank_payment(chat_id, message_id, cheat, days):
    waiting[f"{chat_id}_product"] = cheat
    waiting[f"{chat_id}_days"] = days
    
    price = PRICES[cheat][days][0] if cheat == "so2" else PRICES[cheat][days]
    
    text = (f"<tg-emoji emoji-id=\"5890848474563352982\">💳</tg-emoji> <b>Оплата банковской картой</b>\n\n"
            f"<tg-emoji emoji-id=\"5890848474563352982\">💰</tg-emoji> <b>Сумма:</b> {price}\n"
            f"<tg-emoji emoji-id=\"5890848474563352982\">💳</tg-emoji> <b>Карта:</b> <code>{CARD}</code>\n"
            f"<tg-emoji emoji-id=\"5891105528356018797\">❗</tg-emoji> <b>Комментарий:</b> За цифрові товари\n\n"
            f"<tg-emoji emoji-id=\"5769126056262898415\">📸</tg-emoji> После оплаты нажмите кнопку ниже и пришлите скриншот")
    
    kb = {
        "inline_keyboard": [
            [{"text": "Я оплатил", "callback_data": "send_receipt", "icon_custom_emoji_id": "5258205968025525531"}],
            [{"text": "Отмена", "callback_data": "start", "icon_custom_emoji_id": "5208480322731137426"}]
        ]
    }
    edit_message_caption(chat_id, message_id, text, kb)

# ---------- ОПЛАТА CRYPTO ----------
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
    
    text = (f"<tg-emoji emoji-id=\"5390816416184174666\">💎</tg-emoji> <b>Оплата через CryptoBot</b>\n\n"
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

# ---------- ПРОВЕРКА CRYPTO ПЛАТЕЖА ----------
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
                f"<tg-emoji emoji-id=\"5938252440926163756\">✅</tg-emoji> <b>Оплата подтверждена!</b>\n\n📅 Подписка до {expiry}",
                get_back_button("start"))
            send_message(ADMIN_ID, f"<tg-emoji emoji-id=\"6039486778597970865\">💰</tg-emoji> <b>Новый крипто-платёж</b>\n👤 {user_id}\n📅 {days} дней\n💎 {CHEAT_NAMES[product]}")
    else:
        answer_callback(payment_id, "⏳ Платёж ещё не подтверждён", True)

# ---------- ОТПРАВКА ЧЕКА ----------
def handle_send_receipt(chat_id, message_id, user_id):
    waiting[f"{user_id}_waiting"] = "receipt"
    send_message(chat_id, f"<tg-emoji emoji-id=\"5769126056262898415\">📸</tg-emoji> <b>Отправьте скриншот чека</b> (одним фото)")

# ---------- АДМИН-КОМАНДЫ ----------
def handle_set_status(chat_id, text):
    new_status = text.replace("/set_status ", "").strip()
    cursor.execute('UPDATE settings SET value = ? WHERE key = "cheat_status"', (new_status,))
    conn.commit()
    send_message(chat_id, f"<tg-emoji emoji-id=\"5938252440926163756\">✅</tg-emoji> Статус обновлен на: {new_status}")

def handle_broadcast(chat_id, user_id):
    waiting[f"{user_id}_broadcast"] = "waiting"
    send_message(chat_id, f"<tg-emoji emoji-id=\"5208846279714560254\">📢</tg-emoji> <b>Отправь сообщение для рассылки</b> (текст, фото, видео или документ)")

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
    send_message(chat_id, f"<tg-emoji emoji-id=\"6030563507299160824\">✅</tg-emoji> Пользователь {target_id} забанен")

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
    send_message(chat_id, f"<tg-emoji emoji-id=\"6028205772117118673\">✅</tg-emoji> Пользователь {target_id} разблокирован")

def handle_users(chat_id):
    total = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    banned = cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1').fetchone()[0]
    active = cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0]
    send_message(chat_id, 
        f"<tg-emoji emoji-id=\"5904630315946611415\">👥</tg-emoji> <b>Статистика пользователей:</b>\n\n"
        f"<tg-emoji emoji-id=\"5208846279714560254\">📊</tg-emoji> Всего: {total}\n"
        f"<tg-emoji emoji-id=\"5938252440926163756\">✅</tg-emoji> Активных: {active}\n"
        f"<tg-emoji emoji-id=\"5208480322731137426\">⛔</tg-emoji> Забанено: {banned}")

# ---------- ГЛАВНЫЙ ЦИКЛ ----------
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
                    
                    # Callback
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
                    
                    # Сообщение
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
                            handle_set_status(chat_id, text)
                        elif text.startswith("/ban") and user_id == ADMIN_ID:
                            handle_ban(chat_id, text)
                        elif text.startswith("/unban") and user_id == ADMIN_ID:
                            handle_unban(chat_id, text)
                        elif text == "/users" and user_id == ADMIN_ID:
                            handle_users(chat_id)
                        elif text == "/broadcast" and user_id == ADMIN_ID:
                            handle_broadcast(chat_id, user_id)
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
                                        elif 'video' in msg:
                                            send_video(u['user_id'], msg['video']['file_id'], msg.get('caption', ''))
                                        sent += 1
                                    except:
                                        pass
                                    time.sleep(0.05)
                                send_message(chat_id, f"<tg-emoji emoji-id=\"5938252440926163756\">✅</tg-emoji> Рассылка завершена!\nОтправлено: {sent}")
                        
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
                                f"<tg-emoji emoji-id=\"6039486778597970865\">🔔</tg-emoji> <b>Чек от {user_id}</b>\n"
                                f"<tg-emoji emoji-id=\"6041730074376410123\">📦</tg-emoji> Товар: {CHEAT_NAMES.get(product, 'Unknown')}\n"
                                f"<tg-emoji emoji-id=\"5891211339170326418\">⏳</tg-emoji> Тариф: {days} дней",
                                adm_kb
                            )
                            send_message(chat_id, f"<tg-emoji emoji-id=\"5938252440926163756\">✅</tg-emoji> Чек отправлен администратору!")
                        
                        # Отмена
                        elif text == "/cancel":
                            if waiting.get(f"{user_id}_waiting"):
                                waiting[f"{user_id}_waiting"] = None
                                send_message(chat_id, "✅ Операция отменена")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
