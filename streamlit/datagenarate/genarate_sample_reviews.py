import pandas as pd
import random
import datetime

# CSV ファイルの読み込み
def load_csv_files():
    orders_items = pd.read_csv("streamlit/order_items.csv")
    orders = pd.read_csv("streamlit/orders.csv")
    users = pd.read_csv("streamlit/users.csv")
    products = pd.read_csv("streamlit/products.csv")
    return orders_items, orders, users, products

# レビューを生成する
def generate_product_reviews(products, users, num_reviews=60000):
    reviews = []
    for i in range(1, num_reviews + 1):
        product = products.sample(1).iloc[0]  # ランダムに1つの商品を選択
        user = users.sample(1).iloc[0]        # ランダムに1人のユーザーを選択
        review = {
            "review_id": i,
            "product_id": product["product_number"],
            "user_id": user["user_id"],
            "rating": random.randint(1, 5),  # ランダムな評価 (1～5)
            "review_text": f"Sample review text for product {product['english_name']} by user {user['name']}.",
            "review_date": datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 365))  # 過去1年以内のランダムな日付
        }
        reviews.append(review)
    return pd.DataFrame(reviews)

# フィードバックを生成する
def generate_product_feedback(users, products, num_feedback=60000):
    feedbacks = []
    for i in range(1, num_feedback + 1):
        user = users.sample(1).iloc[0]  # ランダムに1人のユーザーを選択
        product = products.sample(1).iloc[0] if random.random() > 0.5 else None  # 商品は50%の確率で関連付け
        feedback = {
            "response_id": i,
            "customer_id": user["user_id"],
            "survey_date": datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 365)),  # 過去1年以内のランダムな日付
            "nps_score": random.randint(0, 10),  # ランダムなNPSスコア (0～10)
            "nps_category": random.choices(["Promoter", "Passive", "Detractor"], weights=[3, 2, 1])[0],  # NPSカテゴリ
            "reason": f"Sample reason text for user {user['name']}.",
            "product_id": product["product_number"] if product is not None else None,
            "purchase_date": datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 365)) if product is not None else None,
            "product_quality_score": random.randint(1, 5),
            "delivery_speed_score": random.randint(1, 5),
            "website_experience_score": random.randint(1, 5),
            "customer_service_score": random.randint(1, 5),
        }
        feedbacks.append(feedback)
    return pd.DataFrame(feedbacks)

# メイン処理
if __name__ == "__main__":
    # 必要なCSVファイルを読み込む
    orders_items, orders, users, products = load_csv_files()

    # レビューを生成して保存
    print("Generating product reviews...")
    reviews_df = generate_product_reviews(products, users)
    reviews_df.to_csv("products_product_reviews.csv", index=False)
    print(f"Saved {len(reviews_df)} ")

    # フィードバックを生成して保存
    print("Generating next..")
    feedback_df = generate_product_feedback(users, products)
    feedback_df.to_csv("products_product_feedback.csv", index=False)
    print(f"Saved {len(feedback_df)} csv")
