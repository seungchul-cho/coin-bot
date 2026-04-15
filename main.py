import requests
import time

# 🔹 텔레그램 설정
TOKEN = "8618774145:AAEEgEAgn4EGbnXLEOoeODiMEPevHa3leZo"
CHAT_ID = "7543066255"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)

# 🔹 코인 리스트 가져오기
url = "https://api.upbit.com/v1/market/all"
data = requests.get(url).json()

krw_coins = [coin['market'] for coin in data if coin['market'].startswith("KRW-")]

# 🔹 저장용 변수들
previous_prices = {}
previous_volumes = {}
accumulation_count = {}
trend_count = {}
alerted_time = {}

# 🔹 BTC 변수
btc_prev_price = None
btc_trend = 0

while True:
    # 🔹 BTC 데이터 (에러 방지)
    try:
        btc_data = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": "KRW-BTC"}
        ).json()[0]
    except:
        print("⚠️ BTC 데이터 실패")
        time.sleep(5)
        continue

    btc_price = btc_data['trade_price']

    if btc_prev_price is not None:
        btc_change = ((btc_price - btc_prev_price) / btc_prev_price) * 100

        if btc_change > 0:
            btc_trend += 1
        else:
            btc_trend = 0

    btc_prev_price = btc_price

    # 🔹 코인 데이터 (에러 방지)
    try:
        response = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": ",".join(krw_coins)}
        )
        prices = response.json()
    except:
        print("⚠️ 업비트 연결 실패... 재시도")
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

        if change > 0.5:
            trend_count[name] += 1
        else:
            trend_count[name] = 0

        if abs(change) < 1 and volume_change > 1:
            accumulation_count[name] += 1
        else:
            accumulation_count[name] = 0

        if (
            accumulation_count[name] >= 3
            and trend_count[name] >= 2
            and volume_change > 2
            and btc_trend >= 2
        ):
            now = time.time()

            if name not in alerted_time or now - alerted_time[name] > 300:
                msg = f"""
🚨 돌파 감지 (고래 움직임)

코인: {name}
가격 상승: {change:.2f}%
매집 횟수: {accumulation_count[name]}
BTC 흐름: 상승 중

👉 터지기 시작 구간
"""
                print(msg)
                send_telegram(msg)

                accumulation_count[name] = 0
                trend_count[name] = 0
                alerted_time[name] = now

        previous_prices[name] = current_price
        previous_volumes[name] = volume

    time.sleep(10)