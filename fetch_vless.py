import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from datetime import datetime
import os

URL = "https://tiagorrg.github.io/vless-checker/"

TARGET = ["LV", "LT", "EE", "FI", "DE", "SE", "NL", "PL"]

BLACKLIST = ["anycast", "ipv6", "cdn", "test", "cf"]

OUTPUT = "output/vless_eu.txt"


def fetch():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    return r.text


def extract(html):
    soup = BeautifulSoup(html, "html.parser")
    out = []

    for tag in soup.find_all(["code", "pre", "td"]):
        t = tag.get_text(strip=True)
        if t.startswith("vless://"):
            out.append(t)

    return out


def get_remark(vless):
    try:
        parsed = urlparse(vless)
        return unquote(parsed.fragment or "").upper()
    except:
        return ""


def valid(vless):
    low = vless.lower()
    remark = get_remark(vless)

    if not any(c in remark for c in TARGET):
        return False

    if any(b in low for b in BLACKLIST):
        return False

    return True


def save(data):
    os.makedirs("output", exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(f"# updated: {datetime.utcnow()}\n")
        for x in data:
            f.write(x + "\n")


def main():
    html = fetch()
    proxies = extract(html)
    filtered = [p for p in proxies if valid(p)]

    print(f"total: {len(proxies)} | filtered: {len(filtered)}")

    save(filtered)


if __name__ == "__main__":
    main()
