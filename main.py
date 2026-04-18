import requests
import time
import csv
import os
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

# 🔹 CSV 파일 준비
file_name = "trade_log.csv"
if not os.path.exists(file_name):
    with open(file_name, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["시간", "코인", "진입가", "최고%", "최저%"])

# 🔹 코인 리스트
data = requests.get("https://api.upbit.com/v1/market/all").json()
krw_coins = [c['market'] for c in data if c['market'].startswith("KRW-")]

previous_prices = {}
trend_count = {}
alerted_time = {}

# 🔥 가상 매매 저장
active_trades = {}

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

        # 🔥 진짜 급등 감지
        if change > 1.0 and volume > 50000 and trend_count[name] >= 2:
            now = time.time()

            if name not in alerted_time or now - alerted_time[name] > 300:
                msg = f"🚀 급등 {name} {change:.2f}%"
                print(msg)
                send_telegram(msg)

                # 🔥 가상 매수 시작
                active_trades[name] = {
                    "entry": price,
                    "max": price,
                    "min": price,
                    "time": now
                }

                alerted_time[name] = now

        # 🔥 진행 중인 거래 업데이트
        if name in active_trades:
            trade = active_trades[name]

            if price > trade["max"]:
                trade["max"] = price
            if price < trade["min"]:
                trade["min"] = price

            # 🔥 5분 후 결과 기록
            if time.time() - trade["time"] > 300:
                entry = trade["entry"]
                max_p = trade["max"]
                min_p = trade["min"]

                max_profit = (max_p - entry) / entry * 100
                min_profit = (min_p - entry) / entry * 100

                print(f"{name} 결과: 최고 {max_profit:.2f}% / 최저 {min_profit:.2f}%")

                # 🔥 CSV 저장
                with open(file_name, mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                        name,
                        entry,
                        round(max_profit, 2),
                        round(min_profit, 2)
                    ])

                del active_trades[name]

        previous_prices[name] = price

    time.sleep(10)
