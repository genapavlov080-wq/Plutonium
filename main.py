import urllib.request
import json
import time
import sqlite3
import requests
from datetime import datetime, timedelta

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CARD = "4441111008011946"
WEBAPP_URL = "https://rocket-online.vercel.app"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- ЖЕСТКИЙ СБРОС ---
print("🔄 Сброс...")
try:
    urllib.request.urlopen(f"{API_URL}/deleteWebhook?drop_pending_updates=true", timeout=5)
    urllib.request.urlopen(f"{API_URL}/getUpdates?offset=-1", timeout=5)
    time.sleep(2)
    print("✅ Сброс выполнен")
except Exception as e:
    print(f"Сброс: {e}")

# --- ФУНКЦИЯ ДЛЯ ЭМОДЗИ ---
def em(emoji_id, char):
    return f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'

# --- ТЕСТ ---
def send_test():
    text = f"{em('5339472242529045815', '🔥')} <b>Тест Premium эмодзи</b>"
    
    data = {
        "chat_id": ADMIN_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    url = f"{API_URL}/sendMessage"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            print(result)
            if result.get('ok'):
                print("✅ Сообщение отправлено!")
            else:
                print(f"❌ Ошибка: {result}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    send_test()
