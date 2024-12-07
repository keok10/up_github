import os
import random
from faker import Faker
import pandas as pd
from datetime import datetime, timedelta

# Fakerの初期化
fake = Faker("ja_JP")

# 保存先フォルダの設定
BASE_DIR = "ec_flower_db"
os.makedirs(BASE_DIR, exist_ok=True)

# 年月範囲の設定
start_date = datetime(2044, 11, 1)
end_date = datetime(2049, 10, 31)

# カテゴリデータ（商品カテゴリ表）
categories = [
    {"category_id": i + 1, "name": row[1], "parent_id": row[0], "level": row[2]}
    for i, row in enumerate(
        [
            (None, "花・観葉植物", 1),
            (1, "花束・切花", 2),
            (1, "フラワーアレンジメント", 2),
            (1, "観葉植物", 2),
            (1, "鉢花", 2),
            (1, "プリザーブドフラワー", 2),
            (1, "ドライフラワー", 2),
        ]
    )
]

# データ件数の設定
counts = {
    "users": 20000,
    "products": 1936,
    "orders": 30000,
    "analytics": 120000,
    "categories": len(categories),
    "product_reviews": 500,
    "order_items": 30000,
}

# データ生成関数
def generate_data(table_name, num_rows):
    if table_name == "users":
        return [
            {
                "user_id": i + 1,
                "name": fake.name(),
                "email": fake.email(),
                "created_at": fake.date_between(start_date=start_date, end_date=end_date),
            }
            for i in range(num_rows)
        ]
    elif table_name == "products":
        return [
            {
                "product_id": i + 1,
                "name": f"{fake.word()}_{fake.word()}_{hex(i)[2:]}",
                "price": random.randint(1500, 25000),
                "category_id": random.randint(1, len(categories)),
            }
            for i in range(num_rows)
        ]
    elif table_name == "orders":
        return [
            {
                "order_id": i + 1,
                "user_id": random.randint(1, counts["users"]),
                "total_amount": round(random.uniform(1500, 25000), 2),
                "order_date": fake.date_time_between(start_date=start_date, end_date=end_date),
            }
            for i in range(num_rows)
        ]
    elif table_name == "analytics":
        return [
            {
                "view_id": i + 1,
                "user_id": random.randint(1, counts["users"]),
                "page": fake.uri(),
                "view_date": fake.date_time_between(start_date=start_date, end_date=end_date),
            }
            for i in range(num_rows)
        ]
    elif table_name == "categories":
        return categories
    elif table_name == "product_reviews":
        return [
            {
                "review_id": i + 1,
                "product_id": random.randint(1, counts["products"]),
                "user_id": random.randint(1, counts["users"]),
                "rating": random.randint(1, 5),
                "review_text": fake.sentence(),
            }
            for i in range(num_rows)
        ]
    elif table_name == "order_items":
        return [
            {
                "order_item_id": i + 1,
                "order_id": random.randint(1, counts["orders"]),
                "product_id": random.randint(1, counts["products"]),
                "quantity": random.randint(1, 5),
                "price": random.randint(1500, 25000),
            }
            for i in range(num_rows)
        ]
    else:
        return []

# データ保存関数
def save_to_csv(schema, table_name, data):
    schema_dir = os.path.join(BASE_DIR, schema)
    os.makedirs(schema_dir, exist_ok=True)
    file_path = os.path.join(schema_dir, f"{schema}.{table_name}.csv")
    pd.DataFrame(data).to_csv(file_path, index=False)
    print(f"Saved: {file_path}")

# スキーマとテーブル構造
schemas = {
    "users": ["users"],
    "products": ["products", "product_reviews"],
    "orders": ["orders", "order_items"],
    "analytics": ["analytics"],
    "categories": ["categories"],
}

# データ生成と保存
for schema, tables in schemas.items():
    for table in tables:
        data = generate_data(table, counts.get(table, 100))  # データ件数を取得
        save_to_csv(schema, table, data)
