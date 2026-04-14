import requests
import re
from datetime import datetime
import os

JS_URL = "https://tiagorrg.github.io/vless-checker/script.js?v=2"

TARGET = ["LV", "LT", "EE", "FI", "DE", "SE", "NL", "PL"]

BLACKLIST = ["anycast", "ipv6", "cdn", "test", "cf"]

OUTPUT = "output/vless_eu.txt"


def fetch_js():
    r = requests.get(JS_URL, timeout=30)
    r.raise_for_status()
    return r.text


def extract_vless(js):
    # достаём все vless:// из JS
    return re.findall(r'vless://[^\s"\']+', js)


def get_country(text):
    # пытаемся вытащить страну из строки
    match = re.search(r'\b(EE|LV|LT|FI|DE|SE|NL|PL)\b', text.upper())
    return match.group(1) if match else ""


def is_valid(vless):
    low = vless.lower()

    if any(b in low for b in BLACKLIST):
        return False

    country = get_country(vless)

    return country in TARGET


def save(data):
    os.makedirs("output", exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(f"# updated: {datetime.utcnow()}\n")
        for x in data:
            f.write(x + "\n")


def main():
    js = fetch_js()

    vless = extract_vless(js)

    filtered = [v for v in vless if is_valid(v)]

    print(f"TOTAL: {len(vless)} | FILTERED: {len(filtered)}")

    save(filtered)


if __name__ == "__main__":
    main()
