# 標準ライブラリ
import os  # ファイル削除用
import random
import time
import re  # reモジュールのインポート
import json
import asyncio
from datetime import datetime, timedelta
import traceback

# サードパーティライブラリ
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from dateutil import parser
import pytz
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import joblib
import talib

# 外部ライブラリ
import tweepy
import nest_asyncio
import oandapyV20
from oandapyV20 import API
from oandapyV20.endpoints.accounts import AccountDetails
from oandapyV20.endpoints import instruments, transactions, orders, positions, pricing, trades
from oandapyV20.endpoints.instruments import InstrumentsCandles

# APIキーとトークンの読み込み
with open('twitter_key.json') as f:
    twitter_keys = json.load(f)
# twitter_key.json

# Twitter認証
twitter_client = tweepy.Client(
    bearer_token=twitter_keys['bearer_token'],
    consumer_key=twitter_keys['consumer_key'],
    consumer_secret=twitter_keys['consumer_secret'],
    access_token=twitter_keys['access_token'],
    access_token_secret=twitter_keys['access_token_secret']
)

async def reconnect_oanda(api_client, account_id):
    try:
        # OANDA APIクライアントを再接続
        api_client = API(access_token=access_token, environment="live")
        print("Reconnected to OANDA API")
        # 口座情報の取得テスト
        account_info = api_client.request(AccountDetails(accountID=account_id))
        print("Account details fetched after reconnect:", account_info)
        return api_client
    except Exception as e:
        print(f"Error during OANDA reconnection: {e}")
        return None

def is_weekend_japan_time():
    """土日かどうかを判定（日本時間）"""
    now = datetime.now(pytz.timezone('Asia/Tokyo'))
    if now.weekday() == 5 or now.weekday() == 6:  # 土曜日または日曜日
        return True
    elif now.weekday() == 0 and now.hour < 8:  # 月曜日の8時前
        return True
    return False

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504, 520),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


#AccountManager：口座の資産情報、レバレッジ、使用可能な資金などの管理を担当します。
class AccountManager:
    def __init__(self, api_client, account_id, asset_ratio_leverage=7):
        self.api_client = api_client
        self.positions = []  # 現在のポジションを保持するリスト
        self.account_id = account_id
        self.asset_ratio_leverage = asset_ratio_leverage
        self.trade_order_times = {}  # 各トレードIDに対応する注文時間を保存

    def calculate_nav(self):
        """有効証拠金を計算"""
        account_info = self.fetch_account_info()
        if account_info is None:
            return 0.0
        nav = float(account_info['account']['NAV'])
        return nav
    
    def calculate_margin_used(self):
        """使用されている証拠金を計算"""
        account_info = self.fetch_account_info()
        if account_info is None:
            return 0.0
        margin_used = float(account_info['account']['marginUsed'])
        return margin_used
        
    def close_position(self, trade_id):
        """指定されたトレードIDのポジションをクローズする。トレードが存在しない場合はエラーを処理する。"""
        print(f"Attempting to close trade ID: {trade_id}")
        if trade_id in self.trade_order_times:
            print(f"Closing Trade ID {trade_id}: Order time and initial price details: {self.trade_order_times[trade_id]}")
            del self.trade_order_times[trade_id]  # ポジションをクローズする際、注文時間の記録を削除
        data = {
            "units": "ALL"
        }
        endpoint = trades.TradeClose(accountID=self.account_id, tradeID=trade_id, data=data)
        try:
            response = self.api_client.request(endpoint)
            print(f"Trade {trade_id} closed successfully. Response: {response}")
            self.positions = [pos for pos in self.positions if pos['trade_id'] != trade_id]
            return response
        except Exception as e:
            print(f"Error closing trade {trade_id}: {e}")
            return None
    
    def fetch_account_info(self, retries=3, delay=5):
        if is_weekend_japan_time():
            print("土日はリクエストを行いません。")
            return None
    
        attempt = 0
        while attempt < retries:
            try:
                r = AccountDetails(accountID=self.account_id)
                account_info = self.api_client.request(r)  # リクエストを実行
                return account_info  # 結果を返す
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                attempt += 1
        raise Exception("アカウント情報の取得に失敗しました。最大再試行回数に達しました。")
        
    def calculate_available_margin(self):
        """使用可能なマージン（資金）を計算"""
        account_info = self.fetch_account_info()
        if account_info is None:
            return 0.0
        margin_available = float(account_info['account']['marginAvailable'])
        return margin_available
    
    def calculate_leverage(self):
        """レバレッジを計算"""
        account_info = self.fetch_account_info()
        if account_info is None:
            return 0.0
        nav = float(account_info['account']['NAV'])  # 有効証拠金を取得
        margin_used = float(account_info['account']['marginUsed'])
        print(f"NAV (Net Asset Value): {nav}")
        print(f"Margin Used: {margin_used}")
    
        if nav == 0:
            return 0
        leverage = margin_used / nav * 25
        return leverage
        
    def calculate_new_leverage(self, additional_margin):
        """新規注文後のレバレッジを計算"""
        account_info = self.fetch_account_info()
        if account_info is None:
            return 0.0
        margin_used = float(account_info['account']['marginUsed'])
        balance = float(account_info['account']['balance'])

        if balance == 0:
            return 0.0

        new_leverage = (margin_used + additional_margin) / balance * 25  # レバレッジを20倍にする
        print(f"New Calculated leverage after order: {new_leverage}")

        return new_leverage
       
    def update_positions(self):
        if is_weekend_japan_time():
            print("土日はポジションを更新しません。")
            return
    
        endpoint = positions.OpenPositions(accountID=self.account_id)
        response = self.api_client.request(endpoint)
        current_utc_time = datetime.now(pytz.UTC)
        new_positions = []
    
        valid_trade_ids = set()
        for pos in response.get('positions', []):
            instrument = pos['instrument']
            for side in ['long', 'short']:
                units = pos[side]['units']
                if int(units) != 0:
                    trade_ids = pos[side]['tradeIDs']
                    for trade_id in trade_ids:
                        valid_trade_ids.add(trade_id)
                        if trade_id not in self.trade_order_times:
                            order_time = current_utc_time
                            ask_price, bid_price = self.get_current_prices(instrument)
                            initial_price = ask_price if side == 'long' else bid_price
                            self.trade_order_times[trade_id] = {'order_time': order_time, 'initial_price': initial_price}
                        else:
                            order_time = self.trade_order_times[trade_id]['order_time']
                            initial_price = self.trade_order_times[trade_id]['initial_price']
                        
                        ask_price, bid_price = self.get_current_prices(instrument)
                        current_price = ask_price if side == 'long' else bid_price  # 最新の現在価格を取得
                        time_elapsed = current_utc_time - order_time
                        new_position = {
                            'instrument': instrument,
                            'units': int(units),
                            'side': side,
                            'price': current_price,  # 現在価格を保存
                            'initial_price': initial_price,
                            'trade_id': trade_id,
                            'order_time': order_time,
                            'time_elapsed': time_elapsed
                        }
                        new_positions.append(new_position)
    
        self.positions = new_positions
        self.trade_order_times = {k: v for k, v in self.trade_order_times.items() if k in valid_trade_ids}
    
        print("Updated positions:")
        for pos in self.positions:
            print(pos)

    def get_current_prices(self, instrument):
        params = {"instruments": instrument}
        r = pricing.PricingInfo(accountID=self.account_id, params=params)
        try:
            resp = self.api_client.request(r)
            if "prices" in resp and len(resp["prices"]) > 0:
                prices = resp["prices"][0]
                ask_price = float(prices["asks"][0]["price"])
                bid_price = float(prices["bids"][0]["price"])
                return ask_price, bid_price
            else:
                print(f"Prices not found for instrument: {instrument}")
                return None, None
        except Exception as e:
           print(f"Failed to fetch prices for {instrument}: {e}")
           return None, None
            
    def cleanup_trade_order_times(self):
        """保持する取引データを最新の180件に限定する"""
        current_time = datetime.now(pytz.UTC)
        #print("Current trade order times before cleanup:", self.trade_order_times)  # クリーンアップ前のデータを出力
    
        # 最新180件のtrade_idを保持
        recent_keys = sorted(self.trade_order_times.keys(), key=lambda x: self.trade_order_times[x]['order_time'], reverse=True)[:180]
        keys_to_remove = [key for key in self.trade_order_times if key not in recent_keys]
    
        # 削除するキーを出力
        if keys_to_remove:
            print("Keys to be removed:", keys_to_remove)
        else:
            print("No keys to be removed.")
    
        for key in keys_to_remove:
            #print(f"Removing old trade data for trade_id {key}")
            del self.trade_order_times[key]
    
        #print("Current trade order times after cleanup:", self.trade_order_times)  # クリーンアップ後のデータを出力

