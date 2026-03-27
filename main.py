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

# --- ФУНКЦИЯ ДЛЯ TG PREMIUM ЭМОДЗИ (как в файловом боте) ---
def em(emoji_id: str, char: str = "●") -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'

# --- КНОПКИ ---
def btn(text: str, callback: str, emoji_id: str = None):
    button = {"text": text, "callback_data": callback}
    if emoji_id:
        button["icon_custom_emoji_id"] = emoji_id
    return button

def url_btn(text: str, url: str, emoji_id: str = None):
    button = {"text": text, "url": url}
    if emoji_id:
        button["icon_custom_emoji_id"] = emoji_id
    return button

def back_btn(target: str):
    return {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": target}]]}

# --- ID ЭМОДЗИ ---
EMOJI = {
    "fire": "5339472242529045815",
    "status": "5208846279714560254",
    "welcome": "5208657859499282838",
    "buy": "5156877291397055163",
    "profile": "5904630315946611415",
    "id": "6032693626394382504",
    "name": "5879770735999717115",
    "username": "5814247475141153332",
    "product": "6041730074376410123",
    "time": "5891211339170326418",
    "reviews": "5938252440926163756",
    "channel": "6028171274939797252",
    "support": "5208539876747662991",
    "games": "5938413566624272793",
    "standoff": "5393134637667094112",
    "pubg": "6073605466221451561",
    "plutonium": "5339472242529045815",
    "days": "5393330385096575682",
    "bank": "5393576224729633040",
    "crypto": "5390816416184174666",
    "card": "5890848474563352982",
    "comment": "5891105528356018797",
    "screenshot": "5769126056262898415",
    "receipt": "5258205968025525531",
    "cancel": "5208480322731137426",
    "check": "6039486778597970865",
    "approve": "5208657859499282838",
    "reject": "5208480322731137426",
    "success": "5938252440926163756",
    "file": "6037373985400819577",
    "key": "6048733173171359488",
    "done": "5208422125924275090",
    "order": "5208474816583063829",
    "thank": "5413879192267805083",
    "heart": "6039348811363520645",
    "zolo": "5451653043089070124",
    "impact": "5276079251089547977",
    "king": "6172520285330214110",
    "inferno": "5296273418516187626",
    "zolo_cis": "5451841459009379088"
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

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('users.db', timeout=30, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
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

# --- ХРАНИЛИЩА ---
waiting = {}
processed = set()

# --- ОСНОВНЫЕ КНОПКИ ---
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [btn("Купить ключ", "buy_key", EMOJI['buy']),
             btn("Мой профиль", "profile", EMOJI['profile'])],
            [btn("Наши отзывы", "show_reviews", EMOJI['reviews']),
             btn("Статус ПО", "check_status", EMOJI['status'])],
            [url_btn("Plutonium Store", WEBAPP_URL, EMOJI['plutonium'])],
            [url_btn("Техподдержка", "https://t.me/IllyaGarant", EMOJI['support'])]
        ]
    }

# ---------- СТАРТ ----------
def handle_start(chat_id, user_id):
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Вы заблокированы")
        return
    
    cursor.execute('INSERT OR IGNORE INTO users (user_id, subscribed_at) VALUES (?, ?)', 
                  (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    status = cursor.execute('SELECT value FROM settings WHERE key="cheat_status"').fetchone()['value']
    
    text = (f"{em(EMOJI['fire'], '🔥')} <b>Plutonium Store</b>\n\n"
            f"{em(EMOJI['status'], '📈')} Статус ПО: {status}\n\n"
            f"{em(EMOJI['welcome'], '👋')} Добро пожаловать!")
    
    send_photo(chat_id, "https://files.catbox.moe/916cwt.png", text, get_main_keyboard())

# ---------- ПРОФИЛЬ ----------
def handle_profile(chat_id, user_id, message_id):
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Вы заблокированы")
        return
    
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
    
    text = (f"{em(EMOJI['profile'], '👤')} <b>Личный кабинет</b>\n\n"
            f"{em(EMOJI['id'], '🆔')} <b>ID:</b> <code>{user_id}</code>\n"
            f"{em(EMOJI['name'], '📛')} <b>Имя:</b> {user_id}\n"
            f"{em(EMOJI['username'], '🔖')} <b>Username:</b> @{user_id}\n"
            f"{em(EMOJI['product'], '📦')} <b>Товар:</b> {product}\n"
            f"{em(EMOJI['time'], '⏳')} <b>Осталось:</b> {time_left}")
    
    if last_key:
        text += f"\n{em(EMOJI['key'], '🔑')} <b>Ваш ключ:</b> <code>{last_key}</code>"
    
    edit_message_caption(chat_id, message_id, text, back_btn("start"))

# ---------- СТАТУС ----------
def handle_status(chat_id, message_id):
    status = cursor.execute('SELECT value FROM settings WHERE key="cheat_status"').fetchone()['value']
    text = f"{em(EMOJI['status'], '📊')} <b>Статус ПО:</b> {status}"
    edit_message_caption(chat_id, message_id, text, back_btn("start"))

# ---------- ОТЗЫВЫ ----------
def handle_reviews(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [url_btn("Канал с отзывами", "https://t.me/plutoniumrewiews", EMOJI['channel'])],
            [{"text": "⬅️ Назад", "callback_data": "start"}]
        ]
    }
    text = f"{em(EMOJI['reviews'], '⭐')} <b>Наши отзывы</b>"
    edit_message_caption(chat_id, message_id, text, kb)

# ---------- МЕНЮ ПОКУПКИ ----------
def handle_buy_key(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [btn("Standoff 2", "game_so2", EMOJI['standoff'])],
            [btn("PUBG Mobile", "game_pubg", EMOJI['pubg'])],
            [{"text": "⬅️ Назад", "callback_data": "start"}]
        ]
    }
    text = f"{em(EMOJI['games'], '🎮')} <b>Выберите игру:</b>"
    edit_message_caption(chat_id, message_id, text, kb)

# ---------- STANDOFF 2 ----------
def handle_so2_menu(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [btn("Plutonium", "cheat_so2", EMOJI['plutonium'])],
            [{"text": "⬅️ Назад", "callback_data": "buy_key"}]
        ]
    }
    text = (f"{em(EMOJI['standoff'], '⚙️')} <b>Standoff 2</b>\n"
            f"{em(EMOJI['games'], '🎮')} Выберите чит:")
    edit_message_caption(chat_id, message_id, text, kb)

