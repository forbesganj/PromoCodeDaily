"""Flexible parser for promo posts from Telegram public preview pages."""
import html
import re
from urllib.parse import parse_qs, urlparse, unquote

URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+", re.I)
CODE_QUERY_RE = re.compile(r"(?:\?|&)code=([^&\s]+)", re.I)
CODE_LABEL_RE = re.compile(
    r"(?:promo\s*code|promo\s*code\s*2|code|coupon)\s*[:=\-👉]*\s*([A-Za-z0-9_-]{4,})",
    re.I,
)

def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())

def find_app(text: str, allowed_apps: list[str]):
    normalized_text = normalize(text)
    # Longest names first prevents partial-name collisions.
    for app in sorted(allowed_apps, key=len, reverse=True):
        if normalize(app) in normalized_text:
            return app
    return None

def clean_url(url: str) -> str:
    return html.unescape(url).rstrip(".,;)>]}")

def extract_codes(text: str):
    """Return unique codes in appearance order."""
    found = []
    for url in URL_RE.findall(text):
        url = clean_url(url)
        match = CODE_QUERY_RE.search(url)
        if match:
            code = unquote(match.group(1)).strip()
            if code and code not in found:
                found.append(code)

    # Fallback for posts that show a code without ?code= in a URL.
    for match in CODE_LABEL_RE.finditer(text):
        code = match.group(1).strip()
        if code.lower() not in {"new", "drop", "today", "here"} and code not in found:
            found.append(code)
    return found

def parse_post(text: str, allowed_apps: list[str]):
    app = find_app(text, allowed_apps)
    if not app:
        return []
    codes = extract_codes(text)
    if not codes:
        return []
    return [{"app_name": app, "code": code} for code in codes]
