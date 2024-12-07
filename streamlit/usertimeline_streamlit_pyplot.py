import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt

# ランダムデータ生成関数
def generate_dummy_data(num_entries=20):
    names = ["A", "B", "C", "D", "F"]  # 人の名前
    dates = pd.date_range("2024-12-01", "2024-12-05", freq="6H")  # 日付範囲
    actions = ["Purchase", "Buyback", "Sale", "App"]  # 内容
    types = ["能動", "受動"]  # 種別

    data = [
        [
            random.choice(names),
            random.choice(dates).strftime("%Y.%m.%d"),
            random.choice(actions),
            random.choice(types),
            f"{random.randint(0, 23):02}:{random.randint(0, 59):02}",  # 時間
        ]
        for _ in range(num_entries)
    ]
    return pd.DataFrame(data, columns=["名前", "日付", "内容", "種別", "時間"])

# ダミーデータ生成
df = generate_dummy_data()

# Streamlitアプリ
st.title("能動・受動 UML図 - ユーザー選択")

# ユーザー選択（1人だけ選択可能に設定）
users = sorted(df["名前"].unique())
selected_user = st.selectbox("ユーザーを選択してください", users)

# フィルタリング（選択したユーザーのデータ）
filtered_df = df[df["名前"] == selected_user]

# 表を表示（ページ上部）
st.write(f"選択されたユーザー {selected_user} のデータ:")
st.dataframe(filtered_df, use_container_width=True)  # 表の幅を調整

# タイムラインを表示（ページ下部）
st.write("タイムライン:")
total_items = len(filtered_df)  # 選択したユーザーのデータ数を基準にする
fig, ax = plt.subplots(figsize=(8, total_items * 1.5))  # 高さを選択データに基づく

# 均等間隔のY位置（1.5倍の間隔）
y_positions = [1.5 * i for i in range(total_items, 0, -1)]

# 黒線を先に描画して、オレンジのボールを背面に配置
previous_y = None  # 前のボールのY位置を記録
for y_pos in y_positions:
    if previous_y is not None:
        ax.plot([0.5, 0.5], [previous_y, y_pos], color="black", linewidth=1.5, linestyle="--")
    previous_y = y_pos  # 現在のY位置を記録

# オレンジのボールと吹き出しを描画
for y_pos, (_, row) in zip(y_positions, filtered_df.iterrows()):
    ax.plot(0.5, y_pos, "o", color="orange", markersize=10)  # オレンジのボール

    # 日付を縦線の上に枠付きで配置（透過なし）
    ax.text(
        0.5, y_pos + 0.3, row["日付"],
        ha="center", va="bottom", fontsize=10, color="black",
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="gray", facecolor="lightgray")  # 透過なし
    )

    # 吹き出しを描画（矢印の長さ固定、終点を端に固定）
    arrow_offset = 0.2  # 矢印の終点の長さ
    x_pos = 0.5 + (arrow_offset if row["種別"] == "能動" else -arrow_offset)
    align = "left" if row["種別"] == "受動" else "right"  # テキストの配置
    text_length_offset = 0.2 * len(row["内容"]) / 10  # 吹き出しの文字数に応じて位置調整
    arrow_end_x = x_pos + (text_length_offset if row["種別"] == "能動" else -text_length_offset)
    ax.annotate(
        f"{row['時間']}\n{row['内容']}",
        xy=(0.5, y_pos),
        xytext=(arrow_end_x, y_pos),
        arrowprops=dict(arrowstyle="->", color="black"),
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="blue" if row["種別"] == "受動" else "green", 
                  facecolor="lightblue" if row["種別"] == "受動" else "lightgreen"),
        ha=align,
        fontsize=10,
    )

# 軸の調整
ax.set_xlim(0, 1)
ax.set_ylim(0, max(y_positions) + 1.5)  # 高さを調整
ax.axis("off")

# タイムラインをStreamlitで表示
st.pyplot(fig)
