import streamlit as st
import pandas as pd
import numpy as np  # numpyをインポート
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# サンプルデータ生成
def generate_sample_data():
    dates = pd.date_range(datetime.today() - timedelta(days=365), datetime.today(), freq="D")
    categories = ["Electronics", "Fashion", "Home & Kitchen", "Books", "Toys"]
    data = {
        "Date": dates,
        "Sales": [abs(int(x)) for x in np.random.normal(1000, 300, len(dates))],  # np.randomに変更
        "Category": [np.random.choice(categories) for _ in range(len(dates))],  # np.randomに変更
    }
    return pd.DataFrame(data)

# データ準備
data = generate_sample_data()

# サイドバー
st.sidebar.title("オプション")
view_option = st.sidebar.selectbox("表示単位", ["年間", "四半期", "月間", "日別"])
start_date = st.sidebar.date_input("開始日", datetime.today() - timedelta(days=365))
end_date = st.sidebar.date_input("終了日", datetime.today())

# データフィルタリング
filtered_data = data[(data["Date"] >= pd.Timestamp(start_date)) & (data["Date"] <= pd.Timestamp(end_date))]

# 集計
if view_option == "年間":
    filtered_data["Year"] = filtered_data["Date"].dt.year
    aggregated_data = filtered_data.groupby("Year")["Sales"].sum()
elif view_option == "四半期":
    filtered_data["Quarter"] = filtered_data["Date"].dt.to_period("Q")
    aggregated_data = filtered_data.groupby("Quarter")["Sales"].sum()
elif view_option == "月間":
    filtered_data["Month"] = filtered_data["Date"].dt.to_period("M")
    aggregated_data = filtered_data.groupby("Month")["Sales"].sum()
else:
    aggregated_data = filtered_data.groupby("Date")["Sales"].sum()

# 棒グラフ (表1)
st.subheader("売上推移")
fig, ax = plt.subplots()
aggregated_data.plot(kind="bar", ax=ax)
ax.set_ylabel("売上")
ax.set_title(f"売上推移: {view_option}")
st.pyplot(fig)

# 円グラフ (表2)
st.subheader("大カテゴリ別売上割合")
category_sales = filtered_data.groupby("Category")["Sales"].sum()
fig2, ax2 = plt.subplots()
category_sales.plot(kind="pie", autopct="%1.1f%%", ax=ax2, startangle=90)
ax2.set_ylabel("")
ax2.set_title("カテゴリ別売上割合")
st.pyplot(fig2)


# cd ~
# cd /Users/kenjiokabe/github/streamlit
# streamlit run usertimeline_streamlit_timeline.py