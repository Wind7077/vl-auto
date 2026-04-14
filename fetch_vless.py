import requests
import urllib.parse
from datetime import datetime
import os

URL = "https://tiagorrg.github.io/vless-checker/keys.json"

TARGET = ["Estonia", "Finland", "Germany", "Sweden", "Netherlands", "Poland", "Latvia", "Lithuania"]

BLACKLIST = ["anycast", "ipv6", "cdn", "test", "cf"]

OUTPUT = "output/vless_eu.txt"


def fetch():
    return requests.get(URL, timeout=20).json()


def extract_country(vless):
    try:
        fragment = urllib.parse.unquote(vless.split("#")[-1]).lower()
        return fragment
    except:
        return ""


def is_valid(vless):
    low = vless.lower()

    if any(b in low for b in BLACKLIST):
        return False

    frag = extract_country(vless)

    return any(t.lower() in frag for t in TARGET)


def extract(data):
    out = []

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.values()
    else:
        return []

    for item in items:
        if isinstance(item, str) and item.startswith("vless://"):
            if is_valid(item):
                out.append(item)

        elif isinstance(item, dict):
            for v in item.values():
                if isinstance(v, str) and v.startswith("vless://"):
                    if is_valid(v):
                        out.append(v)

    return out


def save(data):
    os.makedirs("output", exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
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
