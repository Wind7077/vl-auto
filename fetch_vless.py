import requests
import urllib.parse
from datetime import datetime
import os
import re

URL = "https://tiagorrg.github.io/vless-checker/keys.json"

TARGET = {
    "estonia": ["estonia", "ee"],
    "finland": ["finland", "fi"],
    "germany": ["germany", "de"],
    "sweden": ["sweden", "se"],
    "netherlands": ["netherlands", "the netherlands", "nl"],
    "poland": ["poland", "pl"],
    "latvia": ["latvia", "lv"],
    "lithuania": ["lithuania", "lt"]
}

BLACKLIST = ["anycast", "ipv6", "cdn", "test", "cf"]

OUTPUT = "output/vless_eu.txt"


def fetch():
    return requests.get(URL, timeout=20).json()


def normalize(text):
    text = urllib.parse.unquote(text)
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return text


def extract_meta(vless):
    try:
        host = vless.split("@")[1].split(":")[0]
        frag = vless.split("#")[-1]
        return host, frag
    except:
        return "", ""


def detect_country(vless):
    host, frag = extract_meta(vless)

    host_n = normalize(host)
    frag_n = normalize(frag)

    combined = host_n + " " + frag_n

    for country, variants in TARGET.items():
        for v in variants:
            if v in combined:
                return country

    return None


def is_valid(vless):
    low = vless.lower()

    if any(b in low for b in BLACKLIST):
        return False

    return detect_country(vless) is not None


def extract(data):
    out = []

    items = data if isinstance(data, list) else data.values()

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
