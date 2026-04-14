import requests
import urllib.parse
import re
import os
from datetime import datetime

URL = "https://tiagorrg.github.io/vless-checker/keys.json"

# страны из "Обычный VPN"
TARGET_KEYWORDS = [
    "estonia", "latvia", "lithuania",
    "finland",
    "germany",
    "sweden",
    "netherlands", "the netherlands",
    "poland"
]

BLACKLIST = ["anycast", "ipv6", "cdn", "test", "cf"]

OUTPUT_FILE = "vless_normal_vpn.txt"


def fetch():
    return requests.get(URL, timeout=20).json()


def normalize(text):
    text = urllib.parse.unquote(text).lower()
    return re.sub(r'[^a-z0-9 ]', ' ', text)


def is_normal_vpn(vless):
    low = vless.lower()

    # убираем мусор
    if any(b in low for b in BLACKLIST):
        return False

    frag = vless.split("#")[-1]
    host = ""

    try:
        host = vless.split("@")[1].split(":")[0]
    except:
        pass

    text = normalize(frag + " " + host)

    return any(k in text for k in TARGET_KEYWORDS)


def extract(data):
    result = []

    items = data if isinstance(data, list) else data.values()

    for item in items:
        if isinstance(item, str) and item.startswith("vless://"):
            if is_normal_vpn(item):
                result.append(item)

        elif isinstance(item, dict):
            for v in item.values():
                if isinstance(v, str) and v.startswith("vless://"):
                    if is_normal_vpn(v):
                        result.append(v)

    return result


def save(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# updated: {datetime.utcnow()}\n")
        for x in data:
            f.write(x + "\n")


def main():
    data = fetch()
    vless = extract(data)

    print("FOUND:", len(vless))
    save(vless)


if __name__ == "__main__":
    main()
