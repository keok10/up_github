import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from joblib import dump, load

# df_feature_valueの読み込みは省略（あなたのコードに従って適切に読み込んでください）
#df_feature_value = pd.read_csv('2024_data_weight_reduction_cutting_deeplearning.csv', parse_dates=['datetime'])

# 特徴量とターゲットの定義
X = df_feature_value.drop(['datetime', 'price_change_label','Open','High','Low','Ask_Open','Ask_High','Ask_Low','Bid_Open','Bid_High','Bid_Low','Volume'], axis=1)
y = df_feature_value['price_change_label']

# TimeSeriesSplitのインスタンス化
tscv = TimeSeriesSplit(n_splits=8)

# ランダムフォレスト分類器のインスタンス化
rf = RandomForestClassifier(random_state=42)

# 探索するパラメータの範囲を定義
param_grid = {
    'n_estimators': [10, 50, 100, 200],
    'max_depth': [None, 10, 20, 30]
}

# GridSearchCVのインスタンス化（クロスバリデーションにTimeSeriesSplitを使用）
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=tscv, scoring='accuracy', n_jobs=-1)

# グリッドサーチの実行
grid_search.fit(X, y)

# 最適なパラメータとその時のスコアを表示
print(f"最適なパラメータ: {grid_search.best_params_}")
print(f"最適なパラメータのスコア: {grid_search.best_score_:.4f}")

# モデルの保存
dump(grid_search.best_estimator_, '2024_data_weight_reduction_cutting_deeplearning.joblib')

# モデルの読み込み
model = load('2024_data_weight_reduction_cutting_deeplearning.joblib')

# 最適なモデルを使用してテストデータでの予済みを行うなど、必要に応じて追加のステップをここに記述
