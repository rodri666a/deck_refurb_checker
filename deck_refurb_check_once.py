#!/usr/bin/env python3
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
import requests

# --- Configuración por variables de entorno (ver workflow) ---
COUNTRY = os.getenv("COUNTRY", "ES")

# IDs oficiales (puedes ajustar si alguna vez cambian)
PACKAGES = {
    903905: "Steam Deck 64GB LCD (Refurb)",
    903906: "Steam Deck 256GB LCD (Refurb)",
    903907: "Steam Deck 512GB LCD (Refurb)",
    1202542: "Steam Deck 512GB OLED (Refurb)",
    1202547: "Steam Deck 1TB OLED (Refurb)",
}

API_URL = "https://api.steampowered.com/IPhysicalGoodsService/CheckInventoryAvailableByPackage/v1/"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://store.steampowered.com",
    "Referer": "https://store.steampowered.com/",
}

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Gmail SMTP (requiere 2FA + App Password)
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL", GMAIL_USER)

STORE_URL = "https://store.steampowered.com/sale/steamdeckrefurbished/?l=spanish"


def check_one(package_id: int, country_code: str) -> bool:
    params = {"packageid": str(package_id), "country_code": country_code, "format": "json"}
    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()
    return bool(data.get("response", {}).get("available"))


def notify_telegram(text: str):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": True}
    try:
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print(f"[WARN] Telegram fallo: {e}")


def notify_email(subject: str, body: str):
    if not (GMAIL_USER and GMAIL_APP_PASSWORD and TO_EMAIL):
        return
    msg = EmailMessage()
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"[WARN] Email fallo: {e}")


def main():
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    in_stock = []

    for pkg, name in PACKAGES.items():
        try:
            available = check_one(pkg, COUNTRY)
            status = "EN STOCK" if available else "Sin stock"
            print(f"[{ts}] {name}: {status}")
            if available:
                in_stock.append(name)
        except Exception as e:
            print(f"[{ts}] Error consultando {pkg} {name}: {e}")

    if True:
        joined = "\n".join(f"• {n}" for n in in_stock)
        text = (
            f"🔥 Steam Deck (Refurb) DISPONIBLE en {COUNTRY}\n"
            f"{joined}\n\nCompra: {STORE_URL}\n"
            f"Hora: {ts}"
        )
        notify_telegram(text)
        notify_email("Steam Deck Refurb: ¡EN STOCK!", text)
    else:
        print(f"[{ts}] No hay stock en {COUNTRY}.")


if __name__ == "__main__":
    main()
