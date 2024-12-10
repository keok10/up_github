import pandas as pd
from IPython.display import display
import gc
import talib

# compute_diffs メソッドで差分を計算するクラス
class MyClass:
    def __init__(self, df):
        self.df = df
        self.df_feature_value = df.copy()
        self.ma_df = pd.DataFrame()

    # 移動平均乖離率の計算
    def calculate_features(self):
        # 短期移動平均線のウィンドウサイズ
        short_term_windows = [3, 5, 8, 10, 12, 15]
        # 長期移動平均線のウィンドウサイズ
        long_term_windows = [30, 35, 40, 45, 50, 60]
        # 短期・長期の移動平均線を計算
        windows = [3, 5, 8, 10, 12, 15, 30, 35, 40, 45, 50, 60]
        
        for window in windows:
            self.df[f'ma_{window}'] = self.df['Close'].rolling(window=window).mean()
        # 移動平均の差分（乖離）を計算
        short_windows = windows[:6]  # 短期
        long_windows = windows[6:]  # 長期
        self.df['diff_short'] = self.df[[f'ma_{w}' for w in short_windows]].diff(axis=1).iloc[:, -1]
        self.df['diff_long'] = self.df[[f'ma_{w}' for w in long_windows]].diff(axis=1).iloc[:, -1]

        #長短GMMA乖離率の差分
        self.df_feature_value['combined_diff'] = self.df['diff_short'] - self.df['diff_long']
        # 過去のcombined_diffの追加
        combined_diff_shifted = pd.concat([self.df_feature_value['combined_diff'].shift(i).rename(f'combined_diff_{i}') for i in range(1, 15)], axis=1)
        
        # 元のDataFrameと結合
        self.df_feature_value = pd.concat([self.df_feature_value, combined_diff_shifted], axis=1)

        # 年、月、曜日の特徴量を追加
        self.df_feature_value['year'] = self.df['datetime'].dt.year
        self.df_feature_value['month'] = self.df['datetime'].dt.month
        self.df_feature_value['day_of_week'] = self.df['datetime'].dt.dayofweek
        # 欠損値を含む行を削除
        self.df_feature_value.dropna(inplace=True)
        # インデックスをリセット
        self.df_feature_value.reset_index(drop=True, inplace=True)
        return self.df_feature_value  # 変更されたDataFrameを返す

    # ラベル付けの提案
    # 0: 価格変動が-0.2以下（価格が下降）
    # 1: 価格変動が-0.2より大きく0.2より小さい（価格があまり変わらない）
    # 2: 価格変動が0.2以上（価格が上昇）            
    def label_price_change(self):
        self.df_feature_value['max_diff_15m'] = self.df_feature_value['Close'].rolling(window=60).max() - self.df_feature_value['Close']
        self.df_feature_value['min_diff_15m'] = self.df_feature_value['Close'].rolling(window=60).min() - self.df_feature_value['Close']
        self.df_feature_value['price_change_label'] = 1  # デフォルト値

        for i in range(15, len(self.df_feature_value)):
            if self.df_feature_value['max_diff_15m'].iloc[i] >= 0.12:
                self.df_feature_value.at[i, 'price_change_label'] = 2
                if any(self.df_feature_value['min_diff_15m'].iloc[i-15:i] <= -0.06):
                    self.df_feature_value.at[i, 'price_change_label'] = 4  # 15分以内に-0.06以下に1回でもなったら4

            elif self.df_feature_value['min_diff_15m'].iloc[i] <= -0.12:
                self.df_feature_value.at[i, 'price_change_label'] = 0
                if any(self.df_feature_value['max_diff_15m'].iloc[i-15:i] >= 0.06):
                    self.df_feature_value.at[i, 'price_change_label'] = 3  # 15分以内に0.06以上に1回でもなったら3

            else:
                # 既にデフォルトで1が割り当てられているため、追加の処理は不要
                pass

    def calculate_1d_WilliamsR_and_MACD(self, df_1d):
        """ウィリアムズ%RとMACDを計算し、df_feature_valueに追加する"""
        # ウィリアムズ%Rの計算（14日を標準期間とする）
        df_1d['Williams_R'] = talib.WILLR(df_1d['Mid_High'].values, df_1d['Mid_Low'].values, df_1d['Mid_Close'].values, timeperiod=14)

        # MACDの計算
        df_1d['MACD'], df_1d['MACD_signal'], df_1d['MACD_hist'] = talib.MACD(df_1d['Mid_Close'].values, fastperiod=12, slowperiod=26, signalperiod=9)

        # 日付のみを抽出（時間情報の削除）
        self.df_feature_value['date'] = self.df_feature_value['datetime'].dt.date
        df_1d['date'] = df_1d['datetime'].dt.date

        # 1日足の特徴量を1分足データにマージ
        self.df_feature_value = pd.merge(self.df_feature_value, df_1d[['date', 'Williams_R', 'MACD']], on='date', how='left')

        # 'date'列の削除
        self.df_feature_value.drop(columns=['date'], inplace=True)
    
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

        # DMIとRSIの過去120日分のデータを追加
        ADX_lag_shifted = pd.concat([self.df_feature_value['ADX'].shift(i).rename(f'ADX_lag_{i}') for i in range(1, 16)], axis=1)
        plus_DI_lag_shifted = pd.concat([self.df_feature_value['plus_DI'].shift(i).rename(f'plus_DI_lag_{i}') for i in range(1, 16)], axis=1)
        minus_DI_lag_shifted = pd.concat([self.df_feature_value['minus_DI'].shift(i).rename(f'minus_DI_lag_{i}') for i in range(1, 16)], axis=1)
        RSI_lag_shifted = pd.concat([self.df_feature_value['RSI'].shift(i).rename(f'RSI_lag_{i}') for i in range(1, 16)], axis=1)
        
        # 元のDataFrameと結合
        self.df_feature_value = pd.concat([self.df_feature_value, ADX_lag_shifted, plus_DI_lag_shifted, minus_DI_lag_shifted, RSI_lag_shifted], axis=1)
    
    def finalize_features(self):
        """特徴量を最終的に整理するメソッド"""
        # 欠損値を含む行を削除
        self.df_feature_value.dropna(inplace=True)

        # インデックスをリセット
        self.df_feature_value.reset_index(drop=True, inplace=True)

