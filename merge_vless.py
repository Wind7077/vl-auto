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
    r = requests.get(URL_HTML, timeout=30)
    r.raise_for_status()
    return re.findall(r'vless://[^\s"<]+', r.text)


def normalize(v):
    return v.strip()


def main():
    all_vless = []

    # JSON source
    try:
        json_data = fetch_json()
        all_vless.extend(extract_json(json_data))
    except Exception as e:
        print("JSON error:", e)

    # HTML source
    try:
        all_vless.extend(fetch_html())
    except Exception as e:
        print("HTML error:", e)

    # очистка
    cleaned = []
    for v in all_vless:
        if isinstance(v, str) and v.startswith("vless://"):
            cleaned.append(normalize(v))

    # УМНЫЙ ДЕПУБ (сохраняет порядок)
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
