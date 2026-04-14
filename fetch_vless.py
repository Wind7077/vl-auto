import requests
from datetime import datetime
import os

URL = "https://tiagorrg.github.io/vless-checker/keys.json"

OUTPUT_FILE = "vless_normal_vpn.txt"

# берём только "Обычный VPN"
CATEGORIES = [
    "baltics",
    "finland",
    "germany",
    "sweden",
    "netherlands",
    "poland"
]


def fetch():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    return r.json()


def extract_from_country(block):
    """
    ВАЖНО: берём ВСЕ, не только best/top10
    """
    result = []

    if not isinstance(block, dict):
        return result

    # 1. best
    if block.get("best"):
        result.append(block["best"])

    # 2. top10 / top5
    for k in ["top10", "top5"]:
        if k in block and isinstance(block[k], list):
            for item in block[k]:
                if isinstance(item, dict) and "key" in item:
                    result.append(item["key"])

    # 3. ALL (самое важное!)
    if "all" in block and isinstance(block["all"], list):
        for item in block["all"]:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict) and "key" in item:
                result.append(item["key"])

    return result


def main():
    data = fetch()

    all_vless = []

    for cat in CATEGORIES:
        if cat in data:
            all_vless.extend(extract_from_country(data[cat]))

    # дедупликация
    all_vless = list(dict.fromkeys(all_vless))

    print("TOTAL:", len(all_vless))

    os.makedirs("output", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# updated: {datetime.utcnow()}\n")
        for v in all_vless:
            if isinstance(v, str) and v.startswith("vless://"):
                f.write(v + "\n")


if __name__ == "__main__":
    main()
