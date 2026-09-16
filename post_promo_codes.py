"""
Daily Telegram Promo Code Poster
---------------------------------
Reads today's promo codes from a public Google Sheet (published as CSV)
and posts a formatted message to a Telegram channel/group.

Setup required (see README.md):
  1. TELEGRAM_BOT_TOKEN - from @BotFather
  2. TELEGRAM_CHAT_ID   - your channel's @username or numeric chat id
  3. SHEET_CSV_URL      - your Google Sheet's "Publish to web" CSV link

Sends all active codes as one Telegram "album" (media group) — each app's
image with its own code + link as the caption underneath, all in a single
pinnable post.

Sheet columns expected (row 1 = header):
  App Name | Code | Redeem Link | Image URL | Expiry (optional) | Active (TRUE/FALSE)

Note: Telegram media groups support max 10 items per post — fine for 10 apps.
If you add more than 10, only the first 10 active rows will be included.
"""

import os
import sys
import csv
import io
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SHEET_CSV_URL = os.environ.get("SHEET_CSV_URL")


def fetch_sheet_rows(csv_url: str):
    """Download the published Google Sheet CSV and return rows as dicts."""
    resp = requests.get(csv_url, timeout=20)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = [row for row in reader]
    return rows


def get_active_rows(rows, limit=10):
    active_rows = [
        r for r in rows
        if str(r.get("Active", "TRUE")).strip().upper() != "FALSE"
        and r.get("Code", "").strip()
    ]
    return active_rows[:limit]  # Telegram media groups cap at 10 items


def build_caption(row, is_first: bool):
    app = row.get("App Name", "").strip()
    code = row.get("Code", "").strip()
    link = row.get("Redeem Link", "").strip()
    expiry = row.get("Expiry", "").strip()

    prefix = "🎮 <b>TODAY'S PROMO CODES</b> 🔥\n\n" if is_first else ""
    entry = f"{prefix}🕹 <b>{app}</b>\nCode: <code>{code}</code>"
    if link:
        entry += f"\n🔗 <a href=\"{link}\">Redeem here</a>"
    if expiry:
        entry += f"\n⏳ Valid till: {expiry}"
    return entry


def send_album_to_telegram(active_rows):
    """Send all active codes as one media group (album): image + caption each."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
    media = []
    for i, row in enumerate(active_rows):
        image_url = row.get("Image URL", "").strip()
        if not image_url:
            continue  # sendMediaGroup requires every item to have a photo
        media.append({
            "type": "photo",
            "media": image_url,
            "caption": build_caption(row, is_first=(i == 0)),
            "parse_mode": "HTML",
        })

    if not media:
        return None

    payload = {"chat_id": TELEGRAM_CHAT_ID, "media": media}
    resp = requests.post(url, json=payload, timeout=30)
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
    active_rows = get_active_rows(rows)

    if not active_rows:
        print("No active promo codes found today. Nothing posted.")
        return

    result = send_album_to_telegram(active_rows)
    if result is None:
        print("No rows had an Image URL — nothing posted. Add images to the sheet.")
        return

    print("Posted successfully:", result.get("ok"))


if __name__ == "__main__":
    main()
