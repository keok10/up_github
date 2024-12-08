import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import os

# ベースディレクトリを設定
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
csv_path = os.path.join(BASE_DIR, "csv_data_up", "orders.csv")

# CSVファイルの存在を確認
if not os.path.exists(csv_path):
    st.error(f"CSVファイルが見つかりません: {csv_path}")
    st.stop()

# CSV読み込み
orders = pd.read_csv(csv_path)
orders['order_date'] = pd.to_datetime(orders['order_date'])

def main():
    st.title("売上集計")  # アプリのタイトル

    # 全データの期間を取得
    min_date = orders['order_date'].min().date()  # date型に変換
    max_date = orders['order_date'].max().date()  # date型に変換

    # 期間の単位を選択
    period_unit = st.selectbox(
        "集計の単位を選択してください",
        ["年", "月", "日"],
        index=0  # デフォルトを「年」に設定
    )

    # 期間のデフォルト値設定
    if period_unit == "年":
        default_start_date = min_date.replace(month=1, day=1)  # 年の開始日
        default_end_date = min_date.replace(year=min_date.year + 1, month=12, day=31)  # 次の年の終了日
    elif period_unit == "月":
        default_start_date = pd.to_datetime("2022-01-01").date()  # 固定で2022年1月の開始日
        default_end_date = pd.to_datetime("2022-12-31").date()  # 固定で2022年12月の終了日
    elif period_unit == "日":
        default_start_date = pd.to_datetime("2022-01-01").date()  # 固定で2022年1月1日
        default_end_date = pd.to_datetime("2022-01-31").date()  # 固定で2022年1月31日

    # カレンダー入力を使用
    start_date = st.date_input("開始日を選択", value=default_start_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("終了日を選択", value=default_end_date, min_value=start_date, max_value=max_date)

    # データを期間でフィルタリング
    filtered_orders = orders[
        (orders['order_date'].dt.date >= start_date) & (orders['order_date'].dt.date <= end_date)
    ]
    if period_unit == "年":
        filtered_orders['period'] = filtered_orders['order_date'].dt.year.astype(str)
    elif period_unit == "月":
        filtered_orders['period'] = filtered_orders['order_date'].dt.strftime("%Y/%m")  # YYYY/MM形式
    elif period_unit == "日":
        filtered_orders['period'] = filtered_orders['order_date'].dt.strftime("%m/%d")

    if filtered_orders.empty:
        st.warning("選択した期間内にデータがありません。")
        return

    # 期間内のデータ本数が31本以上の場合、警告を表示
    if len(filtered_orders['period'].unique()) > 31:
        st.warning("選択された期間内で棒グラフは31本以上表示できません。期間を再選択してください。")
        return

    # 集計データ作成（円を千万円に変換）
    sales_summary = filtered_orders.groupby('period')['total_amount'].sum().reset_index()
    sales_summary['total_amount'] = sales_summary['total_amount'] / 10000000  # 円を千万円に変換
    sales_summary['cumulative'] = sales_summary['total_amount'].cumsum()

    # グラフ作成
    fig = go.Figure()

    # 棒グラフ（売上）: 左側のY軸 (フロスティブルー)
    fig.add_trace(go.Bar(
        x=sales_summary['period'],
        y=sales_summary['total_amount'],
        name="売上 (千万円)",
        marker=dict(color="#A6C8FF", opacity=0.7),  # フロスティブルー
        yaxis="y1",
        hovertemplate="期間: %{x}<br>売上: %{y:.1f} 千万円<extra></extra>"
    ))

    # 折れ線グラフ（累積売上）: 右側のY軸 (少し薄い紺色)
    fig.add_trace(go.Scatter(
        x=sales_summary['period'],
        y=sales_summary['cumulative'],
        mode='lines+markers',
        name="累積売上 (千万円)",
        line=dict(shape='linear', dash='solid', color="#4B6EAF"),  # 少し薄い紺色
        marker=dict(size=6),
        yaxis="y2",
        hovertemplate="期間: %{x}<br>累積売上: %{y:.1f} 千万円<extra></extra>"
    ))

    # X軸とY軸の設定
    fig.update_layout(
        xaxis=dict(
            title="期間",
            tickmode='linear',
        ),
        yaxis=dict(
            title="売上金額 (千万円)",
            titlefont=dict(color="#555555"),  # 気持ち薄い黒
            tickfont=dict(color="#555555"),
            tickformat=".1f"  # 少数1桁
        ),
        yaxis2=dict(
            title="累積売上 (千万円)",
            titlefont=dict(color="#555555"),  # 気持ち薄い黒
            tickfont=dict(color="#555555"),
            overlaying="y",
            side="right",
            tickformat=".1f"  # 少数1桁
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        template="plotly_white",
        barmode='group'
    )

    # グラフを表示
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
