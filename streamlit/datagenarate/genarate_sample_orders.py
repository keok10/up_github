import os
import pandas as pd
import random
from faker import Faker
from datetime import datetime

# Faker の初期化
fake = Faker()
Faker.seed(0)
random.seed(0)

# ファイルの保存先ディレクトリを指定
base_path = "/Users/kenjiokabe/github/streamlit/csv_data"
products_csv_path = os.path.join(base_path, "products.csv")
orders_csv_path = os.path.join(base_path, "orders.csv")
order_items_csv_path = os.path.join(base_path, "order_items.csv")

# 注文数と1つの注文に含まれる最大商品数
NUM_ORDERS = 250000
MAX_ITEMS_PER_ORDER = 3

# データの読み込み
print("Reading products.csv...")
products_df = pd.read_csv(products_csv_path)

# 注文データを生成
def generate_orders(num_orders, user_ids):
    order_data = []
    for order_id in range(1, num_orders + 1):
        user_id = random.choice(user_ids)
        total_amount = 0  # 後で計算
        # 日付範囲を 2015/01/01 ~ 2035/01/01 に設定
        order_date = fake.date_time_between(
            start_date=datetime(2015, 1, 1),
            end_date=datetime(2035, 1, 1)
        ).strftime("%Y-%m-%d %H:%M:%S")
        order_data.append([order_id, user_id, total_amount, order_date])
    return pd.DataFrame(order_data, columns=["order_id", "user_id", "total_amount", "order_date"])

# 注文商品データを生成
def generate_order_items(orders_df, products_df):
    order_items_data = []
    product_ids = products_df["product_number"].tolist()
    product_prices = products_df.set_index("product_number")["price"].to_dict()

    for _, order in orders_df.iterrows():
        order_id = order["order_id"]
        num_items = random.randint(1, MAX_ITEMS_PER_ORDER)  # 注文に含まれる商品数
        order_total = 0

        for _ in range(num_items):
            order_item_id = len(order_items_data) + 1
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 5)
            price = product_prices.get(product_id, random.uniform(10.0, 200.0))
            total_price = price * quantity
            order_total += total_price

            order_items_data.append([order_item_id, order_id, product_id, quantity, price])

        # 注文の合計金額を更新
        orders_df.loc[order["order_id"] - 1, "total_amount"] = order_total

    return orders_df, pd.DataFrame(
        order_items_data,
        columns=["order_item_id", "order_id", "product_id", "quantity", "price"]
    )

# ユーザーIDを生成
print("Generating user IDs...")
NUM_USERS = 100000
user_ids = [i for i in range(1, NUM_USERS + 1)]

# 注文データ生成
print("Generating orders data...")
orders_df = generate_orders(NUM_ORDERS, user_ids)

# 注文商品データ生成
print("Generating order items data...")
orders_df, order_items_df = generate_order_items(orders_df, products_df)

# 保存ディレクトリの作成
os.makedirs(base_path, exist_ok=True)

# CSV ファイルとして保存
print("Saving to CSV files...")
orders_df.to_csv(orders_csv_path, index=False)
order_items_df.to_csv(order_items_csv_path, index=False)

print(f"Data generation complete! Saved to:\n{orders_csv_path}\n{order_items_csv_path}")

# df = pd.read_csv("/Users/kenjiokabe/github/streamlit/csv_data/orders.csv")
# df_mean = df["total_amount"].mean()
# print(df_mean)
# print(df["total_amount"].min())
# print(df["total_amount"].max())
# print(df_mean / 20 * 250000)