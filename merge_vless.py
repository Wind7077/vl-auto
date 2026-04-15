# merge_vless.py
# stable pipeline fix version

import re
import uuid
from datetime import datetime

INPUT_FILE = "vless_normal_vpn.txt"
OUTPUT_FILE = "output.yaml"

def parse_vless(line: str):
    line = line.strip()
    if not line or not line.startswith("vless://"):
        return None

    try:
        line = line.replace("vless://", "")
        uuid_part, rest = line.split("@", 1)
        server_port, params = rest.split("?", 1) if "?" in rest else (rest, "")

        if ":" in server_port:
            server, port = server_port.split(":")
        else:
            server = server_port
            port = "443"

        return {
            "uuid": uuid_part,
            "server": server,
            "port": int(port),
        }
    except:
        return None


def build_proxy(entry, index):
    return f"""- name: "VLESS-{index}"
  type: vless
  server: {entry['server']}
  port: {entry['port']}
  uuid: {entry['uuid']}
  udp: true
  tls: false
  network: tcp
"""


def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("vless_normal_vpn.txt not found")
        return

    proxies = []
    proxy_names = []

    index = 1

    for line in lines:
        parsed = parse_vless(line)
        if parsed:
            proxies.append(build_proxy(parsed, index))
            proxy_names.append(f"VLESS-{index}")
            index += 1

    if not proxies:
        print("NO VLESS FOUND → STOP")
        return

    yaml = f"""# generated {datetime.utcnow().isoformat()}Z

mixed-port: 7890
mode: rule
ipv6: false

proxies:
{''.join(proxies)}

proxy-groups:
- name: AUTO
  type: url-test
  proxies:
{chr(10).join(['  - ' + n for n in proxy_names])}
  url: http://www.gstatic.com/generate_204
  interval: 300

- name: SELECT
  type: select
  proxies:
{chr(10).join(['  - ' + n for n in proxy_names])}

- name: FINAL
  type: select
  proxies:
  - AUTO
  - SELECT

rules:
- MATCH,FINAL
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(yaml)

    print(f"OK: {len(proxy_names)} proxies generated")


if __name__ == "__main__":
    main()
