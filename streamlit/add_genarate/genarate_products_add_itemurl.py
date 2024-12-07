import pandas as pd

# CSV ファイルを読み込む
file_path = "/Users/kenjiokabe/github/streamlit/products.csv"
df = pd.read_csv(file_path)

# 商品URLを生成して新しいカラムに追加
base_url = "https://example-test-flower.jp/item/"
df["product_url"] = df["product_number"].apply(lambda x: f"{base_url}{x}")

# 結果を確認
print(df.head())

# URLを追加したCSVを保存
output_file = "/Users/kenjiokabe/github/streamlit/products.csv"
df.to_csv(output_file, index=False)
