#!/usr/bin/env python3
# -*- coding: utf‑8 -*-

"""
Bot de noticias económicas para Telegram.
Envío:
  • 06:00 Berlín – reporte diario
  • 5 min antes de cada evento USD/EUR impacto medio/alto
  • Sáb 17:00 – resumen semana que termina
  • Dom 17:00 – vista previa semana entrante
Compatible con python‑telegram‑bot 13.x (sin async).
"""

import os
import sys
import json
import time
import logging
import datetime as dt
from typing import List, Dict

import pytz
import requests
from telegram import Bot

# ========= CONFIGURACIÓN =========
BOT_TOKEN   = os.getenv("BOT_TOKEN")           # GitHub Secrets
CHAT_ID     = os.getenv("CHAT_ID")             # GitHub Secrets
THREAD_ID   = int(os.getenv("THREAD_ID", "0")) # GitHub Secrets
JSON_URL    = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
TZ          = pytz.timezone("Europe/Berlin")
# =================================

# --- logging muy verboso a STDERR ---
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("forexbot")

# Comprobación temprana de credenciales
if not BOT_TOKEN or not CHAT_ID:
    log.error("❌ BOT_TOKEN o CHAT_ID vacíos. Revisa tus Secrets.")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)

# --------------------------------------------------------------------- #
#                            FUNCIONES ÚTILES                           #
# --------------------------------------------------------------------- #
def fetch_events() -> List[Dict]:
    """Descarga el feed JSON de ForexFactory y lo devuelve como lista."""
    log.info("Descargando feed JSON…")
    r = requests.get(JSON_URL, timeout=15)
    r.raise_for_status()
    return r.json()


def filter_by_date(events, date: dt.date, currencies, levels):
    """Filtra eventos por fecha, divisas e impacto."""
    out = []
    for e in events:
        try:
            e_date = dt.datetime.strptime(e["Date"], "%Y-%m-%d").date()
        except ValueError:
            continue  # fecha mal formateada

        if e_date != date:
            continue
        if e["Currency"] not in currencies:
            continue
        # ImpactLevel puede venir como str ("3") o int (3)
        if int(e.get("ImpactLevel", 0)) not in levels:
            continue
        out.append(e)
    return out


def format_messages(events) -> List[str]:
    """Convierte eventos en textos Markdown listos para Telegram."""
    msgs = []
    for e in events:
        t   = e["Time"]       # ej. "08:30am"
        ev  = e["Event"]
        prev= e["Previous"]
        fc  = e["Forecast"]
        day = e.get("DateTxt", "")  # opcional (para resúmenes semanales)
        prefix = f"*{t}* " if day == "" else f"*{day}* {t} "
        msgs.append(
            f"🕒 {prefix}| _{ev}_\nForecast: {fc} | Previous: {prev}"
        )
    return msgs


def send_messages(msgs: List[str]):
    """Envía una lista de mensajes al hilo del canal."""
    for m in msgs:
        bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=THREAD_ID if THREAD_ID else None,
            text=m,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        time.sleep(1)  # evita rate‑limit (máx. 30 msg/seg)


# --------------------------------------------------------------------- #
#                                 MAIN                                  #
# --------------------------------------------------------------------- #
def main():
    log.info("🟢 Entrando en main()")
    now   = dt.datetime.now(TZ)
    today = now.date()
    wd    = today.weekday()  # lunes=0, domingo=6

    try:
        events = fetch_events()
    except Exception as ex:
        log.exception("❌ Error al descargar el JSON: %s", ex)
        return

    # 1) ▶️ 5 min antes de cada evento (excepto sáb/dom 17 h: resúmenes)
    if now.minute % 5 == 0 and not (wd in [5, 6] and now.hour == 17):
        in_5 = []
        for e in events:
            # combinamos Date+Time en datetime
            try:
                dt_event = dt.datetime.strptime(
                    f"{e['Date']} {e['Time']}",
                    "%Y-%m-%d %I:%M%p",
                )
            except ValueError:
                continue  # formato de hora raro (“All Day”, etc.)

            dt_event = TZ.localize(dt_event)
            delta_min = (dt_event - now).total_seconds() / 60
            if 4.5 < delta_min <= 5.5 \
               and e["Currency"] in ["USD", "EUR"] \
               and int(e.get("ImpactLevel", 0)) >= 2:
                in_5.append(e)

        if in_5:
            log.info("⏰ Enviando alertas ‘5 min antes’ (%s eventos)", len(in_5))
            send_messages(format_messages(in_5))
            return

    # 2) ▶️ Reporte diario a las 06:00
    if now.hour == 6 and now.minute == 0:
        today_ev = filter_by_date(events, today, ["USD", "EUR"], [2, 3])
        if today_ev:
            log.info("📅 Enviando reporte diario (%s eventos)", len(today_ev))
            send_messages(format_messages(today_ev))
        return

    # 3) ▶️ Resumen de la semana pasada – sábados 17:00
    if wd == 5 and now.hour == 17 and now.minute == 0:
        log.info("📊 Resumen semana TERMINADA")
        msgs = []
        start = today - dt.timedelta(days=7)
        for i in range(7):
            d = start + dt.timedelta(days=i)
            evs = filter_by_date(events, d, ["USD", "EUR"], [2, 3])
            for e in evs:
                e["DateTxt"] = d.strftime("%a %d")
                msgs.append(e)
        if msgs:
            send_messages(format_messages(msgs))
        return

    # 4) ▶️ Vista previa semana entrante – domingos 17:00
    if wd == 6 and now.hour == 17 and now.minute == 0:
        log.info("🔮 Vista previa semana ENTRANTE")
        msgs = []
        for i in range(1, 8):
            d = today + dt.timedelta(days=i)
            evs = filter_by_date(events, d, ["USD", "EUR"], [2, 3])
            for e in evs:
                e["DateTxt"] = d.strftime("%a %d")
                msgs.append(e)
        if msgs:
            send_messages(format_messages(msgs))
        return

    log.info("⚪️ No hay notificaciones que enviar ahora.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("💥 Excepción no controlada")
        raise