# ---------- PUBG ----------
def handle_pubg_menu(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [btn("Zolo", "cheat_zolo", EMOJI['zolo'])],
            [btn("Impact VIP", "cheat_impact", EMOJI['impact'])],
            [btn("King Mod", "cheat_king", EMOJI['king'])],
            [btn("Inferno", "cheat_inferno", EMOJI['inferno'])],
            [btn("Zolo CIS", "cheat_zolo_cis", EMOJI['zolo_cis'])],
            [{"text": "⬅️ Назад", "callback_data": "buy_key"}]
        ]
    }
    text = f"{em(EMOJI['pubg'], '🎯')} <b>PUBG Mobile</b>\nВыберите чит:"
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
        buttons.append([btn(days_text, f"period_{cheat}_{days}", EMOJI['days'])])
    
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
            [btn("Укр Банк", f"bank_{cheat}_{days}", EMOJI['bank'])],
            [btn("CryptoBot", f"crypto_{cheat}_{days}", EMOJI['crypto'])],
            [{"text": "⬅️ Назад", "callback_data": f"cheat_{cheat}"}]
        ]
    }
    edit_message_caption(chat_id, message_id, desc, kb)

# ---------- ОПЛАТА БАНКОМ ----------
def handle_bank_payment(chat_id, message_id, cheat, days):
    waiting[f"{chat_id}_product"] = cheat
    waiting[f"{chat_id}_days"] = days
    
    price = PRICES[cheat][days][0] if cheat == "so2" else PRICES[cheat][days]
    
    text = (f"{em(EMOJI['card'], '💳')} <b>Оплата банковской картой</b>\n\n"
            f"{em(EMOJI['card'], '💰')} <b>Сумма:</b> {price}\n"
            f"{em(EMOJI['card'], '💳')} <b>Карта:</b> <code>{CARD}</code>\n"
            f"{em(EMOJI['comment'], '❗')} <b>Комментарий:</b> За цифрові товари\n\n"
            f"{em(EMOJI['screenshot'], '📸')} После оплаты нажмите кнопку ниже и пришлите скриншот")
    
    kb = {
        "inline_keyboard": [
            [btn("Я оплатил", "send_receipt", EMOJI['receipt'])],
            [btn("Отмена", "start", EMOJI['cancel'])]
        ]
    }
    edit_message_caption(chat_id, message_id, text, kb)

