import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = '-1002675757828'  # Solo el grupo, sin topic

def send_to_telegram(msg):
    payload = {
        'chat_id': CHAT_ID,
        'text': msg,
        'parse_mode': 'HTML'
    }
    response = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

send_to_telegram("📢 Test directo al grupo (sin topic)")
