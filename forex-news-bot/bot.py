from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import os, time

# === BOT TOKEN ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# === CONFIGURACIÓN DEL CHROME HEADLESS ===
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver_path = "/usr/bin/chromedriver"  # Asegúrate que este es el path correcto en tu servidor

def extract_news():
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://www.forexfactory.com/calendar")
    time.sleep(5)  # Esperar carga

    rows = driver.find_elements(By.CSS_SELECTOR, "tr.calendar__row")
    news = []

    for row in rows:
        try:
            impact_icon = row.find_element(By.CSS_SELECTOR, "td.impact span.icon")
            impact_color = impact_icon.get_attribute("style")
            currency = row.find_element(By.CSS_SELECTOR, "td.currency").text.strip()
            event = row.find_element(By.CSS_SELECTOR, "td.event").text.strip()
            date_str = row.find_element(By.CSS_SELECTOR, "td.date").text.strip()
            time_str = row.find_element(By.CSS_SELECTOR, "td.time").text.strip()
            
            if "red" in impact_color and currency == "USD":
                news.append(f"🗓 {date_str} - 🕒 {time_str} | 📢 {event}")
        except:
            continue

    driver.quit()
    return news

async def this_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_news = extract_news()
    this_week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
    filtered = [n for n in all_news if str(this_week_start.day) in n]

    if filtered:
        await update.message.reply_text("\n".join(filtered))
    else:
        await update.message.reply_text("📊 No se encontraron noticias de esta semana.")

async def previous_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_news = extract_news()
    last_week_start = datetime.now().date() - timedelta(days=datetime.now().weekday() + 7)
    filtered = [n for n in all_news if str(last_week_start.day) in n]

    if filtered:
        await update.message.reply_text("\n".join(filtered))
    else:
        await update.message.reply_text("🕰️ No se encontraron noticias de la semana pasada.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("this_week", this_week))
    app.add_handler(CommandHandler("previous_week", previous_week))

    print("🤖 Bot está corriendo...")
    app.run_polling()
