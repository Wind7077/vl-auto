import json
import re

VLESS_FILE = "vless_normal_vpn.txt"

WARP = {
    "type": "wireguard",
    "tag": "warp-out",
    "server": "162.159.195.10",
    "server_port": 4198,
    "local_address": [
        "172.16.0.2/32",
        "2606:4700:110:8172:ca5a:f45d:180d:d977/128"
    ],
    "private_key": "eFzBPxgxWksAAI2S84XV9W3YuG2P+PVZhbdvCzDU42w=",
    "peers": [
        {
            "public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
            "allowed_ips": ["0.0.0.0/0", "::/0"],
            "server": "162.159.195.10",
            "server_port": 4198
        }
    ],
    "mtu": 1280,
    "persistent_keepalive_interval": 25
}

def parse_vless(uri, index):
    m = re.match(r'vless://([^@]+)@([^:]+):(\d+)\?([^#]*)(?:#(.*))?', uri.strip())
    if not m:
        return None
    uuid, host, port, params_str, name = m.groups()
    params = dict(p.split('=', 1) for p in params_str.split('&') if '=' in p)

    outbound = {
        "type": "vless",
        "tag": f"vless-{index:02d}",
        "server": host,
        "server_port": int(port),
        "uuid": uuid,
        "packet_encoding": "xudp"
    }

    flow = params.get("flow", "")
    if flow:
        outbound["flow"] = flow

    security = params.get("security", "")
    if security == "reality":
        outbound["tls"] = {
            "enabled": True,
            "server_name": params.get("sni", host),
            "utls": {
                "enabled": True,
                "fingerprint": params.get("fp", "chrome")
            },
            "reality": {
                "enabled": True,
                "public_key": params.get("pbk", ""),
                "short_id": params.get("sid", "")
            }
        }
    elif security == "tls":
        outbound["tls"] = {
            "enabled": True,
            "server_name": params.get("sni", host),
            "utls": {
                "enabled": True,
                "fingerprint": params.get("fp", "chrome")
            }
        }

    return outbound

def is_good(v):
    tls = v.get("tls", {})
    if not tls:
        return False
    sni = tls.get("server_name", "")
    if "%" in sni:
        return False
    if len(sni) < 3:
        return False
    return True

def main():
    with open(VLESS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    vless_list = []
    for line in lines:
        line = line.strip()
        if line.startswith("vless://"):
            parsed = parse_vless(line, len(vless_list))
            if parsed:
                vless_list.append(parsed)

    if not vless_list:
        print("No vless found!")
        return

    print(f"Total parsed: {len(vless_list)}")

    # фильтруем мусор
    good = [v for v in vless_list if is_good(v)]
    print(f"Good vless: {len(good)}")

    # приоритет — reality серверы
    reality = [v for v in good if v.get("tls", {}).get("reality")]
    other = [v for v in good if not v.get("tls", {}).get("reality")]
    print(f"Reality: {len(reality)}, Other TLS: {len(other)}")

    final_list = (reality + other)[:5]

    if not final_list:
        print("No good vless after filtering, using raw list")
        final_list = vless_list[:5]

    # перенумеруем теги чисто
    for i, v in enumerate(final_list):
        v["tag"] = f"vless-{i:02d}"

    print(f"Using {len(final_list)} vless servers:")
    for v in final_list:
        sni = v.get("tls", {}).get("server_name", "no-tls")
        is_reality = "reality" in v.get("tls", {})
        print(f"  {v['tag']} -> {v['server']}:{v['server_port']} sni={sni} reality={is_reality}")

    warp = dict(WARP)
    warp["detour"] = final_list[0]["tag"]

    outbounds = final_list + [warp, {"type": "direct", "tag": "direct"}]

    config = {
        "log": {
            "level": "info",
            "timestamp": True
        },
        "dns": {
            "servers": [
                {
                    "tag": "dns-direct",
                    "address": "8.8.8.8",
                    "detour": "direct"
                }
            ],
            "final": "dns-direct"
        },
        "inbounds": [
            {
                "type": "tun",
                "tag": "tun-in",
                "interface_name": "tun0",
                "inet4_address": "172.19.0.1/30",
                "mtu": 1500,
                "auto_route": True,
                "strict_route": False,
                "sniff": True
            }
        ],
        "outbounds": outbounds,
        "route": {
            "rules": [
                {
                    "ip_cidr": ["162.159.192.0/22"],
                    "outbound": "direct"
                },
                {
                    "ip_cidr": ["8.8.8.8/32"],
                    "outbound": "direct"
                }
            ],
            "final": "warp-out",
            "auto_detect_interface": True
        }
    }

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("config.json updated successfully")

if __name__ == "__main__":
    main()
