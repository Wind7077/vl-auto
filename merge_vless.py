import requests
import re
import ipaddress
import socket
import yaml
from datetime import datetime, timezone
from urllib.parse import unquote

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"


def safe_text(s: str) -> str:
    """Жёсткая очистка строк для YAML/Clash"""
    if not isinstance(s, str):
        return ""
    s = unquote(s)
    s = s.replace("\n", " ").replace("\r", " ")
    s = s.replace(":", "-")        # 💣 убирает YAML crash
    s = s.replace("#", "-")
    s = s.strip()
    return s[:60]


def parse_vless_uri(uri):
    try:
        rest = uri[len("vless://"):]

        at_pos = rest.find("@")
        if at_pos == -1:
            return None

        uuid = rest[:at_pos]
        rest = rest[at_pos + 1:]

        if rest.startswith("["):
            b = rest.find("]")
            host = rest[1:b]
            rest = rest[b + 1:]
            if rest.startswith(":"):
                rest = rest[1:]
        else:
            host, rest = rest.split(":", 1)

        port = int(rest.split("?")[0].split("#")[0])

        params = {}
        q_pos = rest.find("?")
        fragment = ""

        if q_pos != -1:
            q = rest[q_pos + 1:]
            if "#" in q:
                q, fragment = q.split("#", 1)

            for part in q.split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k] = unquote(v)

        name = safe_text(fragment or f"{host}:{port}")

        return {
            "uuid": uuid,
            "host": host,
            "port": port,
            "params": params,
            "name": name,
        }

    except Exception:
        return None


def vless_to_clash_proxy(p):
    params = p["params"]

    proxy = {
        "name": p["name"],  # 💣 уже очищено
        "type": "vless",
        "server": p["host"],
        "port": p["port"],
        "uuid": p["uuid"],
        "udp": True,
    }

    security = params.get("security", "none")

    if security in ("tls", "reality", "xtls"):
        proxy["tls"] = True
        proxy["servername"] = safe_text(params.get("sni", p["host"]))
        proxy["client-fingerprint"] = params.get("fp", "chrome")

        if security == "reality":
            proxy["reality-opts"] = {
                "public-key": params.get("pbk", ""),
                "short-id": params.get("sid", ""),
            }
    else:
        proxy["tls"] = False

    transport = params.get("type", "tcp")

    if transport == "ws":
        proxy["network"] = "ws"
        proxy["ws-opts"] = {
            "path": params.get("path", "/"),
            "headers": {
                "Host": safe_text(params.get("host", p["host"]))
            }
        }

    elif transport == "grpc":
        proxy["network"] = "grpc"
        proxy["grpc-opts"] = {
            "grpc-service-name": safe_text(params.get("serviceName", ""))
        }

    else:
        proxy["network"] = "tcp"

    return proxy


def generate_clash_yaml(proxies, filename="clash_vless.yaml"):
    clash = []
    names = []

    for v in proxies:
        parsed = parse_vless_uri(v)
        if not parsed:
            continue

        p = vless_to_clash_proxy(parsed)
        clash.append(p)
        names.append(p["name"])

    config = {
        "mixed-port": 7890,
        "mode": "rule",
        "ipv6": False,
        "allow-lan": False,

        "proxies": clash,

        "proxy-groups": [
            {
                "name": "AUTO",
                "type": "url-test",
                "proxies": names,
                "url": "https://api.telegram.org",
                "interval": 300,
            },
            {
                "name": "SELECT",
                "type": "select",
                "proxies": names,
            },
            {
                "name": "MATCH",
                "type": "select",
                "proxies": ["AUTO", "SELECT"],
            }
        ],

        "rules": [
            "MATCH,MATCH"
        ]
    }

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# generated {datetime.now(timezone.utc)}\n\n")
        yaml.safe_dump(
            config,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False
        )

    print(f"OK: {filename} generated")
