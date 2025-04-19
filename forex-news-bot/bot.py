import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# === CONFIGURACIÓN DEL BOT ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = "-1002675757828"  # ID del grupo

# === CONFIGURACIÓN DE CHROMEDRIVER Y OPCIONES ===
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service()  # Usará el chromedriver del sistema (GitHub Actions ya lo tiene)
driver = webdriver.Chrome(service=service, options=options)

# === NAVEGAR A FOREX FACTORY ===
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

# === ENVIAR A TELEGRAM (sin topic) ===
def send_to_telegram(messages):
    for msg in messages:
        payload = {
            'chat_id': CHAT_ID,
            'text': msg,
            'parse_mode': 'HTML'
        }
        response = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=payload)
        print(response.text)  # Debug: ver respuesta

# === EJECUTAR ===
if usd_news:
    print(f"✅ Se encontraron {len(usd_news)} noticias USD de alto impacto.")
    send_to_telegram(usd_news)
else:
    print("❌ No se encontraron noticias USD de alto impacto.")
    send_to_telegram(["❌ No se encontraron noticias USD de alto impacto."])
