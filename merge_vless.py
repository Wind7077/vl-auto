import requests
import re
import ipaddress
import socket
import yaml
import hashlib
from datetime import datetime, timezone
from urllib.parse import unquote

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"


# ─────────────────────────────
# NETWORK FILTERS (мягкие)
# ─────────────────────────────

RUSSIA_IP_RANGES = [
    "5.0.0.0/8",
    "31.0.0.0/8",
    "37.0.0.0/8",
    "77.0.0.0/8",
    "95.0.0.0/8",
]

ANYCAST_RANGES = [
    "1.1.1.0/24",
    "8.8.8.0/24",
    "104.16.0.0/13",
    "172.64.0.0/13",
]


def nets(ranges):
    out = []
    for r in ranges:
        try:
            out.append(ipaddress.ip_network(r))
        except:
            pass
    return out


RUSSIA_NETS = nets(RUSSIA_IP_RANGES)
ANYCAST_NETS = nets(ANYCAST_RANGES)


def ip_in(ip, nets_):
    try:
        ip = ipaddress.ip_address(ip)
        return any(ip in n for n in nets_)
    except:
        return False


def resolve(host):
    try:
        return socket.gethostbyname(host)
    except:
        return host


# ─────────────────────────────
# FETCH
# ─────────────────────────────

def fetch_json():
    return requests.get(URL_JSON, timeout=30).json()


def fetch_html():
    try:
        r = requests.get(URL_HTML, timeout=30)
        return re.findall(r'vless://[^\s"<]+', r.text)
    except:
        return []


def extract_json(data):
    out = []
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, dict):
                for k in ["best", "top10", "all"]:
                    if k in v and isinstance(v[k], list):
                        out += [i for i in v[k] if isinstance(i, str)]
    return [x for x in out if x.startswith("vless://")]


# ─────────────────────────────
# PARSER
# ─────────────────────────────

def parse(v):
    try:
        v = v.replace("vless://", "")
        uuid, rest = v.split("@", 1)

        if rest.startswith("["):
            host = rest[1:rest.find("]")]
            rest = rest[rest.find("]") + 2:]
        else:
            host, rest = rest.split(":", 1)

        port = int(rest.split("?")[0].split("#")[0])

        params = {}
        if "?" in rest:
            q = rest.split("?")[1]
            for p in q.split("&"):
                if "=" in p:
                    k, val = p.split("=", 1)
                    params[k] = unquote(val)

        return {
            "uuid": uuid,
            "host": host,
            "port": port,
            "params": params,
            "raw": v
        }
    except:
        return None


# ─────────────────────────────
# 🔥 ЖЕЛЕЗНЫЕ УНИКАЛЬНЫЕ ИМЕНА
# ─────────────────────────────

def make_name(p, i):
    raw = f"{p['host']}:{p['port']}:{p['uuid']}:{i}"
    h = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"vless-{h}"


# ─────────────────────────────
# PROXY CONVERT
# ─────────────────────────────

def to_proxy(p, name):
    pr = {
        "name": name,
        "type": "vless",
        "server": p["host"],
        "port": p["port"],
        "uuid": p["uuid"],
        "udp": True
    }

    sec = p["params"].get("security", "none")
    if sec in ("tls", "reality"):
        pr["tls"] = True
        pr["servername"] = p["params"].get("sni", p["host"])

    if p["params"].get("type") == "ws":
        pr["network"] = "ws"
        pr["ws-opts"] = {
            "path": p["params"].get("path", "/"),
            "headers": {"Host": p["host"]}
        }

    return pr


# ─────────────────────────────
# YAML SAFE GENERATOR
# ─────────────────────────────

def build_yaml(proxies):
    names = [p["name"] for p in proxies]

    config = {
        "mixed-port": 7890,
        "mode": "rule",
        "allow-lan": False,
        "log-level": "info",

        "proxies": proxies,

        "proxy-groups": [
            {
                "name": "AUTO",
                "type": "url-test",
                "proxies": names if names else ["DIRECT"],
                "url": "https://api.telegram.org",
                "interval": 300
            },
            {
                "name": "MANUAL",
                "type": "select",
                "proxies": ["AUTO"] + names if names else ["DIRECT"]
            }
        ],

        "rules": [
            "MATCH,MANUAL"
        ]
    }

    with open("clash_vless.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print("YAML OK:", len(proxies))


# ─────────────────────────────
# MAIN
# ─────────────────────────────

def main():
    raw = []

    try:
        raw += extract_json(fetch_json())
    except:
        pass

    raw += fetch_html()

    parsed = []
    for v in raw:
        if v.startswith("vless://"):
            p = parse(v)
            if p:
                parsed.append(p)

    # FILTER (мягкий)
    filtered = []
    for p in parsed:
        ip = resolve(p["host"])

        if ip_in(ip, RUSSIA_NETS):
            continue
        if ip_in(ip, ANYCAST_NETS):
            continue

        filtered.append(p)

    # 🔥 УНИКАЛЬНЫЕ ИМЕНА (ГАРАНТИЯ 0 ДУБЛЕЙ)
    proxies = []
    used = set()

    for i, p in enumerate(filtered):
        name = make_name(p, i)

        if name in used:
            continue
        used.add(name)

        proxies.append(to_proxy(p, name))

    # SAFETY CHECK
    names = [p["name"] for p in proxies]
    if len(names) != len(set(names)):
        raise Exception("DUPLICATES STILL EXIST (CRITICAL BUG)")

    # YAML ВСЕГДА
    build_yaml(proxies)

    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        for p in filtered:
            f.write(p["raw"] + "\n")

    print("TXT OK:", len(filtered))


if __name__ == "__main__":
    main()
