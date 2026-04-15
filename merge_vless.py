import requests
import re
import socket
import yaml
import ipaddress
import hashlib
from datetime import datetime, timezone
from urllib.parse import unquote

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"


# ───────────────────────────── FETCH ─────────────────────────────

def fetch_json():
    try:
        return requests.get(URL_JSON, timeout=20).json()
    except:
        return {}


def fetch_html():
    try:
        r = requests.get(URL_HTML, timeout=20)
        return re.findall(r"vless://[^\s\"'<]+", r.text)
    except:
        return []


def extract_json(data):
    out = []
    if not isinstance(data, dict):
        return out

    for v in data.values():
        if isinstance(v, dict):
            for k in v.values():
                if isinstance(k, str) and k.startswith("vless://"):
                    out.append(k)
                if isinstance(k, list):
                    for i in k:
                        if isinstance(i, str) and i.startswith("vless://"):
                            out.append(i)
    return out


# ───────────────────────────── PARSE ─────────────────────────────

def parse(vless):
    try:
        s = vless.replace("vless://", "")
        at = s.find("@")
        uuid = s[:at]
        s = s[at+1:]

        if s.startswith("["):
            end = s.find("]")
            host = s[1:end]
            s = s[end+2:]
        else:
            host, s = s.split(":", 1)

        port = int(s.split("?")[0].split("#")[0])

        name = ""
        if "#" in vless:
            name = unquote(vless.split("#")[1])

        return uuid, host, port, name, vless
    except:
        return None


# ───────────────────────────── NETWORK CHECK ─────────────────────────────

def resolve(host):
    try:
        return socket.gethostbyname(host)
    except:
        return None


def is_bad(ip):
    try:
        ip = ipaddress.ip_address(ip)
        return ip.is_private or ip.is_loopback
    except:
        return True


# ───────────────────────────── UNIQUE NAME FIX ─────────────────────────────

def make_unique(name, host, port, used):
    base = name or f"{host}:{port}"
    base = re.sub(r"\s+", " ", base).strip()[:40]

    h = hashlib.md5(f"{host}:{port}:{base}".encode()).hexdigest()[:6]
    final = f"{base}-{h}"

    while final in used:
        h = hashlib.md5(final.encode()).hexdigest()[:4]
        final = f"{base}-{h}"

    used.add(final)
    return final


# ───────────────────────────── PROXY BUILD ─────────────────────────────

def to_proxy(parsed, used_names):
    uuid, host, port, name, raw = parsed

    ip = host if re.match(r"\d+\.\d+\.\d+\.\d+", host) else resolve(host)
    if not ip or is_bad(ip):
        return None

    safe_name = make_unique(name, host, port, used_names)

    return {
        "name": safe_name,
        "type": "vless",
        "server": host,
        "port": port,
        "uuid": uuid,
        "udp": True,
        "tls": True,
        "skip-cert-verify": True,
        "network": "tcp"
    }


# ───────────────────────────── YAML BUILD ─────────────────────────────

def build_yaml(proxies):
    if not proxies:
        print("NO PROXIES -> YAML SKIP")
        return

    names = [p["name"] for p in proxies]

    config = {
        "mixed-port": 7890,
        "mode": "rule",
        "log-level": "info",
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "AUTO",
                "type": "select",
                "proxies": names
            },
            {
                "name": "FAST",
                "type": "url-test",
                "proxies": names,
                "url": "https://www.google.com/generate_204",
                "interval": 300
            }
        ],
        "rules": [
            "MATCH,AUTO"
        ]
    }

    with open("clash_vless.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print("YAML OK:", len(proxies))


# ───────────────────────────── MAIN ─────────────────────────────

def main():
    raw = []

    try:
        raw += extract_json(fetch_json())
    except:
        pass

    raw += fetch_html()

    raw = list(dict.fromkeys(raw))

    proxies = []
    used_names = set()

    for v in raw:
        parsed = parse(v)
        if not parsed:
            continue

        p = to_proxy(parsed, used_names)
        if p:
            proxies.append(p)

    print("VALID PROXIES:", len(proxies))

    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        f.write(f"# updated {datetime.now(timezone.utc)}\n")
        f.write(f"# total {len(raw)}\n")
        for v in raw:
            f.write(v + "\n")

    build_yaml(proxies)


if __name__ == "__main__":
    main()
