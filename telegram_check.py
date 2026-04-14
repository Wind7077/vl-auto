import subprocess
import json
import tempfile
import time
import requests
import os

INPUT = "vless_normal_vpn.txt"
TEST_URL = "https://api.telegram.org"


def parse_vless(vless):
    # simple parser for sing-box
    import re

    host = vless.split("@")[1].split(":")[0]
    port = int(vless.split(":")[1].split("?")[0])
    uuid = vless.split("vless://")[1].split("@")[0]

    sni = ""
    m = re.search(r"sni=([^&]+)", vless)
    if m:
        sni = m.group(1)

    return {
        "type": "vless",
        "tag": "proxy",
        "server": host,
        "server_port": port,
        "uuid": uuid,
        "tls": {
            "enabled": True,
            "server_name": sni,
            "utls": {"enabled": True, "fingerprint": "chrome"}
        }
    }


def build_config(vless):
    return {
        "log": {"level": "error"},
        "inbounds": [
            {
                "type": "socks",
                "listen": "127.0.0.1",
                "listen_port": 1080
            }
        ],
        "outbounds": [
            parse_vless(vless),
            {"type": "direct"}
        ],
        "route": {"final": "proxy"}
    }


def check(vless):
    cfg = build_config(vless)

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

        time.sleep(2)

        r = requests.get(
            TEST_URL,
            proxies={
                "http": "socks5h://127.0.0.1:1080",
                "https": "socks5h://127.0.0.1:1080"
            },
            timeout=8
        )

        return r.status_code == 200

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
        vless_list = [x.strip() for x in f if x.startswith("vless://")]

    good = []

    print("TESTING:", len(vless_list))

    for i, v in enumerate(vless_list):
        print(i + 1, "/", len(vless_list))
        if check(v):
            good.append(v)

    # overwrite SAME FILE
    with open(INPUT, "w", encoding="utf-8") as f:
        f.write("# telegram-ok only\n")
        for v in good:
            f.write(v + "\n")

    print("GOOD:", len(good))


if __name__ == "__main__":
    main()
