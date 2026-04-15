import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# 🔹 텔레그램 설정
TOKEN = "여기에_토큰"
CHAT_ID = "7543066255"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)

# 🔹 웹서버 (Render용)
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    port = 10000
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

# 🔥 서버 먼저 실행 (중요)
threading.Thread(target=run_server).start()

# 🔹 코인 리스트
url = "https://api.upbit.com/v1/market/all"
data = requests.get(url).json()
krw_coins = [coin['market'] for coin in data if coin['market'].startswith("KRW-")]

# 🔹 변수들
previous_prices = {}
previous_volumes = {}
accumulation_count = {}
trend_count = {}
alerted_time = {}

btc_prev_price = None
btc_trend = 0

while True:
    try:
        btc_data = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": "KRW-BTC"}
        ).json()[0]
    except:
        print("⚠️ BTC 실패")
        time.sleep(5)
        continue

    btc_price = btc_data['trade_price']

    if btc_prev_price:
        btc_change = ((btc_price - btc_prev_price) / btc_prev_price) * 100
        btc_trend = btc_trend + 1 if btc_change > 0 else 0

    btc_prev_price = btc_price

    try:
        prices = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": ",".join(krw_coins)}
        ).json()
    except:
        print("⚠️ 업비트 실패")
        time.sleep(5)
        continue

    for coin in prices:
        name = coin['market']
        current_price = coin['trade_price']
        volume = coin['acc_trade_volume_24h']

        if name not in previous_prices:
            previous_prices[name] = current_price
            previous_volumes[name] = volume
            accumulation_count[name] = 0
            trend_count[name] = 0
            continue

        old_price = previous_prices[name]
        old_volume = previous_volumes[name]

        change = ((current_price - old_price) / old_price) * 100
        volume_change = (volume - old_volume) / old_volume if old_volume > 0 else 0

        trend_count[name] = trend_count[name] + 1 if change > 0.5 else 0
        accumulation_count[name] = accumulation_count[name] + 1 if abs(change) < 1 and volume_change > 1 else 0

        if (
            accumulation_count[name] >= 3
            and trend_count[name] >= 2
            and volume_change > 2
            and btc_trend >= 2
        ):
            now = time.time()

            if name not in alerted_time or now - alerted_time[name] > 300:
                msg = f"🚨 {name} 돌파! {change:.2f}%"
                print(msg)
                send_telegram(msg)

                accumulation_count[name] = 0
                trend_count[name] = 0
                alerted_time[name] = now

        previous_prices[name] = current_price
        previous_volumes[name] = volume

    time.sleep(10)
