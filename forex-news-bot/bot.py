import os
import time
import datetime
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from telebot import TeleBot

# === CONFIGURACIÓN DE TELEGRAM ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = '-1002675757828'  # Puedes usar tu grupo/canal aquí
bot = TeleBot(BOT_TOKEN)

# === CONFIGURACIÓN DE BRAVE ===
BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
CHROMEDRIVER_PATH = "/Users/bru/Desktop/MediTrading/chromedriver"

options = Options()
options.binary_location = BRAVE_PATH
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# === FUNCIONES DE FECHAS ===
def get_this_week_range():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())  # lunes
    end = today
    return start, end

def get_previous_week_range():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday() + 7)  # lunes anterior
    end = start + datetime.timedelta(days=6)  # domingo anterior
    return start, end

# === FUNCIONES DE SCRAPING ===
def scrape_usd_news(start_date, end_date):
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    url = "https://www.forexfactory.com/calendar"
    driver.get(url)
    time.sleep(6)

    rows = driver.find_elements(By.CSS_SELECTOR, "tr.calendar__row")
    usd_news = []

    for row in rows:
        try:
            impact_icon = row.find_element(By.CSS_SELECTOR, "td.impact span.icon")
            impact_color = impact_icon.get_attribute("style")
            currency = row.find_element(By.CSS_SELECTOR, "td.currency").text.strip()
            event = row.find_element(By.CSS_SELECTOR, "td.event").text.strip()
            time_str = row.find_element(By.CSS_SELECTOR, "td.time").text.strip()
            date_str = row.find_element(By.CSS_SELECTOR, "td.date").text.strip()

            if date_str:
                current_date = datetime.datetime.strptime(date_str, "%b %d").replace(year=datetime.date.today().year).date()
            else:
                current_date = current_date  # keep previous value if empty

            if start_date <= current_date <= end_date and "red" in impact_color and currency == "USD":
                usd_news.append(f"🗓️ {current_date} 🕒 {time_str} | 📢 {event}")
        except:
            continue

    driver.quit()
    return usd_news

# === MANEJO DE COMANDOS ===
@bot.message_handler(commands=['this_week', 'previous_week'])
def handle_command(message):
    if message.text == '/this_week':
        start, end = get_this_week_range()
        title = "📅 Noticias USD - Esta semana"
    else:
        start, end = get_previous_week_range()
        title = "⏪ Noticias USD - Semana pasada"

    news = scrape_usd_news(start, end)

    if news:
        bot.send_message(message.chat.id, f"{title}\n\n" + "\n".join(news))
    else:
        bot.send_message(message.chat.id, f"{title}\n\n❌ No se encontraron noticias de alto impacto.")

# === EJECUTAR EL BOT ===
bot.polling()
