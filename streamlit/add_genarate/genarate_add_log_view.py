import pandas as pd
import random
from datetime import datetime, timedelta
#print("動いてます...")
# ファイルのパスを指定
click_logs_file = "/Users/kenjiokabe/github/streamlit/csv_data/click_logs.csv"
page_views_file = "/Users/kenjiokabe/github/streamlit/csv_data/page_views.csv"
products_file = "/Users/kenjiokabe/github/streamlit/csv_data/products.csv"
#print("動いてます...")
# データの読み込み
click_logs_df = pd.read_csv(click_logs_file)
page_views_df = pd.read_csv(page_views_file)
products_df = pd.read_csv(products_file)
#print("動いてます...")
# 商品ページ URL のリストを生成
product_urls = products_df["product_url"].tolist()

# 既存のユーザーIDとページビュー情報
#print("動いてます...")
user_ids = page_views_df["user_id"].unique()
view_ids = set(page_views_df["view_id"])
start_date = datetime(2015, 1, 1)
end_date = datetime(2034, 12, 31)
#print("動いてます...")
date_range = end_date - start_date
#print("動いてます...")
additional_logs = 10000000
#print("動いてます...")

# ランダムデータの生成
new_page_views = []
new_click_logs = []

print("ランダムな商品ページのクリックログとページビューを生成しています...")

for i in range(additional_logs):
    user_id = random.choice(user_ids)
    random_seconds = random.randint(0, int(date_range.total_seconds()))
    view_date = start_date + timedelta(seconds=random_seconds)
    product_url = random.choice(product_urls)
    
    # 一意のページビューIDを生成
    view_id = f"pv_{len(page_views_df) + len(new_page_views) + 1}"

    # ページビューを追加
    new_page_views.append({
        "view_id": view_id,
        "user_id": user_id,
        "page": product_url,
        "view_date": view_date.strftime("%Y-%m-%d %H:%M:%S")
    })

    # クリックログを追加
    click_id = f"cl_{len(click_logs_df) + len(new_click_logs) + 1}"
    new_click_logs.append({
        "click_id": click_id,
        "user_id": user_id,
        "element": "product_link",
        "click_date": view_date.strftime("%Y-%m-%d %H:%M:%S")
    })

    if (i + 1) % 1000000 == 0:
        print(f"{i + 1}/{additional_logs} 件のデータを生成しました。")

print("ランダムデータの生成が完了しました。")

# DataFrame に変換
new_page_views_df = pd.DataFrame(new_page_views)
new_click_logs_df = pd.DataFrame(new_click_logs)

# 既存のデータと結合
page_views_df = pd.concat([page_views_df, new_page_views_df], ignore_index=True)
click_logs_df = pd.concat([click_logs_df, new_click_logs_df], ignore_index=True)

# ファイルに保存
page_views_df.to_csv("/Users/kenjiokabe/github/streamlit/page_views.csv", index=False)
click_logs_df.to_csv("/Users/kenjiokabe/github/streamlit/click_logs.csv", index=False)

print("ページビューとクリックログを更新し、保存しました。")
