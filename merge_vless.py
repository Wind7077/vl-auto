import requests
import re
import ipaddress
import socket
import yaml
from datetime import datetime, timezone
from urllib.parse import unquote

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"


# ─────────────────────────────
# NETWORK FILTERS (оставил как у тебя)
# ─────────────────────────────

RUSSIA_IP_RANGES = [
    "5.3.0.0/16", "5.8.0.0/16", "5.16.0.0/13",
    "31.13.0.0/18", "37.29.0.0/16",
    "77.88.0.0/21", "91.108.4.0/22"
]

ANYCAST_RANGES = [
    "1.1.1.0/24", "8.8.8.0/24",
    "104.16.0.0/13", "172.64.0.0/13"
]


def build_networks(ranges):
    nets = []
    for cidr in ranges:
        try:
            nets.append(ipaddress.ip_network(cidr, strict=False))
        except:
            pass
    return nets


RUSSIA_NETS = build_networks(RUSSIA_IP_RANGES)
ANYCAST_NETS = build_networks(ANYCAST_RANGES)


def resolve_host(host):
    try:
        return socket.getaddrinfo(host, None, socket.AF_INET)[0][4][0]
    except:
        return None


def ip_in(ip, nets):
    try:
        ip = ipaddress.ip_address(ip)
        return any(ip in n for n in nets)
    except:
        return False


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
                    if k in v:
                        val = v[k]
                        if isinstance(val, list):
                            out += [i for i in val if isinstance(i, str)]
                        elif isinstance(val, str):
                            out.append(val)
    return [x for x in out if x.startswith("vless://")]


# ─────────────────────────────
# PARSE
# ─────────────────────────────

def parse_vless(uri):
    try:
        rest = uri.replace("vless://", "")

        uuid, rest = rest.split("@", 1)

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
                    k, v = p.split("=", 1)
                    params[k] = unquote(v)

        name = params.get("sni") or host

        return {
            "uuid": uuid,
            "host": host,
            "port": port,
            "params": params,
            "name": name,
            "raw": uri
        }

    except:
        return None


# ─────────────────────────────
# UNIQUE NAME FIX (ВАЖНО)
# ─────────────────────────────

def make_unique_names(parsed_list):
    used = {}
    result = []

    for i, p in enumerate(parsed_list):
        base = f"{p['host']}:{p['port']}"

        if base not in used:
            used[base] = 0
        used[base] += 1

        uniq = f"{base}-{used[base]}-{p['uuid'][:4]}"
        p["name"] = uniq[:60]
        result.append(p)

    return result


# ─────────────────────────────
# CONVERT
# ─────────────────────────────

def to_proxy(p):
    params = p["params"]

    proxy = {
        "name": p["name"],
        "type": "vless",
        "server": p["host"],
        "port": p["port"],
        "uuid": p["uuid"],
        "udp": True
    }

    if params.get("security") in ["tls", "reality"]:
        proxy["tls"] = True
        proxy["servername"] = params.get("sni", p["host"])

    transport = params.get("type", "tcp")

    if transport == "ws":
        proxy["network"] = "ws"
        proxy["ws-opts"] = {
            "path": params.get("path", "/"),
            "headers": {"Host": params.get("host", p["host"])}
        }

    elif transport == "grpc":
        proxy["network"] = "grpc"
        proxy["grpc-opts"] = {
            "grpc-service-name": params.get("serviceName", "")
        }

    else:
        proxy["network"] = "tcp"

    return proxy


# ─────────────────────────────
# YAML GENERATOR (SAFE)
# ─────────────────────────────

def generate_yaml(proxies):
    names = [p["name"] for p in proxies]

    config = {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",
        "ipv6": False,

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
            p = parse_vless(v)
            if p:
                parsed.append(p)

    # FILTER SAFE (НЕ УБИВАЕМ ВСЁ)
    filtered = []
    for p in parsed:
        ip = resolve_host(p["host"]) or p["host"]

        if ip_in(ip, RUSSIA_NETS):
            continue
        if ip_in(ip, ANYCAST_NETS):
            continue

        filtered.append(p)

    # UNIQUE FIX
    filtered = make_unique_names(filtered)

    proxies = [to_proxy(p) for p in filtered]

    # ВАЖНО: YAML ВСЕГДА ГЕНЕРИРУЕМ
    generate_yaml(proxies)

    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        for p in filtered:
            f.write(p["raw"] + "\n")

    print("TXT OK:", len(filtered))


if __name__ == "__main__":
    main()
