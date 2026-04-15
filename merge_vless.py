import requests
import re
import yaml
import hashlib
from datetime import datetime, timezone
from urllib.parse import unquote

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"

def normalize(v):
    return v.strip()

def is_valid(v):
    return isinstance(v, str) and v.startswith("vless://")

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
                        out += [i for i in x if isinstance(i, str)]
                    elif isinstance(x, str):
                        out.append(x)
    return [i for i in out if i.startswith("vless://")]

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
        return {"uuid": uuid, "host": host, "port": port}
    except:
        return None

def make_name(host, port):
    h = hashlib.md5(f"{host}:{port}".encode()).hexdigest()[:6]
    return f"{host}:{port}-{h}"

def vless_to_proxy(p):
    return {
        "name": make_name(p["host"], p["port"]),
        "type": "vless",
        "server": p["host"],
        "port": p["port"],
        "uuid": p["uuid"],
        "udp": True
    }

def generate_yaml(proxies, filename):
    config = {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",
        "proxies": proxies,
        "proxy-groups": [{
            "name": "AUTO",
            "type": "select",
            "proxies": [p["name"] for p in proxies]
        }],
        "rules": ["MATCH,AUTO"]
    }

    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

def main():
    all_vless = []
    all_vless += extract_json(fetch_json())
    all_vless += fetch_html()

    cleaned = list(dict.fromkeys([v.strip() for v in all_vless if is_valid(v)]))

    parsed = []
    for v in cleaned:
        p = parse_vless(v)
        if p:
            parsed.append(p)

    proxies = [vless_to_proxy(p) for p in parsed]

    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        f.write(f"# updated {datetime.now(timezone.utc)}\n")
        f.write(f"# total {len(cleaned)}\n")
        for v in cleaned:
            f.write(v + "\n")

    generate_yaml(proxies, "clash_vless.yaml")

if __name__ == "__main__":
    main()
