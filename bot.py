#!/usr/bin/env python3
# -*- coding: utf‑8 -*-
"""
Bot de noticias económicas para Telegram.
– 06:00 Berlín: reporte diario
– 5 min antes de cada evento USD/EUR impacto medio/alto
– Sáb 17:00: resumen semana terminada
– Dom 17:00: vista previa semana entrante
Modo TEST: si la variable de entorno FORCE_TEST == "1" envía un ping y sale.
"""

import os, sys, time, json, logging, datetime as dt
from typing import List, Dict

import pytz, requests
from telegram import Bot

# ======== CONFIG ========
BOT_TOKEN   = os.getenv("BOT_TOKEN")
CHAT_ID     = os.getenv("CHAT_ID")
THREAD_ID   = int(os.getenv("THREAD_ID", "0"))
FORCE_TEST  = os.getenv("FORCE_TEST") == "1"
JSON_URL    = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
TZ          = pytz.timezone("Europe/Berlin")
# ========================

logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("forexbot")

if not BOT_TOKEN or not CHAT_ID:
    log.error("Credenciales vacías. Revisa Secrets.")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)

# ---------- helpers ----------
def fetch_events() -> List[Dict]:
    r = requests.get(JSON_URL, timeout=15)
    r.raise_for_status()
    return r.json()

def filter_by_date(events, date, currencies, levels):
    out = []
    for e in events:
        try:
            if dt.datetime.strptime(e["Date"], "%Y-%m-%d").date() != date:
                continue
        except ValueError:
            continue
        if e["Currency"] not in currencies:
            continue
        if int(e.get("ImpactLevel", 0)) not in levels:
            continue
        out.append(e)
    return out

def format_messages(events) -> List[str]:
    msgs = []
    for e in events:
        t   = e["Time"]
        ev  = e["Event"]
        prev= e["Previous"]
        fc  = e["Forecast"]
        day = e.get("DateTxt", "")
        prefix = f"*{t}* " if not day else f"*{day}* {t} "
        msgs.append(f"🕒 {prefix}| _{ev}_\nForecast: {fc} | Previous: {prev}")
    return msgs

def send_messages(msgs: List[str]):
    for m in msgs:
        bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=THREAD_ID or None,
            text=m,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        time.sleep(1)               # evita rate‑limit

# ---------- main ----------
def main():
    now_utc = dt.datetime.utcnow()
    now     = dt.datetime.now(TZ)
    log.info("Runner UTC:   %s", now_utc.isoformat(sep=" ", timespec="seconds"))
    log.info("Runner Berlín:%s", now.isoformat(sep=" ", timespec="seconds"))

    if FORCE_TEST:
        log.info("FORCE_TEST=1 → enviando mensaje de prueba y saliendo")
        bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=THREAD_ID or None,
            text="🏁 Test CI ok – hora Berlín: " + now.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return

    events = fetch_events()
    log.info("JSON contiene %s eventos", len(events))

    today = now.date()
    wd    = today.weekday()            # lunes = 0

    # 1) 5 min antes
    if now.minute % 5 == 0 and not (wd in [5, 6] and now.hour == 17):
        in_5 = []
        for e in events:
            try:
                dt_event = dt.datetime.strptime(
                    f"{e['Date']} {e['Time']}", "%Y-%m-%d %I:%M%p"
                )
            except ValueError:
                continue
            dt_event = TZ.localize(dt_event)
            if 4.5 < (dt_event - now).total_seconds()/60 <= 5.5 \
               and e["Currency"] in ["USD", "EUR"] \
               and int(e.get("ImpactLevel", 0)) >= 2:
                in_5.append(e)
        if in_5:
            log.info("Alertas 5 min antes (%s eventos)", len(in_5))
            send_messages(format_messages(in_5))
            return

    # 2) diario 06:00
    if now.hour == 6 and now.minute == 0:
        daily = filter_by_date(events, today, ["USD","EUR"], [2,3])
        if daily:
            log.info("Reporte diario (%s eventos)", len(daily))
            send_messages(format_messages(daily))
        return

    # 3) sáb 17:00
    if wd == 5 and now.hour == 17 and now.minute == 0:
        log.info("Resumen semana terminada")
        msgs = []
        start = today - dt.timedelta(days=7)
        for i in range(7):
            d = start + dt.timedelta(days=i)
            for e in filter_by_date(events, d, ["USD","EUR"], [2,3]):
                e["DateTxt"] = d.strftime("%a %d")
                msgs.append(e)
        if msgs:
            send_messages(format_messages(msgs))
        return

    # 4) dom 17:00
    if wd == 6 and now.hour == 17 and now.minute == 0:
        log.info("Vista previa semana entrante")
        msgs = []
        for i in range(1,8):
            d = today + dt.timedelta(days=i)
            for e in filter_by_date(events, d, ["USD","EUR"], [2,3]):
                e["DateTxt"] = d.strftime("%a %d")
                msgs.append(e)
        if msgs:
            send_messages(format_messages(msgs))
        return

    log.info("No toca enviar nada ahora.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Excepción inesperada")
        raise
