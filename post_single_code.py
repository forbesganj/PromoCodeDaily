"""
Single Promo Code Poster (high-frequency mode)
------------------------------------------------
Posts ONE promo code per run, rotating through the active codes in the
Google Sheet. Meant to be triggered many times a day (10-15x) by the
GitHub Actions workflow, so the channel stays active throughout the day
instead of one big daily dump.

Rotation is deterministic and needs no external state: it's derived from
the day-of-year + current UTC hour, so consecutive runs naturally move to
the next code, and the cycle reshuffles slightly day to day.

Each post now includes: the app's image (banner/icon), the promo code, and
the redeem link — sent as a photo with caption via Telegram's sendPhoto API.

Sheet columns expected (row 1 = header):
  App Name | Code | Redeem Link | Image URL | Expiry (optional) | Active (TRUE/FALSE)

Env vars required (same as post_promo_codes.py):
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SHEET_CSV_URL
"""

import os
import sys
import csv
import io
import datetime
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SHEET_CSV_URL = os.environ.get("SHEET_CSV_URL")


def fetch_sheet_rows(csv_url: str):
    resp = requests.get(csv_url, timeout=20)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    return list(reader)


def get_active_codes(rows):
    return [
        r for r in rows
        if str(r.get("Active", "TRUE")).strip().upper() != "FALSE"
        and r.get("Code", "").strip()
    ]


def pick_row(active_rows):
    """Deterministically rotate through codes based on date + hour (UTC)."""
    now = datetime.datetime.utcnow()
    idx = (now.timetuple().tm_yday + now.hour) % len(active_rows)
    return active_rows[idx]


def build_caption(row):
    """Caption text that goes UNDER the image (max 1024 chars on Telegram)."""
    app = row.get("App Name", "").strip()
    code = row.get("Code", "").strip()
    link = row.get("Redeem Link", "").strip()
    expiry = row.get("Expiry", "").strip()

    lines = [f"🎮 <b>{app}</b> — Promo Code! 🔥", "", f"Code: <code>{code}</code>"]
    if link:
        lines.append(f"🔗 <a href=\"{link}\">Redeem here</a>")
    if expiry:
        lines.append(f"⏳ Valid till: {expiry}")
    lines.append("")
    lines.append("📢 <i>Forward to a friend before it expires!</i>")
    return "\n".join(lines)


def send_photo_to_telegram(image_url: str, caption: str):
    """Send image + caption (code + link) as one post via sendPhoto."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML",
    }
    resp = requests.post(url, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def send_text_to_telegram(message: str):
    """Fallback: plain text post, used only if a row has no Image URL."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    resp = requests.post(url, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def main():
    missing = [name for name, val in [
        ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
        ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID),
        ("SHEET_CSV_URL", SHEET_CSV_URL),
    ] if not val]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    rows = fetch_sheet_rows(SHEET_CSV_URL)
    active_rows = get_active_codes(rows)

    if not active_rows:
        print("No active promo codes found. Nothing posted.")
        return

    row = pick_row(active_rows)
    caption = build_caption(row)
    image_url = row.get("Image URL", "").strip()

    if image_url:
        result = send_photo_to_telegram(image_url, caption)
    else:
        # No image for this app yet — still post, just without a photo.
        print(f"WARNING: No Image URL for '{row.get('App Name')}', posting text-only.")
        result = send_text_to_telegram(caption)

    print(f"Posted code for '{row.get('App Name')}':", result.get("ok"))


if __name__ == "__main__":
    main()
