import requests
from datetime import datetime

URL = "https://tiagorrg.github.io/vless-checker/keys.json"

CATEGORIES = [
    "baltics",
    "finland",
    "germany",
    "sweden",
    "netherlands",
    "poland",
    "other"
]

def fetch():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    return r.json()

def extract_any(block):
    result = []

    if not isinstance(block, dict):
        return result

    # 1. best
    if isinstance(block.get("best"), str):
        result.append(block["best"])

    # 2. top lists
    for k in ["top10", "top5", "top20"]:
        v = block.get(k)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict):
                    if "key" in item:
                        result.append(item["key"])
                    elif "vless" in item:
                        result.append(item["vless"])

    # 3. all (если есть)
    v = block.get("all")
    if isinstance(v, list):
        for item in v:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                if "key" in item:
                    result.append(item["key"])
                elif "vless" in item:
                    result.append(item["vless"])

    # 4. fallback: иногда лежит напрямую массивом
    for k, v in block.items():
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str) and item.startswith("vless://"):
                    result.append(item)
                elif isinstance(item, dict):
                    for kk in ["key", "vless", "url"]:
                        if kk in item and isinstance(item[kk], str):
                            result.append(item[kk])

    return result

def main():
    data = fetch()

    all_vless = []

    for cat in CATEGORIES:
        block = data.get(cat)
        if not block:
            continue

        all_vless.extend(extract_any(block))

    # дедуп
    all_vless = list(dict.fromkeys(
        [x for x in all_vless if isinstance(x, str) and x.startswith("vless://")]
    ))

    print("TOTAL:", len(all_vless))

    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        f.write(f"# updated: {datetime.utcnow()}\n")
        for v in all_vless:
            f.write(v + "\n")

if __name__ == "__main__":
    main()
