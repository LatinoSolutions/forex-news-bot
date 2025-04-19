import os
import time
import requests
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from flask import Flask, request

# === CONFIGURACIÓN TELEGRAM ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = '-1002675757828'
THREAD_ID = 10

# === CONFIGURACIÓN SELENIUM ===
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
CHROME_BINARY_PATH = "/usr/bin/google-chrome"

options = Options()
options.binary_location = CHROME_BINARY_PATH
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


def get_usd_news(from_date=None, to_date=None):
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    url = "https://www.forexfactory.com/calendar"
    driver.get(url)
    time.sleep(5)

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
    return usd_news


def send_to_telegram(messages):
    for msg in messages:
        payload = {
            'chat_id': CHAT_ID,
            'message_thread_id': THREAD_ID,
            'text': msg,
            'parse_mode': 'HTML'
        }
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=payload)


@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def telegram_webhook():
    data = request.get_json()

    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if text == "/this_week":
            news = get_usd_news()
            if news:
                send_to_telegram(["🗓 <b>Noticias USD - Esta semana</b>"] + news)
            else:
                send_to_telegram(["❌ No se encontraron noticias de alto impacto esta semana."])

        elif text == "/previous_week":
            # Placeholder para historial futuro
            send_to_telegram(["📦 Historial de la semana pasada aún no implementado."])

    return {"ok": True}


if __name__ == "__main__":
    if os.environ.get("RUN_MODE") == "manual":
        news = get_usd_news()
        if news:
            print(f"✅ Se encontraron {len(news)} noticias USD de alto impacto.")
            send_to_telegram(["🗓 <b>Noticias USD - Resumen diario</b>"] + news)
        else:
            print("❌ No se encontraron noticias USD de alto impacto.")
    else:
        app.run(host="0.0.0.0", port=8000)
