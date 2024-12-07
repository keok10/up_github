import streamlit as st
import pandas as pd
import plotly.express as px
import os

@st.cache_data
def load_data():
    # 絶対パスでCSVフォルダを指定
    csv_dir = "/Users/kenjiokabe/github/streamlit/csv_data"

    # CSVファイルのパスを取得
    orders_path = os.path.join(csv_dir, "orders.csv")
    order_items_path = os.path.join(csv_dir, "order_items.csv")
    products_path = os.path.join(csv_dir, "products.csv")

    # 各CSVを読み込む
    orders = pd.read_csv(orders_path)
    order_items = pd.read_csv(order_items_path)
    products = pd.read_csv(products_path)

    # `order_date` を日付型に変換
    orders["order_date"] = pd.to_datetime(orders["order_date"])

    # データの結合
    merged = order_items.merge(products, left_on="product_id", right_on="product_number")
    merged = merged.merge(orders, on="order_id")

    # `total_amount` を計算 (単価 * 数量)
    merged["total_amount"] = merged["quantity"] * merged["price_x"]
    return merged

# メイン関数
def main():
    st.title("売上集計")

    # データの読み込み
    data = load_data()

    # 全データの期間を取得
    min_date = data['order_date'].min().date()
    max_date = data['order_date'].max().date()

    # 集計単位と期間選択 (メイン画面)
    st.subheader("期間を指定してください")
    col1, col2, col3 = st.columns(3)

    with col1:
        period_unit = st.selectbox(
            "集計の単位",
            ["年", "月", "日"],
            index=0
        )

    # 期間のデフォルト値設定
    if period_unit == "年":
        default_start_date = min_date.replace(month=1, day=1)
        default_end_date = min_date.replace(year=min_date.year + 1, month=12, day=31)
    elif period_unit == "月":
        default_start_date = pd.to_datetime("2022-01-01").date()
        default_end_date = pd.to_datetime("2022-12-31").date()
    elif period_unit == "日":
        default_start_date = pd.to_datetime("2022-01-01").date()
        default_end_date = pd.to_datetime("2022-01-31").date()

    with col2:
        start_date = st.date_input("開始日", value=default_start_date, min_value=min_date, max_value=max_date)

    with col3:
        end_date = st.date_input("終了日", value=default_end_date, min_value=start_date, max_value=max_date)

    # データを期間でフィルタリング
    filtered_orders = data[
        (data['order_date'].dt.date >= start_date) & (data['order_date'].dt.date <= end_date)
    ]
    if period_unit == "年":
        filtered_orders['period'] = filtered_orders['order_date'].dt.year.astype(str)
    elif period_unit == "月":
        filtered_orders['period'] = filtered_orders['order_date'].dt.strftime("%Y/%m")
    elif period_unit == "日":
        filtered_orders['period'] = filtered_orders['order_date'].dt.strftime("%m/%d")

    if filtered_orders.empty:
        st.warning("選択した期間内にデータがありません。")
        return

    # サブカテゴリ別の売上金額集計
    sub_category_sales = filtered_orders.groupby("sub_category").agg(
        売上金額=("total_amount", "sum")
    ).reset_index()

    # 全体の売上金額
    total_sales = sub_category_sales["売上金額"].sum()
    sub_category_sales["売上割合"] = sub_category_sales["売上金額"] / total_sales

    # 売上金額をフォーマットした文字列列を追加
    sub_category_sales["売上情報"] = sub_category_sales.apply(
        lambda row: f"{int(row['売上金額'] / 10000):,}万円  \n  {row['売上割合']:.1%}",
        axis=1
    )

    # サブカテゴリの横向き100%積み上げ棒グラフ
    st.header("サブカテゴリの売上割合 (100%積み上げ横棒グラフ)")
    fig = px.bar(
        sub_category_sales,
        y="sub_category",
        x="売上割合",
        color="sub_category",
        text="売上情報",  # 売上割合 + 売上金額
        orientation="h",
        labels={"sub_category": "サブカテゴリ", "売上割合": "売上割合 (%)"},
        title="サブカテゴリ別売上割合",
    )

    # テキスト位置を中央に設定
    fig.update_traces(
        textposition='inside',
        insidetextanchor='middle',  # 真ん中に配置
        hovertemplate='サブカテゴリ: %{y}<br>売上金額: ¥%{customdata:,}<br>売上割合: %{x:.1%}',
        customdata= sub_category_sales["売上金額"],  # ホバーテキスト用
    )

    # レイアウト調整
    fig.update_layout(
        xaxis_tickformat=".0%",
        xaxis_title="売上割合 (%)",
        yaxis_title="サブカテゴリ",
        legend_title="サブカテゴリ",
        uniformtext_minsize=16,
        uniformtext_mode="hide",  # テキストが重ならないように自動調整
    )

    st.plotly_chart(fig, use_container_width=True)

    # ランキングテーブル
    st.header("売上ランキング")

    # サブカテゴリ選択
    sub_category_options = ["ALL"] + sorted(filtered_orders["sub_category"].unique().tolist())
    selected_sub_category = st.selectbox("サブカテゴリを選択してください", sub_category_options)

    # ランキングの表示件数を選択
    ranking_limit = st.selectbox("表示件数を選択してください", [10, 20, 30, 50, 100], index=0)

    # 絞り込み
    if selected_sub_category == "ALL":
        ranking_data = filtered_orders.groupby(
            ["main_category", "sub_category", "small_category", "product_name_candidate"]
        ).agg(
            売上金額=("total_amount", "sum")
        ).reset_index()
    else:
        ranking_data = filtered_orders[filtered_orders["sub_category"] == selected_sub_category].groupby(
            ["main_category", "sub_category", "small_category", "product_name_candidate"]
        ).agg(
            売上金額=("total_amount", "sum")
        ).reset_index()

    # ランキングのソート
    sorted_data = ranking_data.sort_values(by="売上金額", ascending=False).head(ranking_limit)

    # データフレーム表示
    st.dataframe(sorted_data, use_container_width=True)


if __name__ == "__main__":
    main()