# ---------- ОТПРАВКА ЧЕКА ----------
def handle_send_receipt(chat_id, message_id, user_id):
    waiting[f"{user_id}_waiting"] = "receipt"
    send_message(chat_id, f"{em(EMOJI['screenshot'], '📸')} <b>Отправьте скриншот чека</b> (одним фото)")

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
                        chat_id = cb['message']['chat']['id']
                        message_id = cb['message']['message_id']
                        data = cb['data']
                        
                        if data == "start":
                            handle_start(chat_id, user_id)
                        
                        elif data == "profile":
                            handle_profile(chat_id, user_id, message_id)
                        
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
                        
                        elif data == "send_receipt":
                            handle_send_receipt(chat_id, message_id, user_id)
                        
                        answer_callback(cb_id)
                    
                    # Сообщение
                    elif 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        user_id = msg['from']['id']
                        text = msg.get('text', '')
                        
                        # /start
                        if text == "/start":
                            handle_start(chat_id, user_id)
                        
                        # Обработка чека
                        elif waiting.get(f"{user_id}_waiting") == "receipt" and 'photo' in msg:
                            waiting[f"{user_id}_waiting"] = None
                            
                            adm_kb = {
                                "inline_keyboard": [
                                    [btn("Одобрить", f"adm_ok_{user_id}", EMOJI['approve'])],
                                    [btn("Отклонить", f"adm_no_{user_id}", EMOJI['reject'])]
                                ]
                            }
                            product = waiting.get(f"{user_id}_product", "Unknown")
                            days = waiting.get(f"{user_id}_days", "0")
                            
                            send_photo(
                                ADMIN_ID,
                                msg['photo'][-1]['file_id'],
                                f"{em(EMOJI['check'], '🔔')} <b>Чек от {user_id}</b>\n"
                                f"{em(EMOJI['product'], '📦')} Товар: {CHEAT_NAMES.get(product, 'Unknown')}\n"
                                f"{em(EMOJI['order'], '📅')} Тариф: {days} дней",
                                adm_kb
                            )
                            send_message(chat_id, f"{em(EMOJI['success'], '✅')} Чек отправлен администратору! Ожидайте подтверждения.")
                        
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
        
        send_message(chat_id, f"{em(EMOJI['file'], '📎')} <b>Отправьте файл с читом</b> (или текст с инструкцией)")
        waiting[f"admin_{target_id}_waiting"] = "file"
        answer_callback(data, "✅ Одобрено")
    else:
        target_id = int(parts[2])
        send_message(target_id, f"{em(EMOJI['reject'], '❌')} Ваша оплата была отклонена администратором.")
        send_message(chat_id, f"{em(EMOJI['reject'], '❌')} Отклонено")
        answer_callback(data)

# ---------- ФАЙЛ ОТ АДМИНА ----------
def handle_admin_file(chat_id, user_id, msg):
    target_id = int(waiting.get(f"admin_target", 0))
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
    send_message(chat_id, f"{em(EMOJI['key'], '🔑')} <b>Введите ключ активации</b>")

# ---------- КЛЮЧ ОТ АДМИНА ----------
def handle_admin_key(chat_id, user_id, key):
    target_id = int(waiting.get(f"admin_target", 0))
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
    
    text = (f"{em(EMOJI['success'], '✅')} <b>Заказ активирован!</b>\n\n"
            f"{em(EMOJI['order'], '📅')} <b>Действует до:</b> {expiry_date}\n"
            f"{em(EMOJI['key'], '🔑')} <b>Ключ:</b> <code>{key}</code>\n\n"
            f"{em(EMOJI['thank'], '💜')} Благодарим за покупку в Plutonium Store!")
    
    try:
        if file_id:
            send_document(target_id, file_id, text)
        elif file_text:
            send_message(target_id, text + f"\n\n{em(EMOJI['heart'], '📝')} {file_text}")
        else:
            send_message(target_id, text)
        
        send_message(chat_id, f"{em(EMOJI['done'], '✅')} Готово! Товар выдан пользователю.")
    except Exception as e:
        send_message(chat_id, f"❌ Ошибка при отправке: {e}")
    
    # Очищаем
    waiting.pop(f"admin_{target_id}_product", None)
    waiting.pop(f"admin_{target_id}_days", None)
    waiting.pop(f"admin_{target_id}_file", None)
    waiting.pop(f"admin_{target_id}_file_text", None)
    waiting.pop(f"admin_{target_id}_waiting", None)
    waiting.pop(f"admin_target", None)

# ---------- АДМИН-КОМАНДЫ ----------
def handle_set_status(chat_id, text):
    new_status = text.replace("/set_status ", "").strip()
    cursor.execute('UPDATE settings SET value = ? WHERE key = "cheat_status"', (new_status,))
    conn.commit()
    send_message(chat_id, f"{em(EMOJI['success'], '✅')} Статус обновлен на: {new_status}")

def handle_broadcast(chat_id, user_id):
    waiting[f"{user_id}_broadcast"] = "waiting"
    send_message(chat_id, f"{em(EMOJI['status'], '📢')} <b>Отправь сообщение для рассылки</b> (текст, фото, видео или документ)")

def send_broadcast(msg, user_id):
    users = cursor.execute('SELECT user_id FROM users WHERE banned = 0').fetchall()
    if not users:
        send_message(user_id, "📭 Нет пользователей в базе")
        return
    
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
    
    send_message(user_id, f"{em(EMOJI['success'], '✅')} Рассылка завершена!\n{em(EMOJI['success'], '✅')} Успешно: {sent}")

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
    
    send_message(chat_id, f"{em(EMOJI['success'], '✅')} Пользователь {target_id} заблокирован")

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
    
    send_message(chat_id, f"{em(EMOJI['success'], '✅')} Пользователь {target_id} разблокирован")

def handle_users(chat_id):
    total = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    banned = cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1').fetchone()[0]
    active = cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0]
    
    send_message(
        chat_id,
        f"{em(EMOJI['profile'], '👥')} <b>Статистика пользователей:</b>\n\n"
        f"{em(EMOJI['status'], '📊')} Всего: {total}\n"
        f"{em(EMOJI['success'], '✅')} Активных: {active}\n"
        f"{em(EMOJI['cancel'], '⛔')} Забанено: {banned}"
    )

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    main()
