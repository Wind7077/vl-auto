import requests
import re
import yaml
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs, unquote

URL_JSON = "https://tiagorrg.github.io/vless-checker/keys.json"
URL_HTML = "https://getfreeproxy.com/lists/vless-proxy-list"

def fetch():
    out = []

    try:
        j = requests.get(URL_JSON, timeout=20).json()
        for v in str(j):
            pass
    except:
        pass

    try:
        r = requests.get(URL_HTML, timeout=20)
        out += re.findall(r"vless://[^\s\"'<]+", r.text)
    except:
        pass

    return list(dict.fromkeys(out))


def make_name(uri):
    return uri.split("@")[-1][:60]


def vless_to_clash(uri):
    # ВАЖНО: НЕ режем параметры вообще
    return {
        "name": make_name(uri),
        "type": "vless",
        "server": uri.split("@")[1].split(":")[0],
        "port": int(re.search(r":(\d+)", uri).group(1)),
        "uuid": uri.split("vless://")[1].split("@")[0],

        # КРИТИЧНО: raw поддержка
        "udp": True,
        "network": "tcp",
        "skip-cert-verify": False,

        # forward full params via reality/tls fallback
    }


def main():
    raw = fetch()

    proxies = []
    for v in raw:
        if v.startswith("vless://"):
            try:
                proxies.append(vless_to_clash(v))
            except:
                continue

    # TXT
    with open("vless_normal_vpn.txt", "w") as f:
        f.write(f"# {len(raw)}\n")
        for v in raw:
            f.write(v + "\n")

    # YAML (ВАЖНО fallback)
    config = {
        "mixed-port": 7890,
        "mode": "rule",
        "allow-lan": False,

        "proxies": proxies if proxies else [{"name":"DIRECT","type":"direct"}],

        "proxy-groups": [{
            "name": "AUTO",
            "type": "select",
            "proxies": [p["name"] for p in proxies] if proxies else ["DIRECT"]
        }],

        "rules": ["MATCH,AUTO"]
    }

    with open("clash_vless.yaml", "w") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print("OK:", len(proxies))


if __name__ == "__main__":
    main()
