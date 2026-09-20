"""Telegram publisher."""
import os
import requests

API_BASE = "https://api.telegram.org/bot{}"

def send_message(text: str):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "@DailyVaultIN")
    url = API_BASE.format(token) + "/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(payload)
    return payload

def escape_html(value: str) -> str:
    return (
        str(value).replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

def build_premium_post(app_name: str, code: str, referral_link: str):
    return (
        "⚡ <b>DAILYVAULTIN</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"🎁 <b>{escape_html(app_name)} — New Promo Code</b>\n\n"
        f"🔐 <b>Code:</b> <code>{escape_html(code)}</code>\n\n"
        f"🔗 <b>Claim Here:</b>\n{escape_html(referral_link)}\n\n"
        "⚠️ Check the app's eligibility and terms before claiming.\n"
        "━━━━━━━━━━━━━━\n"
        "📌 <i>DailyVaultIN • Promo Updates</i>"
    )
