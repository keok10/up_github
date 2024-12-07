import streamlit as st
from display import create_sidebar
from importlib import import_module
# Streamlitのワイドモードをデフォルトに設定
st.set_page_config(layout="wide")
# URLクエリパラメータで現在のカテゴリを判定
query_params = st.query_params  # st.experimental_get_query_params を st.query_params に置き換え
category = query_params.get("category", "marketing")  # 存在しない場合は "marketing"
if isinstance(category, list):  # クエリパラメータはリスト形式で返される可能性がある
    category = category[0]

# デフォルトページを設定
default_page = {
    "marketing": "timeline",
    "sales": "sales",
    "finance": "cashflow"
}.get(category, "none")  # カテゴリが無効の場合は "none"

page_name = query_params.get("page", default_page)  # 存在しない場合はデフォルトページ
if isinstance(page_name, list):  # クエリパラメータはリスト形式で返される可能性がある
    page_name = page_name[0]

# サイドバーを作成
create_sidebar(category, page_name)

# 有効なカテゴリとページのリスト
valid_categories = {
    "marketing": {"timeline", "ltv", "nps", "sankey_diagram"},
    "sales": {"sales", "category_sales"},
    "finance": {"cashflow", "profitability", "liquidity"}
}

# カテゴリのバリデーション
if category not in valid_categories:
    st.error(f"指定されたカテゴリが無効です: {category}")
    st.write("Current query params:", query_params)
else:
    # ページのバリデーション
    if page_name not in valid_categories[category]:
        st.error(f"指定されたページが無効です: {page_name}")
        st.write("Current query params:", query_params)
    else:
        # 指定されたカテゴリとページを読み込み
        try:
            module = import_module(f"pages.{category}.{page_name}")
            module.main()
        except ModuleNotFoundError as e:
            st.error("ページが見つかりません。")
            st.write(f"Error details: {e}")

# デバッグ用に現在のクエリパラメータを表示
# st.write("Current query params:", query_params)
