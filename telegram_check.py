import subprocess
import json
import tempfile
import time
import requests
import os

INPUT = "vless_normal_vpn.txt"
OUTPUT = "vless_normal_vpn.txt"

TEST_URL = "https://api.telegram.org"
TEST_TIMEOUT = 10
WAIT = 2.5


def clean(v: str) -> str:
    if not isinstance(v, str):
        return ""
    v = v.strip()
    if not v.startswith("vless://"):
        return ""
    if "@" not in v or ":" not in v:
        return ""
    return v


def parse_vless(vless_uri):
    try:
        rest = vless_uri[len("vless://"):]
        uuid, rest = rest.split("@", 1)

        if rest.startswith("["):
            b = rest.find("]")
            host = rest[1:b]
            rest = rest[b + 2:]
        else:
            host, rest = rest.split(":", 1)

        port = int(rest.split("?")[0].split("#")[0])

        return {
            "type": "vless",
            "tag": "proxy",
            "server": host,
            "server_port": port,
            "uuid": uuid,
        }
    except:
        return None


def build_config(vless):
    outbound = parse_vless(vless)

    return {
        "log": {"level": "error"},
        "dns": {"strategy": "ipv4_only"},
        "inbounds": [{
            "type": "socks",
            "listen": "127.0.0.1",
            "listen_port": 1080
        }],
        "outbounds": [
            outbound,
            {"type": "direct"},
        ],
        "route": {"final": "proxy"},
    }


def check(vless):
    cfg = build_config(vless)
    if not cfg:
        return False

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        json.dump(cfg, f)
        path = f.name

    p = None
    try:
        p = subprocess.Popen(
            ["sing-box", "run", "-c", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        time.sleep(WAIT)

        r = requests.get(
            TEST_URL,
            proxies={
                "http": "socks5h://127.0.0.1:1080",
                "https": "socks5h://127.0.0.1:1080",
            },
            timeout=TEST_TIMEOUT
        )

        return r.status_code in (200, 401)

    except:
        return False

    finally:
        if p:
            p.kill()
        try:
            os.remove(path)
        except:
            pass


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        vless_list = [clean(x) for x in f]

    vless_list = list(dict.fromkeys([v for v in vless_list if v]))

    good = []

    for v in vless_list:
        if check(v):
            good.append(v)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("# clean list\n")
        for v in good:
            f.write(v + "\n")

    print("OK:", len(good))


if __name__ == "__main__":
    main()
