import pandas as pd
import streamlit as st

# page_views.csv を読み込む
page_views_df = pd.read_csv("page_views.csv")

# 必要なURLの定義
base_urls = {
    "product_page": "https://example-test-flower.jp/item/",
    "cart": "https://example-test-flower.jp/cart/",
    "cart_v2": "https://example-test-flower.jp/carts_v2/",
    "order_complete": "https://example-test-flower.jp/sanks/"
}

# 商品ページ
product_page_count = len(page_views_df[page_views_df["page"].str.contains(base_urls['product_page'])])
# カートページ
cart_count = len(page_views_df[page_views_df["page"].str.contains(base_urls['cart'])])
# カート2ページ目
cart_v2_count = len(page_views_df[page_views_df["page"].str.contains(base_urls['cart_v2'])])
# サンクスページ
order_complete_count = len(page_views_df[page_views_df["page"].str.contains(base_urls['order_complete'])])
# その他
other_count = len(page_views_df) - (product_page_count + cart_count + cart_v2_count + order_complete_count)

countcheck_table = pd.DataFrame({
    "URL": ["product_page_count","cart_count","cart_v2_count","order_complete_count","other_count"],
    "Count": [product_page_count,cart_count,cart_v2_count,order_complete_count,other_count]
    })

st.title('ページ別ログ件数')
st.dataframe(countcheck_table)


# オレンジ色の水平線を表示
st.markdown(
    "<hr style='border: none; height: 3px; background-color: orange;' />"
    )

st.title('その他の表現')
# # 結果を出力
# print(f"product_page: {product_page_count}件")
# print(f"cart: {cart_count}件")
# print(f"cart_v2: {cart_v2_count}件")
# print(f"order_complete: {order_complete_count}件")
# print(f"other: {other_count}件")
st.write(f"product_page: {product_page_count}件")
st.write(f"cart: {cart_count}件")
st.write(f"cart_v2: {cart_v2_count}件")
st.write(f"order_complete: {order_complete_count}件")
st.write(f"other: {other_count}件")


# カラム名出力
# print('page_views.csv:', page_views_df.columns())
st.dataframe(page_views_df.columns, use_container_width=True)

# streamlit run streamlit/genarate_log_view_countcheck.py