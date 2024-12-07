import pandas as pd
import random

# ファイルパスの指定
file_path = "/Users/kenjiokabe/github/streamlit/products.csv"

# CSVを読み込む
print("Reading products.csv...")
products_df = pd.read_csv(file_path)

# price カラムを追加して、ランダムな値を設定
print("Adding price column...")
products_df['price'] = [random.randint(450, 190800) for _ in range(len(products_df))]

print("Saving updated products.csv...")
products_df.to_csv(file_path, index=False)

print(products_df.head(3))