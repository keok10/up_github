import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

# Google スプレッドシートに接続する関数
def connect_to_google_sheet(json_keyfile, sheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    # 環境変数から認証情報を取得
    creds = Credentials.from_authorized_user(Request())
    #creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).get_worksheet(0)
    return sheet

# A〜H列を取得して DataFrame に格納
def get_a_to_h_as_dataframe(sheet):
    data = sheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.iloc[:, :8]
    return df.reset_index(drop=True)

# H列を増やし、A〜G列を複製して新しい DataFrame を作成
def expand_products_info(df):
    expanded_rows = []
    product_id = 1
    for _, row in df.iterrows():
        original_values = row.iloc[:8].tolist()
        h_base = row["商品名候補"]
        for i in range(16):
            hex_suffix = f"_{i:x}"
            new_row = original_values.copy()
            new_row[-1] = f"{h_base}{hex_suffix}"
            new_row.append(product_id)
            expanded_rows.append(new_row)
            product_id += 1
    expanded_df = pd.DataFrame(expanded_rows, columns=list(df.columns) + ["商品番号"])
        # カラム名を英語表記に変更
    expanded_df.columns = [
        "main_category",
        "sub_category",
        "flower_type",
        "english_name",
        "main_category_en",
        "sub_category_en",
        "small_category",
        "product_name_candidate",
        "product_number"
    ]
    return expanded_df

# 実行部分
if __name__ == "__main__":
    json_keyfile = "test_flower.json"
    sheet_name = "EC商品データテンプレ"
    try:
        sheet = connect_to_google_sheet(json_keyfile, sheet_name)
        df_products_info = get_a_to_h_as_dataframe(sheet)
        expanded_df = expand_products_info(df_products_info)
        file_name = "/Users/kenjiokabe/github/streamlit/products.csv"
        expanded_df.to_csv(file_name, index=False)
        print(expanded_df.head(20))
        print(f"新しい DataFrame の総行数: {len(expanded_df)}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
# /Users/kenjiokabe/miniforge3/bin/python /Users/kenjiokabe/github/streamlit/genarate_sample_columns.py
