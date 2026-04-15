import requests
import re
import yaml
import hashlib
from datetime import datetime, timezone

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"

def fetch_json():
    try:
        return requests.get(URL_JSON, timeout=20).json()
    except:
        return {}

def extract_json(data):
    out = []
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, dict):
                for k in ["best", "top10", "top5", "all"]:
                    x = v.get(k)
                    if isinstance(x, list):
                        out += x
                    elif isinstance(x, str):
                        out.append(x)
    return [i for i in out if isinstance(i, str) and i.startswith("vless://")]

def fetch_html():
    try:
        r = requests.get(URL_HTML, timeout=20)
        return re.findall(r"vless://[^\s\"'<]+", r.text)
    except:
        return []

def parse_vless(uri):
    try:
        rest = uri[8:]
        at = rest.find("@")
        uuid = rest[:at]
        rest = rest[at+1:]

        if rest.startswith("["):
            host = rest[1:rest.find("]")]
            rest = rest[rest.find("]")+2:]
        else:
            host, rest = rest.split(":", 1)

        port = int(rest.split("?")[0].split("#")[0])

        return uuid, host, port
    except:
        return None

def uniq_name(host, port, uuid):
    base = f"{host}:{port}:{uuid}"
    h = hashlib.md5(base.encode()).hexdigest()[:6]
    return f"{host}:{port}-{h}"

def vless_to_proxy(v):
    uuid, host, port = v
    return {
        "name": uniq_name(host, port, uuid),
        "type": "vless",
        "server": host,
        "port": port,
        "uuid": uuid,
        "udp": True
    }

def write_yaml(proxies, path):
    config = {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",

        "proxies": proxies,

        "proxy-groups": [
            {
                "name": "AUTO",
                "type": "select",
                "proxies": [p["name"] for p in proxies] if proxies else ["DIRECT"]
            }
        ],

        "rules": [
            "MATCH,AUTO"
        ]
    }

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

def main():
    raw = []
    raw += extract_json(fetch_json())
    raw += fetch_html()

    cleaned = list(dict.fromkeys([x for x in raw if isinstance(x, str) and x.startswith("vless://")]))

    parsed = []
    for v in cleaned:
        p = parse_vless(v)
        if p:
            parsed.append(p)

    proxies = [vless_to_proxy(p) for p in parsed]

    # ── ВСЕГДА ПИШЕМ TXT ──
    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        f.write(f"# updated {datetime.now(timezone.utc)}\n")
        f.write(f"# total {len(cleaned)}\n")
        for v in cleaned:
            f.write(v + "\n")

    # ── ГАРАНТИРОВАННЫЙ YAML ──
    write_yaml(proxies, "clash_vless.yaml")

    print("OK:", len(cleaned), "→", len(proxies))

if __name__ == "__main__":
    main()
