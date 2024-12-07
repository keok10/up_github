import streamlit as st

def create_sidebar(current_category, current_page):
   # st.sidebar.title("目次")

    # 大カテゴリと中カテゴリの対応関係
    categories = {
        "sales": {
            "name": "全体売上",
            "pages": {
                "sales": "売上",
                "category_sales": "カテゴリ別売上"
            }
        },
        "marketing": {
            "name": "マーケティング",
            "pages": {
                "timeline": "タイムライン",
                "ltv": "LTV",
                "nps": "NPS",
                "sankey_diagram": "サンキーダイアグラム"
            }
        },
        "finance": {
            "name": "ファイナンス",
            "pages": {
                "cashflow": "キャッシュフロー",
                "profitability": "収益性",
                "liquidity": "流動性"
            }
        }
    }
    # サイドバーの表示構造
    for category_key, category_data in categories.items():
        # 大カテゴリ名を表示（リンクなし、フォントサイズを大きくする）
        st.sidebar.markdown(
            f'<div style="font-size:18px; font-weight:bold; margin-bottom:5px;">{category_data["name"]}</div>',
            unsafe_allow_html=True
        )
        
        # 中カテゴリを表示（リンクあり）
        for page_key, page_name in category_data["pages"].items():
            link = f"?category={category_key}&page={page_key}"
            # 表示している中カテゴリ部分のみ「・」を付ける
            if category_key == current_category and page_key == current_page:
                st.sidebar.markdown(f"  - **{page_name}**")
            else:
                # 同じタブでリンクを開くために target="_self" を使用
                st.sidebar.markdown(
                    f'  <a href="{link}" target="_self">{page_name}</a>',
                    unsafe_allow_html=True
                )

        # カテゴリ間に区切り線を入れる
        st.sidebar.markdown("---")
