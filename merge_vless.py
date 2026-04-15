import requests
import re
import yaml
from datetime import datetime, timezone

URLS = [
    "https://tiagorrg.github.io/vless-checker/keys.json",
    "https://getfreeproxy.com/lists/vless-proxy-list"
]

def fetch_all():
    out = []

    # JSON source
    try:
        j = requests.get(URLS[0], timeout=20).json()
        out += re.findall(r"vless://[^\s\"'<]+", str(j))
    except Exception as e:
        print("JSON FAIL:", e)

    # HTML source
    try:
        r = requests.get(URLS[1], timeout=20)
        out += re.findall(r"vless://[^\s\"'<]+", r.text)
    except Exception as e:
        print("HTML FAIL:", e)

    return list(dict.fromkeys(out))


def safe_name(uri):
    try:
        host = uri.split("@")[1].split(":")[0]
        port = re.search(r":(\d+)", uri).group(1)
        return f"{host}:{port}"
    except:
        return "bad-node"


def build_proxy(uri):
    try:
        host = uri.split("@")[1].split(":")[0]
        port = int(re.search(r":(\d+)", uri).group(1))
        uuid = uri.split("vless://")[1].split("@")[0]

        return {
            "name": safe_name(uri),
            "type": "vless",
            "server": host,
            "port": port,
            "uuid": uuid,
            "udp": True
        }
    except:
        return None


def main():
    raw = fetch_all()

    print("RAW:", len(raw))

    proxies = []
    good = []

    for v in raw:
        if not v.startswith("vless://"):
            continue
        p = build_proxy(v)
        if p:
            proxies.append(p)
            good.append(v)

    # ── GUARANTEE: NEVER EMPTY ──
    if not proxies:
        print("WARNING: empty proxies → fallback DIRECT")
        proxies = [{
            "name": "DIRECT",
            "type": "direct"
        }]

    # TXT ALWAYS WRITE
    with open("vless_normal_vpn.txt", "w", encoding="utf-8") as f:
        f.write(f"# updated {datetime.now(timezone.utc)}\n")
        f.write(f"# total {len(good)}\n")
        for v in good:
            f.write(v + "\n")

    # YAML ALWAYS WRITE
    config = {
        "mixed-port": 7890,
        "mode": "rule",
        "allow-lan": False,

        "proxies": proxies,

        "proxy-groups": [{
            "name": "AUTO",
            "type": "select",
            "proxies": [p["name"] for p in proxies]
        }],

        "rules": ["MATCH,AUTO"]
    }

    with open("clash_vless.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print("OK proxies:", len(proxies))


if __name__ == "__main__":
    main()
