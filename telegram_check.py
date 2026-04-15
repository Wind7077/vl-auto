import subprocess
import json
import tempfile
import time
import requests
import os
from urllib.parse import unquote
from merge_vless import parse_vless, vless_to_proxy, generate_yaml

INPUT = "vless_normal_vpn.txt"
OUTPUT = "vless_checked.txt"

TEST_URL = "https://api.telegram.org"
SINGBOX_STARTUP_WAIT = 2.5

def build_config(vless):
    p = parse_vless(vless)

    return {
        "log": {"level": "error"},
        "inbounds": [{
            "type": "socks",
            "listen": "127.0.0.1",
            "listen_port": 1080
        }],
        "outbounds": [{
            "type": "vless",
            "tag": "proxy",
            "server": p["host"],
            "server_port": p["port"],
            "uuid": p["uuid"],
        }],
        "route": {"final": "proxy"}
    }

def check(vless):
    try:
        cfg = build_config(vless)
    except:
        return False

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(cfg, f)
        path = f.name

    p = None
    try:
        p = subprocess.Popen(["sing-box", "run", "-c", path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        time.sleep(SINGBOX_STARTUP_WAIT)

        r = requests.get(TEST_URL, proxies={
            "http": "socks5h://127.0.0.1:1080",
            "https": "socks5h://127.0.0.1:1080"
        }, timeout=10)

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
        vless_list = [x.strip() for x in f if x.startswith("vless://")]

    good = []

    for v in vless_list:
        if check(v):
            good.append(v)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("# checked\n")
        for v in good:
            f.write(v + "\n")

    try:
        parsed = [vless_to_proxy(parse_vless(v)) for v in good if parse_vless(v)]
        generate_yaml(parsed, "clash_vless.yaml")
    except:
        pass

if __name__ == "__main__":
    main()
