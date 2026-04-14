import requests
import urllib.parse
import re
from datetime import datetime

URL = "https://tiagorrg.github.io/vless-checker/keys.json"
OUTPUT_FILE = "vless_normal_vpn.txt"

TARGET = [
    "estonia", "latvia", "lithuania",
    "finland",
    "germany",
    "sweden",
    "netherlands", "the netherlands",
    "poland"
]

BLACKLIST = ["anycast", "ipv6", "cdn", "test", "cf"]


def normalize(t):
    return re.sub(r'[^a-z0-9 ]', ' ', urllib.parse.unquote(t.lower()))


def is_good(v):
    try:
        low = v.lower()

        if any(b in low for b in BLACKLIST):
            return False

        host = v.split("@")[1].split(":")[0]
        frag = v.split("#")[-1]

        text = normalize(host + " " + frag)

        return any(x in text for x in TARGET)

    except Exception as e:
        print("SKIP ERROR:", e)
        return False


def main():
    try:
        r = requests.get(URL, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print("FETCH ERROR:", e)
        exit(1)

    print("TYPE:", type(data))

    vless_list = []

    try:
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.values()
        else:
            items = []
    except Exception as e:
        print("STRUCT ERROR:", e)
        items = []

    for item in items:
        if isinstance(item, str) and item.startswith("vless://"):
            if is_good(item):
                vless_list.append(item)

        elif isinstance(item, dict):
            for v in item.values():
                if isinstance(v, str) and v.startswith("vless://"):
                    if is_good(v):
                        vless_list.append(v)

    print("FOUND:", len(vless_list))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# updated: {datetime.utcnow()}\n")
        for v in vless_list:
            f.write(v + "\n")


if __name__ == "__main__":
    main()
