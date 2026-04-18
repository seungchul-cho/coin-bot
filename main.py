import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TOKEN = "8618774145:AAEEgEAgn4EGbnXLEOoeODiMEPevHa3leZo"
CHAT_ID = "7543066255"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# 🔹 웹서버
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_server).start()

# 🔹 코인 리스트
data = requests.get("https://api.upbit.com/v1/market/all").json()
krw_coins = [c['market'] for c in data if c['market'].startswith("KRW-")]

previous_prices = {}
trend_count = {}
alerted_time = {}

while True:
    try:
        prices = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": ",".join(krw_coins)}
        ).json()
    except:
        print("⚠️ 오류")
        time.sleep(5)
        continue

    for coin in prices:
        name = coin['market']
        price = coin['trade_price']
        volume = coin['acc_trade_volume_24h']

        if name not in previous_prices:
            previous_prices[name] = price
            trend_count[name] = 0
            continue

        old_price = previous_prices[name]
        change = ((price - old_price) / old_price) * 100

        # 🔥 연속 상승 체크
        if change > 0.3:
            trend_count[name] += 1
        else:
            trend_count[name] = 0

        # 🔥 진짜 급등만
        if change > 1.0 and volume > 50000 and trend_count[name] >= 2:
            now = time.time()

            if name not in alerted_time or now - alerted_time[name] > 300:
                msg = f"🚀 진짜 급등 {name} {change:.2f}%"
                print(msg)
                send_telegram(msg)
                alerted_time[name] = now

        previous_prices[name] = price

    time.sleep(10)
