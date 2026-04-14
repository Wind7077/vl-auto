import requests
from datetime import datetime
import os

URL = "https://tiagorrg.github.io/vless-checker/keys.json"

TARGET = ["LV", "LT", "EE", "FI", "DE", "SE", "NL", "PL"]

BLACKLIST = ["anycast", "ipv6", "cdn", "test", "cf"]

OUTPUT = "output/vless_eu.txt"


def fetch():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    return r.json()


def is_valid(key):
    low = key.lower()

    if any(b in low for b in BLACKLIST):
        return False

    if not any(c in key.upper() for c in TARGET):
        return False

    return True


def extract(data):
    result = []

    # структура keys.json может быть разная → делаем универсально
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.values()
    else:
        return []

    for item in items:
        if isinstance(item, str):
            if item.startswith("vless://") and is_valid(item):
                result.append(item)

        elif isinstance(item, dict):
            for v in item.values():
                if isinstance(v, str) and v.startswith("vless://"):
                    if is_valid(v):
                        result.append(v)

    return result


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
