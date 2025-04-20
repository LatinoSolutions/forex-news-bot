#!/usr/bin/env python3
import os
import requests
import datetime
import pytz
from telegram import Bot

# === CONFIG ===
BOT_TOKEN  = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ ERROR: la variable de entorno BOT_TOKEN no está configurada")
CHAT_ID    = os.getenv("CHAT_ID", "-1002675757828")
THREAD_ID  = int(os.getenv("THREAD_ID", "10"))

# URL del feed JSON de ForexFactory (esta semana)
JSON_URL   = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# Zona horaria de tus horarios (e.g. Europe/Berlin)
TZ         = pytz.timezone("Europe/Berlin")

bot = Bot(token=BOT_TOKEN)


def fetch_events():
    """Descarga y parsea el JSON de eventos."""
    resp = requests.get(JSON_URL)
    resp.raise_for_status()
    return resp.json()  # devuelve lista de dicts


def filter_by_date(events, target_date, currencies, impact_levels):
    """Filtra eventos por fecha, divisa e impacto."""
    out = []
    for e in events:
        # e["Date"] viene en formato "YYYY-MM-DD"
        try:
            date = datetime.datetime.strptime(e["Date"], "%Y-%m-%d").date()
        except Exception:
            continue
        if date != target_date:
            continue
        if e.get("Currency") not in currencies:
            continue
        if int(e.get("ImpactLevel", 0)) not in impact_levels:
            continue
        out.append(e)
    return out


def format_messages(events):
    """Convierte cada evento en un texto de Telegram."""
    msgs = []
    for e in events:
        t    = e.get("Time", "?")
        ev   = e.get("Event", "?")
        prev = e.get("Previous", "?")
        fc   = e.get("Forecast", "?")
        msgs.append(
            f"🕒 *{t}* | _{ev}_\nForecast: {fc} | Previous: {prev}"
        )
    return msgs


def send_messages(msgs):
    """Envía cada mensaje al canal/topic de Telegram."""
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
    wd    = today.weekday()  # lun=0 … dom=6

    events = fetch_events()

    # ⚠️ 5 min antes de cada evento
    if now.minute % 5 == 0 and now.hour*60+now.minute not in (4,15):
        in_5min = []
        for e in events:
            date = e.get("Date")
            time = e.get("Time")
            if not date or not time:
                continue
            dt_str = f"{date} {time}"
            try:
                dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M%p")
                dt = TZ.localize(dt)
            except Exception:
                continue
            delta = (dt - now).total_seconds() / 60
            if 4.5 < delta <= 5.5 and \
               e.get("Currency") in ["USD","EUR"] and \
               int(e.get("ImpactLevel",0)) >= 2:
                in_5min.append(e)
        if in_5min:
            send_messages(format_messages(in_5min))
        return

    # 🗓 Boletín diario a las 06:00
    if now.hour == 6 and now.minute == 0:
        today_events = filter_by_date(events, today, ["USD","EUR"], [2,3])
        if today_events:
            send_messages(format_messages(today_events))
        return

    # 📋 Resumen semana pasada: sábados 17:00
    if wd == 5 and now.hour == 17 and now.minute == 0:
        start = today - datetime.timedelta(days=7)
        msgs = []
        for i in range(7):
            d   = start + datetime.timedelta(days=i)
            evs = filter_by_date(events, d, ["USD","EUR"], [2,3])
            for e in evs:
                e["Date"] = d.strftime("%a %d")
                msgs.append(e)
        if msgs:
            send_messages(format_messages(msgs))
        return

    # 🔮 Resumen semana entrante: domingos 17:00
    if wd == 6 and now.hour == 17 and now.minute == 0:
        msgs = []
        for i in range(1,8):
            d   = today + datetime.timedelta(days=i)
            evs = filter_by_date(events, d, ["USD","EUR"], [2,3])
            for e in evs:
                e["Date"] = d.strftime("%a %d")
                msgs.append(e)
        if msgs:
            send_messages(format_messages(msgs))
        return


if __name__ == "__main__":
    main()
