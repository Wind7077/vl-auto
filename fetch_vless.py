import requests
import urllib.parse
from datetime import datetime
import os
import re

URL = "https://tiagorrg.github.io/vless-checker/keys.json"

HOST_MAP = {
    "es.": "estonia",
    "fi.": "finland",
    "gr.": "germany",
    "de.": "germany",
    "nl.": "netherlands",
    "pl.": "poland",
    "se.": "sweden",
    "lv.": "latvia",
    "lt.": "lithuania"
}

TARGET = set(HOST_MAP.values())

BLACKLIST = ["anycast", "ipv6", "cdn", "test", "cf"]

OUTPUT = "output/vless_eu.txt"


def fetch():
    return requests.get(URL, timeout=20).json()


def normalize(text):
    text = urllib.parse.unquote(text).lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return text


def detect_country(vless):
    try:
        host = vless.split("@")[1].split(":")[0].lower()
    except:
        host = ""

    try:
        frag = vless.split("#")[-1]
    except:
        frag = ""

    host_country = None

    for k, v in HOST_MAP.items():
        if k in host:
            host_country = v
            break

    frag_norm = normalize(frag)

    if host_country:
        return host_country

    for country in TARGET:
        if country in frag_norm:
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
