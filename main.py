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

# 🔹 웹서버 (Render용)
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
url = "https://api.upbit.com/v1/market/all"
data = requests.get(url).json()
krw_coins = [coin['market'] for coin in data if coin['market'].startswith("KRW-")]

# 🔹 저장 변수
previous_prices = {}
previous_volumes = {}
accumulation_count = {}
trend_count = {}
alerted_time = {}

# 🔹 BTC 변수
btc_prev_price = None
btc_trend = 0

while True:
    # 🔹 BTC 체크
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

    # 🔹 코인 데이터
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

        # 🔥 상승 유지
        trend_count[name] = trend_count[name] + 1 if change > 0.5 else 0

        # 🔥 매집 감지
        if abs(change) < 0.5 and volume_change > 1:
            accumulation_count[name] += 1
        else:
            accumulation_count[name] = 0

        # 🔥 고래 돌파 (강화)
        if (
            accumulation_count[name] >= 1 and
            trend_count[name] >= 0.5 and
            volume_change > 0.5 and
            btc_trend >= 0.5
        ):
            now = time.time()

            if name not in alerted_time or now - alerted_time[name] > 600:
                msg = f"""
🚨 고래 돌파 감지

코인: {name}
상승률: {change:.2f}%
매집: {accumulation_count[name]}회
거래량 증가: {volume_change:.2f}
BTC 흐름: 상승

🔥 진짜 시작 구간
"""
                print(msg)
                send_telegram(msg)

                accumulation_count[name] = 0
                trend_count[name] = 0
                alerted_time[name] = now

        previous_prices[name] = current_price
        previous_volumes[name] = volume

    time.sleep(10)
