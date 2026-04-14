import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime
import os

URL = "https://tiagorrg.github.io/vless-checker/"

TARGET = ["LV", "LT", "EE", "FI", "DE", "SE", "NL", "PL"]

BLACKLIST_WORDS = [
    "anycast",
    "ipv6",
    "cdn",
    "cf",
    "test"
]

OUTPUT_FILE = "output/vless_eu.txt"


def fetch():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    return r.text


def extract_vless(html):
    soup = BeautifulSoup(html, "html.parser")
    result = []

    for tag in soup.find_all(["code", "pre", "td"]):
        text = tag.get_text(strip=True)
        if text.startswith("vless://"):
            result.append(text)

    return result


def parse_remark(vless_url):
    try:
        parsed = urlparse(vless_url)
        fragment = unquote(parsed.fragment)  # часть после #
        return fragment.upper()
    except:
        return ""


def is_valid(proxy):
    remark = parse_remark(proxy)

    # фильтр стран
    if not any(c in remark for c in TARGET):
        return False

    # фильтр мусора
    low = proxy.lower()
    if any(bad in low for bad in BLACKLIST_WORDS):
        return False

    return True


def save(proxies):
    os.makedirs("output", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# updated: {datetime.utcnow()}\n")
        for p in proxies:
            f.write(p + "\n")


def main():
    html = fetch()
    proxies = extract_vless(html)

    filtered = [p for p in proxies if is_valid(p)]

    print(f"TOTAL: {len(proxies)} | FILTERED: {len(filtered)}")

    save(filtered)


if __name__ == "__main__":
    main()
