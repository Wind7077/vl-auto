import requests
import re
import ipaddress
import socket
import yaml
from datetime import datetime, timezone
from urllib.parse import unquote

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"


# ─────────────────────────────────────────────
# SAFE UTILS
# ─────────────────────────────────────────────

def safe_name(text: str) -> str:
    """Гарантируем что YAML/Clash не упадёт"""
    if not isinstance(text, str):
        return "node"
    text = unquote(text)
    text = text.replace("\n", " ").replace("\r", " ")
    text = text.replace(":", "-")
    text = text.replace("#", "-")
    text = text.strip()
    return text[:60] if text else "node"


def normalize(v):
    if not isinstance(v, str):
        return ""
    return v.strip()


def is_valid(v):
    # мягкая проверка (ВАЖНО — не убивает данные)
    return isinstance(v, str) and "vless://" in v


# ─────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────

def fetch_json():
    r = requests.get(URL_JSON, timeout=30)
    r.raise_for_status()
    return r.json()


def extract_json(data):
    result = []
    if not isinstance(data, dict):
        return result

    for _, v in data.items():
        if isinstance(v, dict):
            for k in ["best", "top10", "top5", "top20", "all"]:
                val = v.get(k)
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


# ─────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────

def parse_vless_uri(uri):
    try:
        rest = uri[len("vless://"):]

        at_pos = rest.find("@")
        if at_pos == -1:
            return None

        uuid = rest[:at_pos]
        rest = rest[at_pos + 1:]

        # host
        if rest.startswith("["):
            b = rest.find("]")
            host = rest[1:b]
            rest = rest[b + 1:]
            if rest.startswith(":"):
                rest = rest[1:]
        else:
            host, rest = rest.split(":", 1)

        port = int(rest.split("?")[0].split("#")[0])

        # fragment (name)
        name = ""
        if "#" in uri:
            name = uri.split("#")[-1]

        return {
            "uuid": uuid,
            "host": host,
            "port": port,
            "name": safe_name(name or host),
            "raw": uri
        }

    except:
        return None


# ─────────────────────────────────────────────
# CLASH CONVERTER
# ─────────────────────────────────────────────

def to_proxy(p):
    return {
        "name": p["name"],
        "type": "vless",
        "server": p["host"],
        "port": p["port"],
        "uuid": p["uuid"],
        "udp": True,
        "tls": False,
        "network": "tcp"
    }


# ─────────────────────────────────────────────
# GENERATOR
# ─────────────────────────────────────────────

def generate(vless_list):
    proxies = []
    names = []

    for v in vless_list:
        p = parse_vless_uri(v)
        if not p:
            continue

        proxy = to_proxy(p)
        proxies.append(proxy)
        names.append(proxy["name"])

    # защита от пустого списка
    if not proxies:
        print("WARNING: empty proxy list, fallback to raw input")
        for v in vless_list[:20]:
            proxies.append({
                "name": "fallback",
                "type": "vless",
                "server": "127.0.0.1",
                "port": 443,
                "uuid": "00000000-0000-0000-0000-000000000000"
            })
            names.append("fallback")

    names = list(dict.fromkeys(names))

    config = {
        "mixed-port": 7890,
        "mode": "rule",
        "ipv6": False,

        "proxies": proxies,

        "proxy-groups": [
            {
                "name": "AUTO",
                "type": "url-test",
                "proxies": names,
                "url": "https://api.telegram.org",
                "interval": 300
            },
            {
                "name": "SELECT",
                "type": "select",
                "proxies": names
            },
            {
                "name": "FINAL",
                "type": "select",
                "proxies": ["AUTO", "SELECT"]
            }
        ],

        "rules": [
            "MATCH,FINAL"
        ]
    }

    with open("clash_vless.yaml", "w", encoding="utf-8") as f:
        f.write(f"# generated {datetime.now(timezone.utc)}\n\n")
        yaml.safe_dump(
            config,
            f,
            allow_unicode=True,
            sort_keys=False
        )

    print("OK: clash_vless.yaml generated")


# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

def main():
    all_vless = []

    try:
        j = fetch_json()
        all_vless += extract_json(j)
    except:
        pass

    all_vless += fetch_html()

    # мягкая нормализация
    cleaned = [normalize(v) for v in all_vless if v]

    # убираем дубли
    unique = list(dict.fromkeys(cleaned))

    print("RAW:", len(unique))

    # мягкий фильтр (НЕ УБИВАЕМ ВСЁ)
    filtered = []

    for v in unique:
        if is_valid(v):
            parsed = parse_vless_uri(v)
            if parsed:
                filtered.append(v)

    # fallback защита
    if not filtered:
        print("WARNING: fallback activated")
        filtered = unique

    print("FINAL:", len(filtered))

    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        f.write(f"# updated {datetime.now(timezone.utc)}\n")
        for v in filtered:
            f.write(v + "\n")

    generate(filtered)


if __name__ == "__main__":
    main()
