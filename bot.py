from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import requests

# === CONFIGURACIÓN DEL BOT ===
BOT_TOKEN = '7820146097:AAGIH6RmpUwGUUZV2ICf3dp0T96_jp32f9E'
CHAT_ID = '-1002675757828'
THREAD_ID = 10  # ID del topic "Forex-News"

# === CONFIGURACIÓN DE BRAVE ===
BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
CHROMEDRIVER_PATH = "/Users/bru/Desktop/MediTrading/chromedriver"

# === OPCIONES PARA BRAVE ===
options = Options()
options.binary_location = BRAVE_PATH
options.add_argument("--headless")  # Puedes comentar esta línea para ver Brave abrirse
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# === INICIAR DRIVER ===
service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# === ABRIR FOREX FACTORY ===
driver.get("https://www.forexfactory.com/calendar")
time.sleep(5)  # Esperar que cargue JavaScript

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
