import requests
from datetime import datetime
import os
from urllib.parse import urlparse

URL = "https://tiagorrg.github.io/vless-checker/keys.json"

OUTPUT_FILE = "vless_normal_vpn.txt"

CATEGORIES = [
    "baltics",
    "finland",
    "germany",
    "sweden",
    "netherlands",
    "poland"
]

# ❌ мусорные домены (анти-VPN / чужие сети)
BLOCKED_DOMAINS = [
    "anti-vpn.ru",
    "csbeta60.com",
    "fastsync.xyz",
    "beestvpn.ru",
    "vpn-port.com",
    "nitroo-tech.ru",
    "stardevs.top"
]


def fetch():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    return r.json()


def is_good(vless: str) -> bool:
    try:
        if not vless.startswith("vless://"):
            return False

        host = vless.split("@")[1].split(":")[0]

        # фильтр мусора
        for b in BLOCKED_DOMAINS:
            if b in host:
                return False

        # убираем явные тестовые/дублирующиеся схемы
        if "alpn=http%2525" in vless:
            return False

        return True

    except:
        return False


def collect(obj, out):
    if isinstance(obj, str):
        if obj.startswith("vless://") and is_good(obj):
            out.append(obj)

    elif isinstance(obj, dict):
        for v in obj.values():
            collect(v, out)

    elif isinstance(obj, list):
        for v in obj:
            collect(v, out)


def main():
    data = fetch()

    all_vless = []

    for cat in CATEGORIES:
        if cat in data:
            collect(data[cat], all_vless)

    # дедуп
    all_vless = list(dict.fromkeys(all_vless))

    print("TOTAL CLEAN:", len(all_vless))

    os.makedirs("output", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# updated: {datetime.utcnow()}\n")
        for v in all_vless:
            f.write(v + "\n")


if __name__ == "__main__":
    main()
