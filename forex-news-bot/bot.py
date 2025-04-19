import requests
import os

# === CONFIGURACIÓN DEL BOT ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Usamos variable de entorno (correcto para GitHub Actions)
CHAT_ID = '-1002675757828'  # ID de tu supergrupo con foro
THREAD_ID = 10  # ID del topic "Forex-News"

# === FUNCIÓN PARA ENVIAR A TELEGRAM ===
def send_to_telegram(messages):
    for msg in messages:
        payload = {
            'chat_id': CHAT_ID,
            'message_thread_id': THREAD_ID,
            'text': msg,
            'parse_mode': 'HTML'
        }
        response = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

# === EJECUTAR TEST ===
send_to_telegram(["🚨 Test de conexión exitosa con el topic 'Forex-News' 🚀"])
