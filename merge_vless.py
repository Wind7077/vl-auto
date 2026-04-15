import yaml
from datetime import datetime, timezone
from urllib.parse import unquote

def safe(s):
    if not isinstance(s, str):
        return ""
    s = unquote(s)
    s = s.replace(":", "-")
    s = s.replace("#", "-")
    s = s.replace("\n", " ")
    return s[:50]


def parse_vless(v):
    try:
        v = v.strip()
        rest = v[8:]
        uuid, rest = rest.split("@", 1)

        if rest.startswith("["):
            b = rest.find("]")
            host = rest[1:b]
            rest = rest[b+2:]
        else:
            host, rest = rest.split(":", 1)

        port = int(rest.split("?")[0].split("#")[0])

        frag = ""
        if "#" in v:
            frag = v.split("#")[-1]

        return {
            "uuid": uuid,
            "host": host,
            "port": port,
            "name": safe(frag or host),
        }
    except:
        return None


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


def generate(vless_list):
    proxies = []
    names = []

    for v in vless_list:
        p = parse_vless(v)
        if not p:
            continue
        pr = to_proxy(p)
        proxies.append(pr)
        names.append(pr["name"])

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
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)

    print("generated")


if __name__ == "__main__":
    import sys
    generate(open("vless_normal_vpn.txt").read().splitlines())
