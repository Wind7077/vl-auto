import re
import socket

VLESS_FILE = "vless_normal_vpn.txt"
OUTPUT_FILE = "ain.txt"
TIMEOUT = 5

def parse_host_port(uri):
    m = re.match(r'vless://[^@]+@([^:]+):(\d+)', uri.strip())
    if not m:
        return None, None
    return m.group(1), int(m.group(2))

def is_good(uri):
    # исключаем encoded мусор в sni
    if "%3A" in uri or "%3a" in uri:
        return False
    # только reality или tls
    if "security=reality" not in uri and "security=tls" not in uri:
        return False
    # исключаем российские серверы
    if "Russia" in uri or "RU%5D" in uri:
        return False
    return True

def is_reachable(host, port):
    try:
        ip = socket.gethostbyname(host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"  Error {host}:{port} -> {e}")
        return False

def main():
    with open(VLESS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    candidates = []
    for line in lines:
        line = line.strip()
        if line.startswith("vless://") and is_good(line):
            candidates.append(line)

    print(f"Candidates after filter: {len(candidates)}")

    if not candidates:
        print("No candidates found!")
        return

    best = None
    for uri in candidates:
        host, port = parse_host_port(uri)
        if not host:
            continue
        print(f"Checking {host}:{port} ...")
        if is_reachable(host, port):
            print(f"  ✓ ALIVE -> selected")
            best = uri
            break
        else:
            print(f"  ✗ dead")

    if not best:
        print("No alive vless found! Using first candidate.")
        best = candidates[0]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(best + "\n")

    print(f"Written to {OUTPUT_FILE}")
    print(f"Selected: {best[:100]}...")

if __name__ == "__main__":
    main()
