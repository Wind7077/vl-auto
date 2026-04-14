import requests
import re

URL = "https://getfreeproxy.com/lists/vless-proxy-list"

def main():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()

    html = r.text

    vless = re.findall(r'vless://[^\s"<]+', html)

    # дедуп локально
    vless = list(dict.fromkeys(vless))

    if not vless:
        print("No HTML VLESS found")
        return

    print("HTML:", len(vless))

    # ВАЖНО: добавляем в существующий файл, а не перезаписываем
    with open("vless_normal_vpn.txt", "a", encoding="utf-8") as f:
        for v in vless:
            f.write(v + "\n")

if __name__ == "__main__":
    main()
