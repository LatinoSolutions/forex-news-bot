import os
import time
import datetime
import requests
import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# === CONFIGURACIÓN ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = '-1002675757828'  # tu grupo/canal
THREAD_ID = 10  # ID del topic "Forex-News"

BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
CHROMEDRIVER_PATH = "/Users/bru/Desktop/MediTrading/chromedriver"

# === CONFIGURAR TELEGRAM BOT ===
bot = telebot.TeleBot(BOT_TOKEN)

# === CONFIGURAR NAVEGADOR HEADLESS ===
def get_driver():
    options = Options()
    options.binary_location = BRAVE_PATH
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

# === EXTRAER NOTICIAS DE FOREX FACTORY ===
def scrape_usd_news(week="this"):
    url = "https://www.forexfactory.com/calendar?week=" + week
    driver = get_driver()
    driver.get(url)
    time.sleep(5)

    usd_news = []
    rows = driver.find_elements(By.CSS_SELECTOR, "tr.calendar__row")
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

# === ENVIAR MENSAJES A TELEGRAM ===
def send_news(news_list, title):
    if not news_list:
        text = "❌ No se encontraron noticias USD de alto impacto."
    else:
        text = f"📊 <b>{title}</b>\n\n" + "\n".join(news_list)
    
    payload = {
        'chat_id': CHAT_ID,
        'message_thread_id': THREAD_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=payload)

# === COMANDOS DE TELEGRAM ===
@bot.message_handler(commands=['this_week'])
def handle_this_week(message):
    news = scrape_usd_news("this")
    send_news(news, "USD News - This Week")

@bot.message_handler(commands=['previous_week'])
def handle_previous_week(message):
    news = scrape_usd_news("previous")
    send_news(news, "USD News - Previous Week")

# === INICIAR BOT ===
print("✅ Bot is running...")
bot.polling()