# データ読み込み
df = pd.read_csv('USD_JPY_M1_GMMA_all_20160104-20240302.csv', parse_dates=['datetime'])
df_1d = pd.read_csv('USD_JPY_d1_all_20160104-20240302.csv', parse_dates=['datetime'])

obj = MyClass(df)

obj.calculate_features()
print("calculate_features:end")
obj.label_price_change()
print("label_price_change:end")
obj.calculate_1m_WilliamsR_and_MACD()
print("calculate_1m_WilliamsR_and_MACD:end")
obj.calculate_1d_WilliamsR_and_MACD(df_1d)
print("calculate_1d_WilliamsR_and_MACD:end")
obj.calculate_DMI_and_RSI()
print("calculate_DMI_and_RSI:end")
obj.finalize_features()
print("finalize_features:end")

# 小数点以下6桁で四捨五入
obj.df_feature_value = obj.df_feature_value.round(6)

# 'datetime' 列を除外した列名のリストを取得
columns_except_datetime = obj.df_feature_value.columns.difference(['datetime'])

# 'datetime' 列を除外した列のみを float32 に変換
obj.df_feature_value[columns_except_datetime] = obj.df_feature_value[columns_except_datetime].astype('float32')

# 特定の列を指定した型に変更
obj.df_feature_value = obj.df_feature_value.astype({
    'Volume': 'int16',
    'price_change_label': 'int8',
    'year': 'int16',
    'month': 'int16',
    'day_of_week': 'int16'
})

print("resize:end")

# CSVファイルとして保存
obj.df_feature_value.to_csv('2024_15day_MaDiff_15dayRSI_MDI_1m&1dmacd_Williams%R_pips15m.csv', index=False)
print("tocsv:end")

# 必要な列のリスト
required_columns = ['High', 'Low', 'Close']

# df_1dの列名を表示
print("df_1d columns:", df_1d.columns.tolist())

# 必要な列がdf_1dに存在するか確認
missing_columns = [col for col in required_columns if col not in df_1d.columns]
if missing_columns:
    print("Missing columns in df_1d:", missing_columns)
else:
    print("All required columns are present in df_1d.")

# 必要な列のリスト
required_columns = ['High', 'Low', 'Close']

# df_1dの列名を表示
print("df_1d columns:", df_1d.columns.tolist())

# 必要な列がdf_1dに存在するか確認
missing_columns = [col for col in required_columns if col not in df_1d.columns]
if missing_columns:
    print("Missing columns in df_1d:", missing_columns)
else:
    print("All required columns are present in df_1d.")

