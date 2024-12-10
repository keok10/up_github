import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
from sklearn.metrics import precision_score, recall_score, f1_score
from joblib import dump
from joblib import load


df_feature_value = pd.read_csv('2024_15day_MaDiff_15dayRSI_MDI_1m&1dmacd_Williams%R_pips15m.csv', parse_dates=['datetime'])
#value['price_change_label'] = df_feature_value['price_change_label'].shift(-1)
#df_feature_value.dropna(inplace=True)

# 特徴量とターゲットの定義（'price_change_label'をターゲットとする）
#xが特徴量で、datetimeとターゲットを除外する。
X = df_feature_value.drop(['datetime', 'price_change_label'], axis=1)  # datetime列とターゲット列を除外

# ターゲット（ラベル）
y = df_feature_value['price_change_label']

# TimeSeriesSplitのインスタンス化
tscv = TimeSeriesSplit(n_splits=8)

# スコアを格納するリスト
scores = []

# 時系列交差検証
for train_index, test_index in tscv.split(X):
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    
    # ランダムフォレスト分類器のインスタンス化と訓練
    model = RandomForestClassifier(random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # テストデータでの予測とスコア計算
    predictions = model.predict(X_test)
    score = accuracy_score(y_test, predictions)
    scores.append(score)

# 平均スコアの計算と表示
# 予測
predictions = model.predict(X_test)
# 精度
precision = precision_score(y_test, predictions, average='macro')  # 'macro'はクラス間で平均を取る方法の一つ
# 再現率
recall = recall_score(y_test, predictions, average='macro')
# F1スコア
f1 = f1_score(y_test, predictions, average='macro')
#平均精度
average_score = sum(scores) / len(scores)

# 学習済みモデルから特徴量の重要度を取得
importances = model.feature_importances_

# 特徴量の名前のリスト（Xが特徴量のDataFrameの場合）
feature_names = X.columns

print(f'平均精度: {average_score:.4f}')
print(f'精度: {precision:.4f}')
print(f'再現率: {recall:.4f}')
print(f'F1スコア: {f1:.4f}')

dump(model, '2024_15day_MaDiff_15dayRSI_MDI_1m&1dmacd_Williams%R_pips15m.joblib')

# 学習済みモデルから特徴量の重要度を取得
importances = model.feature_importances_

# 特徴量の名前のリスト（Xが特徴量のDataFrameの場合）
feature_names = X.columns

plt.figure(figsize=(10, 50))  # グラフのサイズを大きく調整
plt.barh(range(X.shape[1]), importances, align='center')
plt.yticks(range(X.shape[1]), feature_names, fontsize=8)  # フォントサイズを小さくする
plt.xlabel('Feature Importance')
plt.ylabel('Feature')

plt.tight_layout()  # グラフのレイアウトを自動で調整
plt.show()


#model = load('2024_data_weight_reduction_cutting_deeplearning.joblib')
# 平均精度: 0.9876
# 精度: 0.9504
# 再現率: 0.9167
# F1スコア: 0.9328