class MarketDataFetcher:
    def __init__(self, api_client, instrument="USD_JPY"):
        self.api_client = api_client
        self.instrument = instrument

    def run(self):
        """30秒ごとに最新のデータを取得する"""
        while True:
            now = datetime.now(pytz.UTC)
            if now.second == 0:
                df = self.fetch_latest_data()
                #print("最新データを取得しました。")
                # 必要に応じてdfを処理
            #else:
                #print("待機中...")
                #time.sleep(1)  # 次の分まで待機
                
    def fetch_latest_data(self):
        """直近のデータを取得し、過去75本のデータを保持する"""
        # 直近のデータを取得するためのパラメータ
        params = {
            "granularity": "M3",
            "count": 125,
            "price": "BAM",  # BidとAskのデータを取得
        }

        # APIリクエストを実行
        r = instruments.InstrumentsCandles(instrument=self.instrument, params=params)
        resp = self.api_client.request(r)

        # データをDataFrameに変換
        data = []
        if 'candles' in resp:
            for candle in resp['candles']:
                if candle['complete']:
                    row = {
                        'Time': pd.to_datetime(candle['time']),
                        'Open': float(candle['mid']['o']) if 'mid' in candle else None,
                        'High': float(candle['mid']['h']) if 'mid' in candle else None,
                        'Low': float(candle['mid']['l']) if 'mid' in candle else None,
                        'Close': float(candle['mid']['c']) if 'mid' in candle else None,
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
        
        df = pd.DataFrame(data)
        return df

class FeatureGenerator:
    pred_0 = 0
    pred_1 = 0
    pred_2 = 0
    pred_3 = 0
    def __init__(self, df):
        #print("受け取る。")
        self.df = df
        self.df_feature_value = self.df.copy()
        self.model = None
        
    # 移動平均乖離率の計算
    def calculate_features(self):
        # 短期移動平均線のウィンドウサイズ
        short_term_windows = [3, 5, 8, 10, 12, 15]
        # 長期移動平均線のウィンドウサイズ
        long_term_windows = [30, 35, 40, 45, 50, 60]
        
        # 短期移動平均線を計算
        for window in short_term_windows:
            self.df_feature_value[f'short_ma{window}'] = self.df['Close'].rolling(window=window).mean()

        # 長期移動平均線を計算
        for window in long_term_windows:
            self.df_feature_value[f'long_ma{window}'] = self.df['Close'].rolling(window=window).mean()        # 移動平均の差分（乖離）を計算

        # 短期・長期の移動平均線を計算
        windows = [3, 5, 8, 10, 12, 15, 30, 35, 40, 45, 50, 60]
        short_windows = windows[:6]  # 短期
        long_windows = windows[6:]  # 長期
        self.df['diff_short'] = self.df_feature_value[[f'short_ma{w}' for w in short_windows]].diff(axis=1).iloc[:, -1]
        self.df['diff_long'] = self.df_feature_value[[f'long_ma{w}' for w in long_windows]].diff(axis=1).iloc[:, -1]

        #長短GMMA乖離率の差分
        self.df_feature_value['combined_diff'] = self.df['diff_short'] - self.df['diff_long']
        # 過去のcombined_diffの追加
        combined_diff_shifted = pd.concat([self.df_feature_value['combined_diff'].shift(i).rename(f'combined_diff_{i}') for i in range(1, 15)], axis=1)
        
        # 元のDataFrameと結合
        self.df_feature_value = pd.concat([self.df_feature_value, combined_diff_shifted], axis=1)
        
        # 'Time'列が存在していれば、それを基に'datetime'列を作成
        if 'Time' in self.df.columns:
            self.df_feature_value['datetime'] = pd.to_datetime(self.df['Time'], utc=True)
        else:
            print("'Time'列がデータフレームに存在しません。")
            return  # 'Time'列がない場合はここで処理を終了

        # 年、月、曜日の特徴量を追加
        self.df_feature_value['year'] = self.df_feature_value['datetime'].dt.year
        self.df_feature_value['month'] = self.df_feature_value['datetime'].dt.month
        self.df_feature_value['day_of_week'] = self.df_feature_value['datetime'].dt.dayofweek
        # 欠損値を含む行を削除
        #self.df_feature_value.dropna(inplace=True)
        # インデックスをリセット
        #self.df_feature_value.reset_index(drop=True, inplace=True)
        return self.df_feature_value  # 変更されたDataFrameを返す

    # ラベル付けの提案
    # 0: 価格変動が-0.2以下（価格が下降）
    # 1: 価格変動が-0.2より大きく0.2より小さい（価格があまり変わらない）
    # 2: 価格変動が0.2以上（価格が上昇）            
    def label_price_change(self):
        # 2時間以内の最大値との差分を計算
        self.df_feature_value['max_diff_2h'] = self.df_feature_value['Close'].rolling(window=20).max() - self.df_feature_value['Close'] 

        # 2時間以内の最小値との差分を計算
        self.df_feature_value['min_diff_2h'] = self.df_feature_value['Close'].rolling(window=20).min() - self.df_feature_value['Close']   
        
    def calculate_1m_WilliamsR_and_MACD(self):
        """1分足データに対してウィリアムズ%RとMACDを計算し、df_feature_valueに追加する"""
        length = len(self.df_feature_value.index)  # df_feature_valueの長さを取得
        # ウィリアムズ%Rの計算（結果をdf_feature_valueの長さに合わせる）
        Williams_R_1m = talib.WILLR(self.df['High'].values[-length:], self.df['Low'].values[-length:], self.df['Close'].values[-length:], timeperiod=14)
        # MACDの計算（結果をdf_feature_valueの長さに合わせる）
        MACD_1m, MACD_signal_1m, MACD_hist_1m = talib.MACD(self.df['Close'].values[-length:], fastperiod=12, slowperiod=26, signalperiod=9)

        # 計算結果をdf_feature_valueに追加
        self.df_feature_value['Williams_R_1m'] = Williams_R_1m
        self.df_feature_value['MACD_1m'] = MACD_1m
        self.df_feature_value['MACD_signal_1m'] = MACD_signal_1m
        self.df_feature_value['MACD_hist_1m'] = MACD_hist_1m

    def calculate_DMI_and_RSI(self):
        """DMIとRSIを計算してself.df_feature_valueに追加する"""
        # ADX, +DI, -DIの計算（14日を標準期間とする）
        self.df_feature_value['ADX'] = talib.ADX(self.df['High'], self.df['Low'], self.df['Close'], timeperiod=14)
        self.df_feature_value['plus_DI'] = talib.PLUS_DI(self.df['High'], self.df['Low'], self.df['Close'], timeperiod=14)
        self.df_feature_value['minus_DI'] = talib.MINUS_DI(self.df['High'], self.df['Low'], self.df['Close'], timeperiod=14)
    
        # RSIの計算（14日を標準期間とする）
        self.df_feature_value['RSI'] = talib.RSI(self.df['Close'], timeperiod=14)
    
        # 過去のDMI指標とRSIのシフト値を計算
        ADX_lag_shifted = pd.concat([self.df_feature_value['ADX'].shift(i).rename(f'ADX_lag_{i}') for i in range(1, 16)], axis=1)
        plus_DI_lag_shifted = pd.concat([self.df_feature_value['plus_DI'].shift(i).rename(f'plus_DI_lag_{i}') for i in range(1, 16)], axis=1)
        minus_DI_lag_shifted = pd.concat([self.df_feature_value['minus_DI'].shift(i).rename(f'minus_DI_lag_{i}') for i in range(1, 16)], axis=1)
        RSI_lag_shifted = pd.concat([self.df_feature_value['RSI'].shift(i).rename(f'RSI_lag_{i}') for i in range(1, 16)], axis=1)
    
        # 元のDataFrameと結合
        self.df_feature_value = pd.concat([self.df_feature_value, ADX_lag_shifted, plus_DI_lag_shifted, minus_DI_lag_shifted, RSI_lag_shifted], axis=1)
        
    def finalize_features(self):
        """特徴量を最終的に整理するメソッド"""

        self.df_feature_value.dropna(inplace=True)

        # インデックスをリセット
        self.df_feature_value.reset_index(drop=True, inplace=True)

        # 数値型の列のみを選択
        numeric_cols = self.df_feature_value.select_dtypes(include=[np.number]).columns

        # 数値型の列のみを float32 に変換
        self.df_feature_value[numeric_cols] = self.df_feature_value[numeric_cols].astype('float32')

        # 無限大の値をNaNに置き換える
        self.df_feature_value.replace([np.inf, -np.inf], np.nan, inplace=True)

        # NaNを前の値で埋める
        #self.df_feature_value.fillna(method='ffill', inplace=True)
        self.df_feature_value.ffill(inplace=True)
        # 小数点以下6桁で四捨五入
        self.df_feature_value = self.df_feature_value.round(6)

        # 特定の列を指定した型に変更
        self.df_feature_value = self.df_feature_value.astype({
            'Volume': 'int16',
            'year': 'int16',
            'month': 'int16',
            'day_of_week': 'int16'
        })

        return self.df_feature_value

    def load_model(self, model_path):
        # 指定されたパスからモデルを読み込む
        self.model = joblib.load(model_path)

    def predict(self, X=None):
        #print("df_feature_valueの形状:", self.df_feature_value.shape)
        #print("df_feature_valueの最初の5行:\n", self.df_feature_value.head())
        #print("df_feature_valueの最後の5行:\n", self.df_feature_value.tail())
        # モデルが読み込まれていない場合はエラーを発生させる
        if self.model is None:
            raise Exception("Model is not loaded. Please load a model before prediction.")

        # 欠損値の数を表示
        #print("欠損値の数（カラムごと）:")
        #print(self.df_feature_value.isnull().sum())
        #self.df_feature_value.to_csv('deback.csv')
        
        # Xが指定されていない場合は、インスタンス変数からデータフレームを使用
        if X is None:
            X = self.df_feature_value
            X = X.iloc[[-1]]
            if 'Time' in X.columns:
                X = X.drop(columns=['Time'])
            if 'datetime' in X.columns:
                X = X.drop(columns=['datetime'])

        # NaN値を前の値で補完し、データ型を推測
        X_filled = X.ffill().infer_objects()
        
        # まだNaNが残っている場合（例えば、最初の行がNaNである場合）、それらを0で補完する
        X_filled.fillna(0, inplace=True)
        
        #X_filled.to_csv('deback2.csv')
        X_filled = X_filled[[
                'min_diff_2h',
                'max_diff_2h',
                'Volume',
                'Williams_R_1m',
                'MACD_hist_1m',
                'MACD_1m',
                'MACD_signal_1m',
                'combined_diff',
                'combined_diff_1',
                'combined_diff_2'
                ]]

        # 予測を行う
        predictions = self.model.predict(X_filled)
        # 予測結果に基づいてメッセージを出力
            
        for pred in predictions:
            if pred == 0:
                print("価格上昇予測")
                FeatureGenerator.pred_0 += 1
            elif pred == 1:
                print("価格変動なし")
                FeatureGenerator.pred_1 += 1
            elif pred == 2:
                print("価格下降予測")
                FeatureGenerator.pred_2 += 1
            else:
                print("未知の予測結果：3or4")
                FeatureGenerator.pred_3 += 1
            print(f"pred0:{FeatureGenerator.pred_0},pred1:{FeatureGenerator.pred_1},pred2:{FeatureGenerator.pred_2},pred3:{FeatureGenerator.pred_3}")
        return predictions
        
class New_Orders_StrategyExecutor:
    def __init__(self, feature_generator, account_manager, api_client, account_id):
        self.feature_generator = feature_generator
        self.new_order_leverage_limit = 22  # 新規注文が許可されるレバレッジの上限
        self.account_manager = account_manager
        self.api_client = api_client
        self.account_id = account_id
        self.asset_ratio_leverage = self.account_manager.asset_ratio_leverage
        self.skip_new_tradecount = 0  # スキップされた注文の回数をカウントする

    def check_trading_hours(self):
        """取引時間外（週末など）のチェックを行う"""
        now = datetime.utcnow() + timedelta(hours=9)  # UTCからJSTへ変換
        if now.weekday() == 4 and now.hour >= 23:  # 金曜日の23時以降はトレードを停止
            print("トレードを停止します（金曜日の23時以降）")
            return False
        elif now.weekday() == 5:  # 土曜日全日はトレードを停止
            print("トレードを停止します（土曜日全日）")
            return False
        elif now.weekday() == 6:  # 日曜日全日はトレードを停止
            print("トレードを停止します（日曜日全日）")
            return False
        elif now.weekday() == 0 and now.hour < 8:  # 月曜日の8時前はトレードを停止
            print("トレードを停止します（月曜日の8時前）")
            return False
        print("トレード時間内です。")
        return True

    def execute_strategy(self):
        try:
            print("Executing strategy...")  # デバッグ用メッセージ
            # 取引時間外のチェック
            if not self.check_trading_hours():
                print("新規注文は取引時間外のためスキップされます。")
                return
    
            # レバレッジのチェック
            current_leverage = self.account_manager.calculate_leverage()
            print(f"現在のレバレッジ: {current_leverage}, レバレッジ制限: {self.new_order_leverage_limit}")
            if current_leverage >= self.new_order_leverage_limit:
                print("新規注文はレバレッジ制限のためスキップされます。")
                self.skip_new_tradecount += 1  # スキップされた注文の回数をカウント
                print(f"スキップされた注文の回数: {self.skip_new_tradecount}")
                return
    
            # 特徴量を生成し、予測を行う
            predictions = self.feature_generator.predict()
    
            # 予測結果に基づいてアクションを決定
            for prediction in predictions:
                print(f"Prediction: {prediction}")  # 予測結果を出力
                if prediction == 0:  # 価格下落予測
                    self.process_new_order(is_buy=False)
                    print("0なので、shortです")
                    #time.sleep(4)
                    #self.process_new_order(is_buy=False)
                    #print("0なので、short2です")
                    print(f"{datetime.now()}:")
                elif prediction == 2:  # 価格上昇予
                    # self.process_new_order(is_buy=True)
                    print("2なので、longです")
                    #time.sleep(4)
                    #self.process_new_order(is_buy=True)
                    #print("2なので、long2です")
                    #print(f"{datetime.now()}:")
                else:
                    print("予測に基づくアクションはありませんでした。")
                    print(f"{datetime.now()}:")
                    #self.process_new_order(is_buy=False)
                    #time.sleep(12)
                    #self.process_new_order(is_buy=False)
                    #self.process_new_order(is_buy=False)
                    
        except Exception as e:
            print(f"Error in execute_strategy: {e}")

    def process_new_order(self, is_buy):
        instrument = "USD_JPY"  # 取引する通貨ペア
        nav = self.account_manager.calculate_nav()
        margin_available = self.account_manager.calculate_available_margin()
        ask_price, bid_price = self.account_manager.get_current_prices(instrument)
        current_price = ask_price if is_buy else bid_price
        print(f"Processing new order: is_buy={is_buy}, current_price={current_price}")
        if current_price is None:
            print("Failed to fetch current prices. Skipping order.")
            return
    
        # 総評価額を計算
        total_value_target = nav * self.asset_ratio_leverage
    
        # 新規注文するロット数を計算
        units_needed = total_value_target / current_price
    
        # 新規注文の実行
        data = {
            "order": {
                "units": str(int(units_needed) if is_buy else -int(units_needed)),
                "instrument": instrument,
                "timeInForce": "FOK",
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }
        print(f"Order data: {data}")
        r = orders.OrderCreate(accountID=self.account_id, data=data)
        response = self.api_client.request(r)
        print(f"Order response: {response}")
        if 'orderFillTransaction' in response:
            trade_id = response['orderFillTransaction']['tradeOpened']['tradeID']
            # 注文時間を記録
            order_time = parser.parse(response['orderFillTransaction']['time'])
            # トレード情報を辞書として保存
            self.account_manager.trade_order_times[trade_id] = {'order_time': order_time.replace(tzinfo=pytz.UTC), 'initial_price': current_price}
            print(f"Order placed at {order_time}: {response}")
            # ポジションを更新
            self.account_manager.update_positions()
        else:
            print("Order was not filled successfully.")

class Settlement_order_StrategyExecutor:
    def __init__(self, account_manager, api_client, account_id):
        self.account_manager = account_manager
        self.api_client = api_client
        self.account_id = account_id
        self.leverage_limit = 24  # レバレッジ制限を24に設定
        self.position_check = 0

    def execute_settlement(self):
        self.account_manager.update_positions()  # ポジションを更新
        current_time = datetime.now(pytz.UTC)  # UTCで現在時刻を取得
        positions = self.account_manager.positions
    
        if not positions:
            print("No positions available.")  # ポジションがない場合の出力
            return
    
        print(f"Current positions: {positions}")  # デバッグ用メッセージ
        for position_id, position in enumerate(positions):
            try:
                trade_id = position['trade_id']
                side = position['side']
                initial_price = position['initial_price']
                current_price = position['price']
                
                if initial_price is None or current_price is None:
                    raise ValueError("Initial price or current price is None")
                    
                price_diff = current_price - initial_price if side == 'long' else initial_price - current_price
                time_elapsed = current_time - position['order_time']
    
                print(f"Position {position_id}: Trade ID = {trade_id}, Side = {side}")
                print(f"Initial Price = {initial_price}, Current Price = {current_price}, Price Diff = {price_diff}")
                print(f"Time Elapsed = {time_elapsed}")
    
                if self.should_close_position(position, time_elapsed, price_diff):
                    print(f"Closing position {position_id} due to conditions met.")
                    self.account_manager.close_position(trade_id)
                else:
                    print(f"Position {position_id} does not meet closing conditions.")
            except Exception as e:
                print(f"Error processing position {position_id}: {e}")
                continue  # エラーが発生した場合、そのポジションをスキップして次に進む
            
    def should_close_position(self, position, time_elapsed, price_diff):
        if position['side'] == 'long':
            print(f"Long position close check: Time elapsed = {time_elapsed}, Price diff = {price_diff}")
            if (time_elapsed >= timedelta(minutes=12) or price_diff <= -0.05 or price_diff >= 0.25):
                return True
        elif position['side'] == 'short':
            print(f"Short position close check: Time elapsed = {time_elapsed}, Price diff = {price_diff}")
            if (time_elapsed >= timedelta(minutes=12) or price_diff >= 0.05 or price_diff <= -0.25):
                return True
        return False
        
    def close_all_positions_if_leverage_exceeded(self):
        #レバレッジが設定された上限を超えた場合に、全ポジションをクローズする。
        # 現在のレバレッジを計算
        current_leverage = self.account_manager.calculate_leverage()
        print(f"現在のレバレッジ: {current_leverage}, 上限: {self.leverage_limit}") #デバック
        # レバレッジが上限を超えているか確認
        if current_leverage > self.leverage_limit:
            print("レバレッジ上限を超えたため、全ポジションをクローズします。")
            # 全ポジションをクローズ
            self.close_all_positions()
            
    def close_all_positions(self):
        # 開いている全トレードを取得
        #print("開いている全トレードをクローズします。")
        open_trades = trades.OpenTrades(accountID=self.account_id)
        open_trades_response = self.api_client.request(open_trades)
        #print(f"クローズするトレード数: {len(open_trades_response['trades'])}")
        for trade in open_trades_response['trades']:
            trade_id = trade['id']
            self.account_manager.close_position(trade_id)
            #print(f"トレード {trade['id']} をクローズしました。")
            
    def close_positions_before_weekend(self):
        """金曜日の23:30に保有ポジションを解消する"""
        now = datetime.utcnow() + timedelta(hours=9)  # UTCからJSTへ変換
        #print(f"現在時刻: {now}")
        if now.weekday() == 4 and now.hour == 23 and now.minute >= 30:
            #print("金曜日の23:30を過ぎたため、全ポジションをクローズします。")
            # 開いている全トレードを取得
            open_trades = trades.OpenTrades(accountID=self.account_id)
            open_trades_response = self.api_client.request(open_trades)
            for trade in open_trades_response['trades']:
                trade_id = trade['id']
                # トレードをクローズ
                self.account_manager.close_position(trade_id)

async def run_long_term_tasks(api_client, account_id, model_path):
    market_data_fetcher = MarketDataFetcher(api_client, 'USD_JPY')
    account_manager = AccountManager(api_client, account_id)
    #initial_wait_time = 300 - (time.time() % 300)  # 次の30分までの秒数を計算
    initial_wait_time = 180 - (time.time() % 180)  # 次の30分までの秒数を計算
    await asyncio.sleep(initial_wait_time)  # 最初のスケジュールまで待機
    skip_count = 0  # 土日にスキップされた回数をカウント
    reconnect_interval = 1 * 90 * 60 
    #reconnect_interval = 2 * 60 * 60  # 2時間ごとに再接続
    last_reconnect_time = time.time()  # 最後の再接続の時間を記録
    reconnect_count = 0  # 再接続の回数をカウント

    while True:
        if is_weekend_japan_time():
            skip_count += 1
            print("土日はリクエストを行いません。")
            #await asyncio.sleep(300)  # 次のループまで待機
            await asyncio.sleep(180)  # 次のループまで待機
            continue
        
        print(f"{datetime.now(pytz.UTC)}: データ取得と処理を開始します。")
        df = market_data_fetcher.fetch_latest_data()
        fg = FeatureGenerator(df)
        fg.calculate_features()
        fg.label_price_change()
        fg.calculate_1m_WilliamsR_and_MACD()
        fg.calculate_DMI_and_RSI()
        fg.finalize_features()
        fg.load_model(model_path)
        predictions = fg.predict()
        print(f"予測結果: {predictions}")

        nos = New_Orders_StrategyExecutor(feature_generator=fg, account_manager=account_manager, api_client=api_client, account_id=account_id)
        if nos.check_trading_hours():
            nos.execute_strategy()  # ここを修正

        #await asyncio.sleep(300)  # 30分ごとの待機
        await asyncio.sleep(180)

async def run_short_term_tasks(api_client, account_id):
    account_manager = AccountManager(api_client, account_id, asset_ratio_leverage=7)
    settlement_executor = Settlement_order_StrategyExecutor(account_manager, api_client, account_id)
    skip_count = 0  # 土日にスキップされた回数をカウント
    reconnect_interval = 1 * 90 * 60  # 2時間ごとに再接続
    last_reconnect_time = time.time()  # 最後の再接続の時間を記録
    reconnect_count = 0  # 再接続の回数をカウント
    
    while True:
        if is_weekend_japan_time():
            skip_count += 1
            print(f"土日はリクエストを行いません。{skip_count}回目")
            await asyncio.sleep(1)  # 次のループまで待機
            continue
        
        # 現在の時間と最後の再接続時間を比較
        current_time = time.time()
        if (current_time - last_reconnect_time >= reconnect_interval):
            # ポジションを確認し、ポジションがない場合のみ再接続
            account_manager.update_positions()
            if not account_manager.positions:
                api_client = await reconnect_oanda(api_client, account_id)
                last_reconnect_time = current_time
                reconnect_count += 1
                print(f'reconnect: {reconnect_count}')
                
        # 口座情報の更新やポジションの管理
        await asyncio.sleep(1)  # 10秒待機
        # Settlement_order_StrategyExecutorを使用して決済処理を実行
        settlement_executor.execute_settlement()
        # レバレッジ上限を超えた場合に全ポジションをクローズ
        settlement_executor.close_all_positions_if_leverage_exceeded()
        # (具体的な決済処理の実装はここに追加)
        am = AccountManager(api_client, account_id, asset_ratio_leverage=7)
        am.fetch_account_info()
        am.calculate_available_margin()
        am.calculate_leverage()
        am.get_current_prices("USD_JPY")
        am.update_positions()
        print(f"pred0:{FeatureGenerator.pred_0},pred1:{FeatureGenerator.pred_1},pred2:{FeatureGenerator.pred_2},pred3:{FeatureGenerator.pred_3},reconnect: {reconnect_count}")

# OANDAデータの取得と処理関数の追加
async def fetch_oanda_data(account_id, days=30):
    client = oandapyV20.API(access_token=access_token, environment="live")  # 正しいトークンと環境を設定
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    params = {
        "from": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "to": end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "type": "ORDER_FILL",
    }
    
    r = transactions.TransactionList(accountID=account_id, params=params)
    
    try:
        client.request(r)
    except oandapyV20.exceptions.V20Error as e:
        print(f"Error: {e}")
        return []
    
    res = r.response
    
    transaction_data = []
    
    for i in res["pages"]:
        m = re.search(pattern=r"from=(?P<from_id>[0-9]+)&to=(?P<to_id>[0-9]+)", string=i)
        
        data = {
            "type": "ORDER_FILL",
            "from": int(m.group("from_id")),
            "to": int(m.group("to_id")),
        }

        r = transactions.TransactionIDRange(accountID=account_id, params=data)
        
        try:
            res_idrange = client.request(r)
        except oandapyV20.exceptions.V20Error as e:
            print(f"Error: {e}")
            continue
        
        transaction_data.extend(res_idrange.get("transactions"))

    return transaction_data

# 投稿回数の初期化
tweet_count = 0

# Twitter投稿関数の追加
async def post_summary(post_type, period_days):
    try:
        data = await fetch_oanda_data(account_id, days=period_days)
        
        if not data:
            print("No transactions found.")
            return
        
        transactions = data
        
        total_pnl = 0
        total_trades = len(transactions)
        win_trades = 0
        total_units = 0  # トレードUnitの合計を計算するための変数
        today_trades = 0
        today_pnl = 0
        today_win_trades = 0
        today_units = 0

        today_date = datetime.utcnow().strftime('%Y-%m-%d')

        pnl_list = []
        cumulative_pnl = 0

        for transaction in transactions:
            if transaction['type'] == 'ORDER_FILL':
                pnl = float(transaction['pl'])
                units = abs(float(transaction['units']))
                total_pnl += pnl
                total_units += units
                cumulative_pnl += pnl
                pnl_list.append(cumulative_pnl)
                if pnl > 0:
                    win_trades += 1

                # 今日のトレードを計算
                if transaction['time'].startswith(today_date):
                    today_trades += 1
                    today_pnl += pnl
                    today_units += units
                    if pnl > 0:
                        today_win_trades += 1

        win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0
        today_win_rate = (today_win_trades / today_trades) * 100 if today_trades > 0 else 0

        # コメントの生成
        positive_comments_100000 = ["FXの自動売買（オートトレード）のBot作ってよかったー！Pythonの勉強始めてから数年経ったけど、もっと上達できるように頑張ります！", 
                             "福利で積み上がっていってるぜ、これが１年続いたら人生イージーモードなんだろうな。でも、金持ちは金持ちで襲われる心配とかあるからな。",
                             "よっしゃー、巨人戦見て頑張ろう",
                             "よっしゃー、今日も1日お疲れ様でした。"
                             "あざます！さすがっす。botterの講習会をmentaで始めよっかな。"
                             "あざます！さすがっす。botterの道のりガイドをnoteで始めます！"]
                             
        positive_comments_50000 = ["FXの自動売買（オートトレード）のBot作ってよかったー！Pythonの勉強始めてから数年経ったけど、もっと上達できるように頑張ります！", 
                             "まだまだ、これからだぜ。機械学習の質はもっとあげないとな。データの質が重要。これを果たして維持できるのか？", 
                             "福利で積み上がっていってるぜ、これが１年続いたら人生イージーモードなんだろうな。でも、金持ちは金持ちで襲われる心配とかあるからな。",
                             "よっしゃー、巨人戦見て頑張ろう",
                             "よっしゃー、そろそろBotの作り方をnoteに書き始めようかな。Botの作り方とか、勝つための考え方とか知りたい人はDMお待ちしてます。A級BotterになったらNote記事有料化するので今のうちです。"]

        positive_comments_10000 = ["ここから、もっと伸ばせるか、このまま終わるのかがbotterの分岐点だからな。頑張ろう。",
                                    "継続は力なり、マジでこのまま頑張ってくれ。今日もbot用の機械学習モデルの構築を頑張ります。",
                                    "こっからや、今日もbot用の機械学習モデルの構築を頑張ります。",
                                    "おお、このくらいコンスタントに稼げたら良いよね。マイナスの量を減らして、いかにプラスの時に利益を増せるかだからな。今日もモデル構築しますか。"
        ]
        
        positive_comments_5000 = ["まだまだ、これから。日利で5%~6.%はいけるようにならないと。機械学習の質はもっとあげないとな。新しい機械学習モデル作るかー",
                                  "数万円単位で稼ぎたいよねー、FXのオートトレードって福利で上がってくるから良いよねー。他のモデルも構築せねばな。",
                                  "まぁ。このくらいは今日の範囲内でしょう。今日は巨人戦でも観ようかな。",
                                  "まだまだだな。このBot作ったばかりだから、まだまだ改善は必要そうだな。今日はPandasとPythonの基礎勉強しようっと！"
        ]
        
        positive_comments_0 = ["もっと、稼いでくれー！！！！！Python基礎のコード書こうっと！",
                               "少しだけ勝ったか。今日は巨人戦あんのかな？ジャイアンツ優勝してくれー！",
                               "もっと、勝ってくれ！",
                               "PythonでBot作ったけど、この利益じゃ労力に見合わないぞ。頑張れよ。機械学習モデル見直すか。",
                               "これじゃあ、最近の高校生の小遣い稼ぎにもならんぞ、AWS止めたろうか。"
        ]
        
        negative_comments = ["こ、これは、次回は利益を出してくれ。このままだと止めざるを得ない。機械学習で結果出すって難しいよね。", "そういう日もあるよね。仕方なし。Pythonの勉強しよっと。", "うん、1日くらい許容できるんだけどねぇ。困ったぜ。Pythonって極論、何でもできるから便利だね。"]

        even_comments = ["このロジックだとトレード回数がそもそも少ないなぁ。決定木を使ってるけど、分類が偏ってるのかな。　https://www.kikagaku.co.jp/kikagaku-blog/decision-tree-visualization/","やっぱ、AIは万能ではないんだよ。この記事が言ってるように。https://xtech.nikkei.com/atcl/nxt/column/18/02108/062700001/","1日10回トレードして、日利4%~5%でも稼げば良いんだよね。　https://news.yahoo.co.jp/articles/48b0fa2fad0057e9ffbd659fe82d197c67261090?page=2","トレードをもっとしてくれ！！これなら自分でやった方が良いぞ。この決定木の説明まぁまぁわかりやすい https://datawokagaku.com/decision_tree/"]
        if today_trades < 3:
            comment = random.choice(even_comments)
        else:
            if today_pnl > 100000:
                comment = random.choice(positive_comments_100000)
            elif today_pnl > 50000:
                comment = random.choice(positive_comments_50000)
            elif today_pnl > 10000:
                comment = random.choice(positive_comments_10000)
            elif today_pnl > 5000:
                comment = random.choice(positive_comments_5000)
            elif today_pnl > 0:
                comment = random.choice(positive_comments_5000)        
            else:
                comment = random.choice(negative_comments)
        
        # グラフを作成
        x = np.arange(len(transactions))
        y = [float(transaction['pl']) for transaction in transactions]
        
        fig, ax1 = plt.subplots()

        color = 'tab:blue'
        ax1.set_xlabel('Trade Number')
        ax1.set_ylabel('Profit/Loss', color=color)
        ax1.plot(x, y, label='PnL per Trade', color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        
        color = 'tab:pink'
        ax2.set_ylabel('Cumulative PnL', color=color)  # we already handled the x-label with ax1
        ax2.plot(x, pnl_list, label='Cumulative PnL', color=color)
        ax2.tick_params(axis='y', labelcolor=color)

        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.title(f'{period_days} Day Trading Performance')

        # 画像保存
        image_path = f'/tmp/trade_performance_{period_days}days.png'
        plt.savefig(image_path)
        plt.close()

        # グラフを作成するコードの直後
        global tweet_count
        tweet_count += 1  # ツイート回数をカウント

        # ツイート内容の作成コードの直前
        # ツイート内容の作成コードの直前
        today = datetime.now().strftime('%Y年%m月%d日')
        
        # ツイート内容に投稿回数を追加
        if post_type == "本日":
            post_content = f"{today}\n (1つ目のBot)" \
                           f"本日: 回数 {today_trades}, Unit {today_units:.2f}, 勝率 {today_win_rate:.2f}%, 損益 {today_pnl:.2f}円\n" \
                           f"過去30日: 損益 {total_pnl:.2f}円, 回数 {total_trades}, 勝率 {win_rate:.2f}%\n" \
                           f"{comment}"
        else:
            # 2024年累積のデータを計算
            year_start = datetime(datetime.now().year, 1, 1)
            year_data = await fetch_oanda_data(account_id, days=(datetime.now() - year_start).days)
            if year_data:
                year_transactions = year_data
                year_total_pnl = 0
                year_total_trades = len(year_transactions)
                year_win_trades = 0
                year_total_units = 0
        
                for transaction in year_transactions:
                    if transaction['type'] == 'ORDER_FILL':
                        pnl = float(transaction['pl'])
                        units = abs(float(transaction['units']))
                        year_total_pnl += pnl
                        year_total_units += units
                        if pnl > 0:
                            year_win_trades += 1
        
                year_win_rate = (year_win_trades / year_total_trades) * 100 if year_total_trades > 0 else 0

                # コメントの生成
                positive_comments_total_5000000 = ["FXの自動売買（オートトレード）のBot作ってよかったー！Pythonの勉強始めてから数年経ったけど、もっと上達できるように頑張ります！", 
                                     "まだまだ、これからだぜ。日利で5%~6.%はいけるようにならないと。機械学習の質はもっとあげないとな。データの質が重要。", 
                                     "福利で積み上がっていってるぜ、これが１年続いたら人生イージーモードなんだろうな。でも、金持ちは金持ちで襲われる心配とかあるからな。",
                                     "よっしゃー、巨人戦見て頑張ろう",
                                     "機械学習の勉強するか。"
                                     "よっしゃー、そろそろ独立しようかな。",
                                     "ジャイアンツのシーズンシート買おうかな。迷うなー、水道橋に住むか。迷うなー。",
                                     "今年はこれを維持したい。統計学の資格取得するために勉強しますかー！統計検定1級まで取りたい。"]
                                     
                positive_comments_total_1000000 = ["FXの自動売買（オートトレード）のBot作ってよかったー！Pythonの勉強始めてから数年経ったけど、もっと上達できるように頑張ります！", 
                                     "まだまだ、これからだぜ。日利で5%~6.%はいけるようにならないと。機械学習の質はもっとあげないとな。データの質が重要。", 
                                     "福利で積み上がっていってるぜ、これが１年続いたら人生イージーモードなんだろうな。でも、金持ちは金持ちで襲われる心配とかあるからな。",
                                     "よっしゃー、巨人戦見て頑張ろう",
                                     "よっしゃー"]
                positive_comments_total_500000 = ["トータルで考えると良い成績ではあるが、ちょっと物足りない感がある。仮想通貨について勉強しようかな。それより統計学学ぶか。",
                                            "これから相場も変わるかもしれないし、何が起こるのかわからないからもっと稼いでおきたいところではある。統計検定2級は早く取りたいな。",
                                            "継続は力なりなので頑張って継続してもらいましょう！新しい機械学習モデル作ります。",
                                            "このままこのまま！","このまま頑張ってくれー！！","がんばれー","よっしゃ、ジャイアンツ優勝しないかな。","よっしゃ、岡本がんばれ！","このまま継続継続〜"
                ]
                
                positive_comments_total_100000 = ["",
                                            "まだまだ、これからですね。頑張りましょう。",
                                            "Numpyも頑張ります。",
                                            "よし、頑張ります。","これからー！","Pythonって本当に良いよね。","Pandas極めるか！勉強ー！","日経平均の機械学習やりますかー。","日経平均の指標に関連する上場企業の株価指標を全部取って機械学習するか。",
                                            "はやく年700万稼ぐようになりたい。機械学習の勉強大事。"
                ]        
                
                positive_comments_total_0 = ["まぁ、勝ててるから良いものの...",
                                            "まぁ、勝ててるから...",
                                            "まぁ、勝ててるからね...",
                                            "まぁ、勝ててるからさ..."
                ]

                negative_comments_total = ["そろそろ、このBot閉じようかな。", "もう少しみようかな。", "まだまだこれからだよ"]

                negative_comments_total_30000 = ["負ける時もあるよね。今日の統計学：1-1. ギリシャ文字の読み方　https://bellcurve.jp/statistics/course/1547.html", "もう少しみようかな。　統計学に必要な数学：https://bellcurve.jp/statistics/course/1559.html", "まだまだこれからだよ　分散とは：https://bellcurve.jp/statistics/course/5919.html "]
                
                if year_total_pnl > 5000000:
                    total_comment = random.choice(positive_comments_total_5000000)
                elif year_total_pnl > 1000000:
                    total_comment = random.choice(positive_comments_total_1000000)
                elif year_total_pnl > 500000:
                    total_comment = random.choice(positive_comments_total_500000)
                elif year_total_pnl > 100000:
                    total_comment = random.choice(positive_comments_total_100000)
                elif year_total_pnl > 0:
                    total_comment = random.choice(positive_comments_total_0)
                elif year_total_pnl > -30000:
                    total_comment = random.choice(negative_comments_total_30000)
                else:
                    total_comment = random.choice(negative_comments_total)        
       
                post_content = f"2024年累積\n (1つ目のBot)" \
                               f"回数 {year_total_trades}, Unit {year_total_units:.2f}, 勝率 {year_win_rate:.2f}%, 損益 {year_total_pnl:.2f}円\n" \
                               f"過去90日: 損益 {total_pnl:.2f}円, 回数 {total_trades}, 勝率 {win_rate:.2f}%\n" \
                               f"{total_comment}"

        # 画像をアップロードし、メディアIDを取得
        auth = tweepy.OAuth1UserHandler(
            twitter_keys['consumer_key'],
            twitter_keys['consumer_secret'],
            twitter_keys['access_token'],
            twitter_keys['access_token_secret']
        )
        api = tweepy.API(auth)
        media = api.media_upload(image_path)
        media_id = media.media_id
        
        # ツイートを投稿
        twitter_client.create_tweet(text=post_content, media_ids=[media_id])
        print(f"{post_type} summary tweet posted.")
        print(f"投稿回数: {tweet_count}回")

        # 画像ファイルを削除
        os.remove(image_path)
        print(f"画像ファイル {image_path} を削除しました。")

    except Exception as e:
        print(f"Error during post_summary: {e}")

async def tweet_task():
    while True:
        now = datetime.now(pytz.timezone('Asia/Tokyo'))

        # 日曜日の場合
        if 1 <= now.weekday() <= 5:
            if now.hour == 0 and now.minute == 0:
                print("本日の投稿")
                await post_summary("累積", 30)  # 累積の投稿テスト
            elif now.hour == 20 and now.minute == 0:
                #await asyncio.sleep(3600)  # 5秒後に次の投稿を行う
                print("累積の投稿")
                await post_summary("本日", 90)  # 本日の投稿テスト
                
        await asyncio.sleep(60)  # 1分ごとにチェック

# async def tweet_task():
#     # 一度だけバックテストを行う部分
#     print("バックテストを実行します")
#     await post_summary("バックテスト", 100)  # バックテストの投稿テスト

#     while True:
#         now = datetime.now(pytz.timezone('Asia/Tokyo'))

#         # 日曜日の場合
#         if 1 <= now.weekday() <= 7:
#             if now.hour == 0 and now.minute == 0:
#                 print("本日の投稿")
#                 await post_summary("累積", 30)  # 累積の投稿テスト
#             elif now.hour == 20 and now.minute == 0:
#                 #await asyncio.sleep(3600)  # 5秒後に次の投稿を行う
#                 print("累積の投稿")
#                 await post_summary("本日", 90)  # 本日の投稿テスト
                
#         await asyncio.sleep(60)  # 1分ごとにチェック


reconnect_interval = 1 * 90 * 60  # 1分ごとに再接続   
reconnect_count = 0  # 再接続の回数をカウント
async def main(api_client, account_id, model_path):
    account_manager = AccountManager(api_client, account_id)
    task1 = asyncio.create_task(run_long_term_tasks(api_client, account_id, model_path))
    task2 = asyncio.create_task(run_short_term_tasks(api_client, account_id))
    task3 = asyncio.create_task(tweet_task())  # ツイートタスクを追加
    
    last_reconnect_time = time.time()  # 最後に再接続を行った時間
    
    try:
        while True:
            await asyncio.gather(task1, task2, task3)
            current_time = time.time()
            if current_time - last_reconnect_time >= reconnect_interval:
                account_manager.update_positions()  # ポジションを更新
                if not account_manager.positions:  # ポジションがない場合のみ再接続
                    print("No positions, reconnecting...")

                    api_client = oandapyV20.API(access_token=access_token, environment="live")
                    account_manager = AccountManager(api_client, account_id)  # AccountManagerのインスタンスを更新
                    reconnect_count += 1
                    last_reconnect_time = current_time
                    print(f"Reconnected: {reconnect_count} times")
                else:
                    print("Positions exist, no need to reconnect.")
            
            await asyncio.sleep(1)  # 短い間隔でチェックを行う

    except Exception as e:
        print("Error occurred:")
        traceback.print_exc()  # ここでスタックトレースを出力        #await asyncio.sleep(3)

# API設定
if __name__ == "__main__":
    nest_asyncio.apply()
    

# JSONファイルを読み込む
with open('config.json', 'r') as f:
    config = json.load(f)

account_id = config['account_id']
access_token = config['access_token']
environment = config['environment']
model_path = '06_2_20090104-20240704_3m.joblib'  # モデルのパスを指定

# APIクライアントの初期化
api_client = API(access_token=access_token, environment=environment)

# asyncio.runでmain関数を呼び出し、必要な引数を渡す
asyncio.run(main(api_client, account_id, model_path))

