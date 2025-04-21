import os
import requests
import datetime
import pytz
from telegram import Bot

# ==== CONFIGURACIÓN ====
BOT_TOKEN   = os.getenv("BOT_TOKEN")           # Se define en GitHub Secrets
CHAT_ID     = os.getenv("CHAT_ID")             # Se define en GitHub Secrets
THREAD_ID   = int(os.getenv("THREAD_ID", "0")) # Se define en GitHub Secrets
JSON_URL    = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
TZ          = pytz.timezone("Europe/Berlin")

bot = Bot(token=BOT_TOKEN)

def fetch_events():
    r = requests.get(JSON_URL)
    r.raise_for_status()
    return r.json()  # lista de dicts

def filter_by_date(events, date, currencies, levels):
    out = []
    for e in events:
        e_date = datetime.datetime.strptime(e["Date"], "%Y-%m-%d").date()
        if e_date != date: 
            continue
        if e["Currency"] not in currencies: 
            continue
        if int(e["ImpactLevel"]) not in levels: 
            continue
        out.append(e)
    return out

def format_messages(events):
    msgs = []
    for e in events:
        t   = e["Time"]       # ej. "08:30am"
        ev  = e["Event"]
        prev= e["Previous"]
        fc  = e["Forecast"]
        msgs.append(f"🕒 *{t}* | _{ev}_\nForecast: {fc} | Previous: {prev}")
    return msgs

def send_messages(msgs):
    for m in msgs:
        bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=THREAD_ID,
            text=m,
            parse_mode="Markdown"
        )

def main():
    now   = datetime.datetime.now(TZ)
    today = now.date()
    wd    = today.weekday()  # lunes=0, domingo=6
    events= fetch_events()

    # 1) ▶️ 5 min antes de cada evento
    if now.minute % 5 == 0 and not (wd in [5,6] and now.hour==17):
        in_5 = []
        for e in events:
            # combinamos Date+Time en datetime
            dt = datetime.datetime.strptime(f"{e['Date']} {e['Time']}", "%Y-%m-%d %I:%M%p")
            dt = TZ.localize(dt)
            delta = (dt - now).total_seconds()/60
            if 4.5 < delta <= 5.5 and e["Currency"] in ["USD","EUR"] and int(e["ImpactLevel"])>=2:
                in_5.append(e)
        if in_5:
            send_messages(format_messages(in_5))
            return

    # 2) ▶️ Reporte diario a las 06:00
    if now.hour==6 and now.minute==0:
        today_ev = filter_by_date(events, today, ["USD","EUR"], [2,3])
        if today_ev:
            send_messages(format_messages(today_ev))
        return

    # 3) ▶️ Resumen semana pasada: sábados a las 17:00
    if wd==5 and now.hour==17 and now.minute==0:
        msgs = []
        start = today - datetime.timedelta(days=7)
        for i in range(7):
            d = start + datetime.timedelta(days=i)
            evs = filter_by_date(events, d, ["USD","EUR"], [2,3])
            for e in evs:
                e["Date"] = d.strftime("%a %d")
                msgs.append(e)
        if msgs:
            send_messages(format_messages(msgs))
        return

    # 4) ▶️ Resumen semana entrante: domingos a las 17:00
    if wd==6 and now.hour==17 and now.minute==0:
        msgs = []
        for i in range(1,8):
            d = today + datetime.timedelta(days=i)
            evs = filter_by_date(events, d, ["USD","EUR"], [2,3])
            for e in evs:
                e["Date"] = d.strftime("%a %d")
                msgs.append(e)
        if msgs:
            send_messages(format_messages(msgs))
        return

    print("⚪️ No hay notificaciones que enviar ahora.")

if __name__ == "__main__":
    main()
