"""Monitor configured public Telegram preview pages and publish selected promo codes."""
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .parser import parse_post
from .publisher import build_premium_post, send_message

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"
STATE_PATH = ROOT / "data" / "state.json"

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

def fetch_posts(channel: str):
    url = f"https://t.me/s/{channel.lstrip('@')}"
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 DailyVaultIN-Monitor/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    posts = []

    for node in soup.select(".tgme_widget_message_wrap"):
        data_post = node.select_one("[data-post]")
        text_node = node.select_one(".tgme_widget_message_text")
        if not data_post or not text_node:
            continue

        post_ref = data_post.get("data-post", "")
        match = re.search(r"/(\d+)$", post_ref)
        if not match:
            continue

        post_id = int(match.group(1))
        text = text_node.get_text("\n", strip=True)
        posts.append({"id": post_id, "text": text})

    return sorted(posts, key=lambda item: item["id"])

def main():
    config = load_json(CONFIG_PATH)
    state = load_json(STATE_PATH)

    allowed_apps = config["allowed_apps"]
    referral_links = config["referral_links"]
    settings = config.get("settings", {})
    max_posts = int(settings.get("max_posts_per_run_per_channel", 50))
    require_link = bool(settings.get("require_referral_link", True))

    for channel in config["source_channels"]:
        last_id = int(state.get("channels", {}).get(channel, 0))
        posts = [p for p in fetch_posts(channel) if p["id"] > last_id]
        posts = posts[-max_posts:]

        max_seen = last_id
        for post in posts:
            max_seen = max(max_seen, post["id"])
            parsed_items = parse_post(post["text"], allowed_apps)

            for item in parsed_items:
                app = item["app_name"]
                code = item["code"]
                referral_link = referral_links.get(app, "").strip()

                if require_link and (
                    not referral_link or referral_link.startswith("PASTE_YOUR_")
                ):
                    print(f"SKIP: referral link missing for {app}")
                    continue

                message = build_premium_post(app, code, referral_link)
                send_message(message)
                print(f"PUBLISHED: {channel} / {post['id']} / {app} / {code}")

        state.setdefault("channels", {})[channel] = max_seen

    save_json(STATE_PATH, state)

if __name__ == "__main__":
    main()
