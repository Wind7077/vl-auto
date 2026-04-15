import re
from urllib.parse import urlparse, parse_qs

INPUT_FILE = "vless_raw.txt"
OUTPUT_FILE = "vless_normal_vpn.txt"


def parse_vless(line: str):
    line = line.strip()

    if not line.startswith("vless://"):
        return None

    try:
        # vless://uuid@host:port?params#name
        parsed = urlparse(line)

        uuid_host = parsed.netloc
        if "@" not in uuid_host:
            return None

        uuid, host_port = uuid_host.split("@", 1)

        if ":" not in host_port:
            return None

        host, port = host_port.split(":")

        qs = parse_qs(parsed.query)

        name = parsed.fragment if parsed.fragment else f"{host}"

        return {
            "name": name,
            "type": "vless",
            "server": host,
            "port": int(port),
            "uuid": uuid,
            "udp": True,
            "tls": False,
            "network": "tcp"
        }

    except Exception:
        return None


def main():
    proxies = []

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("INPUT FILE NOT FOUND")
        return

    for line in lines:
        p = parse_vless(line)
        if p:
            proxies.append(p)

    print(f"Parsed proxies: {len(proxies)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for p in proxies:
            f.write(
                f"{p['name']}|{p['server']}|{p['port']}|{p['uuid']}\n"
            )


if __name__ == "__main__":
    main()
