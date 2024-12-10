import pandas as pd
from datetime import datetime, timedelta
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments

api_token = ""
client = API(access_token=api_token, environment="")
instrument = "USD_JPY"

start_date = datetime(2024, 7, 2)
end_date = datetime(2024, 7, 11)

start_time = datetime.now()

# データを格納するための空リスト
data = []

current_date = start_date
while current_date < end_date:
    next_date = current_date + timedelta(days=3)
    if next_date > end_date:
        next_date = end_date
    
    # 現在の進捗を表示
    elapsed_days = (current_date - start_date).days
    print(f"開始から{elapsed_days}日経過しました。")
    
    # 現在時刻と開始時刻から経過時間（分）を計算
    elapsed_time = datetime.now() - start_time

    elapsed_seconds = int(elapsed_time.total_seconds())  # 経過時間を秒単位で計算し、整数に変換
    print(f"開始から{elapsed_seconds}秒経過しました。")  # 秒単位で経過時間を表示

    params = {
        "granularity": "M3",
        "price": "BAM",  # BidとAskのデータを取得
        "from": current_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "to": next_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }

    r = instruments.InstrumentsCandles(instrument=instrument, params=params)
    resp = client.request(r)
    
    # 次のループのために現在の日付を更新
    current_date = next_date + timedelta(seconds=1)
    
    if 'candles' in resp:
        for candle in resp['candles']:
            if candle['complete']:
                row = {
                    'Time': pd.to_datetime(candle['time']),
                    'Mid_Open': float(candle['mid']['o']) if 'mid' in candle else None,
                    'Mid_High': float(candle['mid']['h']) if 'mid' in candle else None,
                    'Mid_Low': float(candle['mid']['l']) if 'mid' in candle else None,
                    'Mid_Close': float(candle['mid']['c']) if 'mid' in candle else None,
                    'Ask_Open': float(candle['ask']['o']) if 'ask' in candle else None,
                    'Ask_High': float(candle['ask']['h']) if 'ask' in candle else None,
                    'Ask_Low': float(candle['ask']['l']) if 'ask' in candle else None,
                    'Ask_Close': float(candle['ask']['c']) if 'ask' in candle else None,
                    'Bid_Open': float(candle['bid']['o']) if 'bid' in candle else None,
                    'Bid_High': float(candle['bid']['h']) if 'bid' in candle else None,
                    'Bid_Low': float(candle['bid']['l']) if 'bid' in candle else None,
                    'Bid_Close': float(candle['bid']['c']) if 'bid' in candle else None,
                    'Volume': candle['volume'],
                }
                data.append(row)
    
    # 次のループのために現在の日付を更新
    current_date = next_date + timedelta(seconds=1)

# リストからDataFrameを作成
df_full = pd.DataFrame(data)
df_full.set_index('Time', inplace=True)
df_full = df_full[df_full.index.dayofweek < 5]

print(df_full.head(10))
print("---------")
print(df_full.tail(10))

# CSVに保存
df_full.to_csv('test_USD_JPY_M3_all_20240702-0712.csv')