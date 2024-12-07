import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# ファイルのパスを指定
orders_file = "/Users/kenjiokabe/github/streamlit/csv_data/orders.csv"
order_items_file = "/Users/kenjiokabe/github/streamlit/csv_data/order_items.csv"
products_file = "/Users/kenjiokabe/github/streamlit/csv_data/products.csv"

# データの読み込み
orders = pd.read_csv(orders_file)
order_items = pd.read_csv(order_items_file)
products = pd.read_csv(products_file)

# 必要なURLの定義
base_urls = {
    "product_page": "https://example-test-flower.jp/item/",
    "cart": "https://example-test-flower.jp/cart/",
    "cart_v2": "https://example-test-flower.jp/carts_v2/",
    "order_complete": "https://example-test-flower.jp/sanks/"
}

# ページビューとクリックログを格納するリスト
page_views_data = []
click_logs_data = []

# 購入フローのデータ生成
def generate_purchase_flow(order, order_items):
    user_id = order["user_id"]
    order_id = order["order_id"]
    order_date = datetime.strptime(order["order_date"], "%Y-%m-%d %H:%M:%S")
    items = order_items[order_items["order_id"] == order_id]
    view_date = order_date - timedelta(minutes=random.randint(10, 60))

    # 商品ページの閲覧（注文商品の商品ページを閲覧）
    for _, item in items.iterrows():
        product_id = item["product_id"]
        url = base_urls["product_page"] + str(product_id)
        view_id = f"pv_{len(page_views_data) + 1}"

        # ページビューを追加
        page_views_data.append({
            "view_id": view_id,
            "user_id": user_id,
            "page": url,
            "view_date": view_date.strftime("%Y-%m-%d %H:%M:%S")
        })

        # クリックログを追加
        click_id = f"cl_{len(click_logs_data) + 1}"
        click_logs_data.append({
            "click_id": click_id,
            "user_id": user_id,
            "element": "product_link",
            "click_date": view_date.strftime("%Y-%m-%d %H:%M:%S")
        })

        # 時間を進める
        view_date += timedelta(seconds=random.randint(10, 120))

    # カートページの閲覧
    for page_key in ["cart", "cart_v2", "order_complete"]:
        url = base_urls[page_key]
        view_id = f"pv_{len(page_views_data) + 1}"

        # ページビューを追加
        page_views_data.append({
            "view_id": view_id,
            "user_id": user_id,
            "page": url,
            "view_date": view_date.strftime("%Y-%m-%d %H:%M:%S")
        })

        # クリックログを追加
        click_id = f"cl_{len(click_logs_data) + 1}"
        click_logs_data.append({
            "click_id": click_id,
            "user_id": user_id,
            "element": "button",
            "click_date": view_date.strftime("%Y-%m-%d %H:%M:%S")
        })

        # 時間を進める
        view_date += timedelta(seconds=random.randint(10, 120))

# 購入フローを持つユーザーのデータ生成
num_orders = len(orders)
print("購入フローのデータを生成中...")
for idx, order in orders.iterrows():
    generate_purchase_flow(order, order_items)
    if (idx + 1) % 100000 == 0:
        print(f"{idx + 1}/{num_orders} 件の注文を処理しました。")

# カート、カート2ページ目、注文完了ページの合計件数
cart_pages = ["https://example-test-flower.jp/cart/",
              "https://example-test-flower.jp/carts_v2/",
              "https://example-test-flower.jp/sanks/"]
cart_page_views = [pv for pv in page_views_data if pv["page"] in cart_pages]
print(f"カート関連のページビュー数: {len(cart_page_views)}")

# ランダムなページビューとクリックログを生成
random_page_urls = [
    "https://example-test-flower.jp/",
    "https://example-test-flower.jp/category/flowers_and_plants",
    "https://example-test-flower.jp/category/birthday-flower/jan",
    "https://example-test-flower.jp/login",
    "https://example-test-flower.jp/register",
    "https://example-test-flower.jp/faq",
    "https://example-test-flower.jp/about",
    "https://example-test-flower.jp/category/sale",
    "https://example-test-flower.jp/category/new-arrivals",
    "https://example-test-flower.jp/category/ranking",
    "https://example-test-flower.jp/search/advanced"
]

user_ids = orders["user_id"].unique()
start_date = datetime(2015, 1, 1)
end_date = datetime(2035, 12, 31)
date_range = end_date - start_date
remaining_logs = 4500000

print(f"ランダムなページビューとクリックログを {remaining_logs} 件生成します。")

for i in range(remaining_logs):
    user_id = random.choice(user_ids)
    random_seconds = random.randint(0, int(date_range.total_seconds()))
    view_date = start_date + timedelta(seconds=random_seconds)
    page = random.choice(random_page_urls)
    view_id = f"pv_{len(page_views_data) + 1}"

    # ページビューを追加
    page_views_data.append({
        "view_id": view_id,
        "user_id": user_id,
        "page": page,
        "view_date": view_date.strftime("%Y-%m-%d %H:%M:%S")
    })

    # クリックログを追加
    click_id = f"cl_{len(click_logs_data) + 1}"
    click_logs_data.append({
        "click_id": click_id,
        "user_id": user_id,
        "element": "link" if random.random() < 0.5 else "button",
        "click_date": view_date.strftime("%Y-%m-%d %H:%M:%S")
    })

    if (i + 1) % 1000000 == 0:
        print(f"{i + 1}/{remaining_logs} 件のランダムログを生成しました。")

print("ランダムなデータの生成が完了しました。")

# DataFrameに変換
page_views_df = pd.DataFrame(page_views_data)
click_logs_df = pd.DataFrame(click_logs_data)

# ファイルに保存
page_views_df.to_csv("/Users/kenjiokabe/github/streamlit/csv_data/page_views.csv", index=False)
click_logs_df.to_csv("/Users/kenjiokabe/github/streamlit/csv_data/click_logs.csv", index=False)

print("すべてのデータの生成と保存が完了しました。")
