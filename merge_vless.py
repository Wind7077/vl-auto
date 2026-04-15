import yaml
from datetime import datetime

INPUT_FILE = "vless_normal_vpn.txt"
OUTPUT_FILE = "config.yaml"


def parse_vless(text):
    proxies = []

    for line in text.splitlines():
        line = line.strip()

        if "vless://" not in line:
            continue

        try:
            # vless://UUID@server:port
            part = line.replace("vless://", "")
            creds, server_part = part.split("@")
            server, port = server_part.split(":")

            proxies.append({
                "name": server[:40],
                "type": "vless",
                "server": server,
                "port": int(port),
                "uuid": creds,
                "udp": True,
                "tls": False,
                "network": "tcp"
            })

        except:
            continue

    return proxies


def build_yaml(proxies):
    names = [p["name"] for p in proxies]

    return {
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
        "rules": ["MATCH,FINAL"]
    }


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = f.read()

    proxies = parse_vless(data)

    print("PARSED:", len(proxies))

    if len(proxies) == 0:
        print("ERROR: no vless found in input file")
        return

    config = build_yaml(proxies)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# generated " + str(datetime.utcnow()) + "\n")
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print("DONE: config.yaml created")


if __name__ == "__main__":
    main()
