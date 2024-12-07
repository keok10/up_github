import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Googleスプレッドシートに接続する関数
def connect_to_google_sheet(json_keyfile, sheet_url):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_url)
    sheet = spreadsheet.worksheet("pages")
    return sheet

# 階層レベルを計算する関数
def calculate_level(url):
    return url.strip('/').count('/') - int(1)

# データフレームに整形し、CSVとして保存する関数
def generate_category_csv(sheet, output_csv):
    # スプレッドシートからデータを取得
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])  # 1行目をカラム名に設定

    # デバッグ: スプレッドシートの内容を表示
    print("取得したデータフレーム:\n", df.head())

    # カラム名のスペースや大文字小文字を標準化
    df.columns = df.columns.str.strip().str.lower()

    # デバッグ: 標準化後のカラム名を表示
    print("標準化後のカラム名:", df.columns.tolist())

    # 必要なカラムがあるか確認
    if 'url' not in df.columns or 'page_title' not in df.columns or 'page_category' not in df.columns:
        raise ValueError("スプレッドシートに必要なカラム (url, page_title, page_category) がありません。")

    # category.csv形式のデータを作成
    categories = []
    parent_ids = {1: None}  # ルートカテゴリーの親IDはNULL

    for i, row in df.iterrows():
        url = row["url"]
        name_en = row["page_title"]
        description = row["page_category"]

        # 階層レベルを計算
        level = calculate_level(url)

        # 親カテゴリーIDを計算
        parent_id = None
        if level > 1:
            parent_url = '/'.join(url.strip('/').split('/')[:-1]) + '/'
            parent_id = int(level) - int(1)

        # カテゴリーIDを生成
        category_id = i + 1
        parent_ids[category_id] = url

        # カテゴリー情報をリストに追加
        categories.append({
            "category_id": category_id,
            "parent_id": parent_id,
            "level": level,
            "name_en": name_en,
            "url": url,
            "description": description,
        })

    # DataFrameに変換してCSVとして保存
    category_df = pd.DataFrame(categories)
    category_df.to_csv(output_csv, index=False)
    print(f"'{output_csv}' にカテゴリ情報を保存しました。")

# 実行部分
if __name__ == "__main__":
    json_keyfile = "streamlit/flower.json"  # JSONファイルのパス
    sheet_url = "https://docs.google.com/spreadsheets/d/1MpRr6sqXBNJFRmNB1nuaRWWgIBBpqCyRHynKILONmXE/edit#gid=0"
    output_csv = "category.csv"  # 出力するCSVファイル名

    try:
        sheet = connect_to_google_sheet(json_keyfile, sheet_url)
        generate_category_csv(sheet, output_csv)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
