from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import os

# === CONFIGURACIÓN DEL BOT ===

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Lee el token desde las variables de entorno (GitHub Secrets)
CHAT_ID = -1002675757828  # sin comillas, como número
THREAD_ID = 10  # ID del topic "Forex-News"

# === OPCIONES PARA CHROME HEADLESS ===
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# === INICIAR CHROME DRIVER ===
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# === ABRIR FOREX FACTORY ===
driver.get("https://www.forexfactory.com/calendar")
time.sleep(5)

# === EXTRAER NOTICIAS USD DE ALTO IMPACTO ===
rows = driver.find_elements(By.CSS_SELECTOR, "tr.calendar__row")
usd_news = []

for row in rows:
    try:
        impact_icon = row.find_element(By.CSS_SELECTOR, "td.impact span.icon")
        impact_color = impact_icon.get_attribute("style")
        currency = row.find_element(By.CSS_SELECTOR, "td.currency").text.strip()
        event = row.find_element(By.CSS_SELECTOR, "td.event").text.strip()
        time_str = row.find_element(By.CSS_SELECTOR, "td.time").text.strip()

        if "red" in impact_color and currency == "USD":
            usd_news.append(f"🕒 {time_str} | 📢 {event}")
    except:
        continue

driver.quit()

# === ENVIAR A TELEGRAM ===
def send_to_telegram(messages):
    for msg in messages:
        payload = {
            'chat_id': CHAT_ID,
            'message_thread_id': THREAD_ID,
            'text': msg,
            'parse_mode': 'HTML'
        }
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=payload)

# === EJECUTAR ===
if usd_news:
    print(f"✅ Se encontraron {len(usd_news)} noticias USD de alto impacto.")
    send_to_telegram(usd_news)
else:
    print("❌ No se encontraron noticias USD de alto impacto.")
