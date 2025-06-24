import requests
import re
import urllib.parse

url = "http://127.0.0.1:5000/synthesize"
data = {
    "text": "你好，世界！",
    "voice": "f1",
    "speed": 100,
    "pitch": 100,
    "volume": 100
}

response = requests.post(url, json=data)
if response.status_code == 200:
    cd = response.headers.get("Content-Disposition", "")
    # 优先解析 filename*=
    m = re.search(r"filename\*\=UTF-8''([^;]+)", cd)
    if m:
        filename = urllib.parse.unquote(m.group(1))
    else:
        m = re.search(r'filename="?([^";]+)"?', cd)
        filename = m.group(1) if m else "output.wav"
    with open(filename, "wb") as f:
        f.write(response.content)
    print(f"已保存 {filename}")
else:
    print("请求失败:", response.json())
