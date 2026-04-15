import re
import yaml
from datetime import datetime

INPUT_FILE = "vless_normal_vpn.txt"
OUTPUT_FILE = "config.yaml"

VLESS_REGEX = re.compile(
    r"vless://(?P<uuid>[^@]+)@(?P<server>[^:]+):(?P<port>\d+)"
)

def parse_vless_lines(text: str):
    proxies = []

    for line in text.splitlines():
        line = line.strip()
        if not line or not line.startswith("vless://"):
            continue

        match = VLESS_REGEX.search(line)
        if not match:
            continue

        proxies.append({
            "name": line.split("@")[1][:40],
            "type": "vless",
            "server": match.group("server"),
            "port": int(match.group("port")),
            "uuid": match.group("uuid"),
            "udp": True,
            "tls": False,
            "network": "tcp"
        })

    return proxies


def build_yaml(proxies):
    config = {
        "mixed-port": 7890,
        "mode": "rule",
        "ipv6": False,
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "AUTO",
                "type": "url-test",
                "proxies": [p["name"] for p in proxies],
                "url": "https://api.telegram.org",
                "interval": 300
            },
            {
                "name": "SELECT",
                "type": "select",
                "proxies": [p["name"] for p in proxies]
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

    return config


def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            raw = f.read()

        proxies = parse_vless_lines(raw)

        print(f"[INFO] parsed proxies: {len(proxies)}")

        if not proxies:
            print("[ERROR] no proxies parsed -> STOP")
            return

        yaml_data = build_yaml(proxies)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("# generated " + str(datetime.utcnow()) + "\n\n")
            yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False)

        print("[OK] YAML generated")

    except Exception as e:
        print("[FATAL ERROR]", str(e))


if __name__ == "__main__":
    main()
