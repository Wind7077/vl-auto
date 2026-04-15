import requests
import re
import yaml
from datetime import datetime, timezone
from urllib.parse import unquote

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"


def fetch_json():
    try:
        r = requests.get(URL_JSON, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def extract_json(data):
    result = []
    if not isinstance(data, dict):
        return result

    for _, v in data.items():
        if isinstance(v, dict):
            for kk in ["best", "top10", "top5", "all"]:
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
        r = requests.get(URL_HTML, timeout=20)
        r.raise_for_status()
        return re.findall(r'vless://[^\s"<]+', r.text)
    except Exception:
        return []


def normalize(v):
    return v.strip()


def is_valid(v):
    return isinstance(v, str) and v.startswith("vless://") and len(v) > 50


def deduplicate(lst):
    return list(dict.fromkeys(lst))


def generate_clash_yaml(proxies, filename="clash_vless.yaml"):
    """
    Гарантированная генерация YAML даже если proxies пустой
    """

    config = {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",

        "proxies": [],

        "proxy-groups": [
            {
                "name": "AUTO",
                "type": "select",
                "proxies": ["DIRECT"]
            }
        ],

        "rules": [
            "MATCH,DIRECT"
        ]
    }

    # если есть прокси — добавляем
    for v in proxies:
        config["proxies"].append({
            "name": v[:50],
            "type": "vless",
            "server": "127.0.0.1",
            "port": 443,
            "uuid": "00000000-0000-0000-0000-000000000000"
        })

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# generated {datetime.now(timezone.utc)}\n\n")
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print(f"YAML OK: {filename} ({len(proxies)} proxies)")


def main():
    all_vless = []

    json_data = fetch_json()
    all_vless.extend(extract_json(json_data))
    all_vless.extend(fetch_html())

    cleaned = [normalize(v) for v in all_vless if is_valid(v)]
    unique = deduplicate(cleaned)

    print("RAW:", len(unique))

    # ВАЖНО: НИКАКИХ DNS / IP FILTERS
    filtered = unique

    print("FINAL:", len(filtered))

    # TXT всегда создаётся
    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        f.write(f"# updated {datetime.now(timezone.utc)}\n")
        f.write(f"# total {len(filtered)}\n\n")
        for v in filtered:
            f.write(v + "\n")

    # YAML всегда создаётся (даже если пусто)
    generate_clash_yaml(filtered)


if __name__ == "__main__":
    main()
