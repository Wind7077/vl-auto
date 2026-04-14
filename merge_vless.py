import requests
import re
from datetime import datetime, timezone

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"


def fetch_json():
    r = requests.get(URL_JSON, timeout=30)
    r.raise_for_status()
    return r.json()


def extract_json(data):
    result = []

    if not isinstance(data, dict):
        return result

    for k, v in data.items():
        if isinstance(v, dict):
            for kk in ["best", "top10", "top5", "top20", "all"]:
                val = v.get(kk)

                if isinstance(val, str) and val.startswith("vless://"):
                    result.append(val)

                elif isinstance(val, list):
                    for i in val:
                        if isinstance(i, str) and i.startswith("vless://"):
                            result.append(i)
                        elif isinstance(i, dict):
                            for x in ["key", "vless", "url"]:
                                if x in i and isinstance(i[x], str):
                                    result.append(i[x])

    return result


def fetch_html():
    try:
        r = requests.get(URL_HTML, timeout=30)
        r.raise_for_status()
        return re.findall(r'vless://[^\s"<]+', r.text)
    except Exception:
        return []


def normalize(v):
    return v.strip()


def is_valid(v):
    return isinstance(v, str) and v.startswith("vless://") and len(v) > 50


def main():
    all_vless = []

    try:
        json_data = fetch_json()
        all_vless.extend(extract_json(json_data))
    except Exception as e:
        print("JSON error:", e)

    all_vless.extend(fetch_html())

    cleaned = [normalize(v) for v in all_vless if is_valid(v)]

    # SMART DEDUP (order preserved)
    unique = list(dict.fromkeys(cleaned))

    if not unique:
        raise RuntimeError("Empty VLESS list after merge")

    print("FINAL TOTAL:", len(unique))

    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        f.write(f"# updated: {datetime.now(timezone.utc)}\n")
        for v in unique:
            f.write(v + "\n")


if __name__ == "__main__":
    main()
