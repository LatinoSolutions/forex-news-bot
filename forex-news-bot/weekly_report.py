import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz

# === CONFIGURA TU BOT ===
BOT_TOKEN = 'TU_TOKEN_DE_TELEGRAM'
CHAT_ID = '-1002675757828'
THREAD_ID = 10  # ID del topic "Forex-News"

# === CONFIGURA FECHAS ===
tz = pytz.timezone("Etc/GMT+3")
today = datetime.now(tz)
start_date = today
end_date = today + timedelta(days=7)

# === URL de Forex Factory para la semana ===
url = 'https://www.forexfactory.com/calendar?week=this'

headers = {
    'User-Agent': 'Mozilla/5.0'
}

# === Scraping ===
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
rows = soup.find_all('tr', class_='calendar__row')

events_by_day = {}

for row in rows:
    try:
        impact = row.find('td', class_='impact')
        if not impact or 'high' not in impact.get('class', []):
            continue

        currency = row.find('td', class_='currency').text.strip()
        if currency not in ['USD', 'EUR']:
            continue

        date_cell = row.find('td', class_='date')
        time_cell = row.find('td', class_='time')
        event_cell = row.find('td', class_='event')
        forecast_cell = row.find('td', class_='forecast')
        previous_cell = row.find('td', class_='previous')

        date_text = date_cell.text.strip() if date_cell else ''
        time_text = time_cell.text.strip() if time_cell else 'All Day'
        event = event_cell.text.strip()
        forecast = forecast_cell.text.strip() or '—'
        previous = previous_cell.text.strip() or '—'

        # Guarda por día
        if date_text not in events_by_day:
            events_by_day[date_text] = []

        events_by_day[date_text].append(
            f"🕒 {time_text} | 💱 {currency} | 📢 {event}\n📊 Forecast: {forecast} | 📉 Previous: {previous}"
        )

    except Exception as e:
        continue

# === Armar el mensaje final ===
if events_by_day:
    message = "📆 <b>Boletín Semanal - Noticias EUR/USD (Impacto Alto)</b>\n\n"
    for date, events in events_by_day.items():
        message += f"<b>📅 {date}</b>\n"
        for event in events:
            message += f"{event}\n\n"
    else:
        message += "\n🎯 Prepárate para la semana, trader."

else:
    message = "❌ No se encontraron noticias relevantes para la semana."

# === Enviar por Telegram ===
def send_to_telegram(text):
    payload = {
        'chat_id': CHAT_ID,
        'message_thread_id': THREAD_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=payload)

send_to_telegram(message)
