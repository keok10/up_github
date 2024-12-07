import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta

# Fakerを利用してランダムデータを生成
fake = Faker()
Faker.seed(0)
random.seed(0)

# ユーザー数
NUM_USERS = 250000

# ランダムデータ生成関数
def generate_users(num_users):
    user_data = []
    for user_id in range(1, num_users + 1):
        name = fake.name()
        email = fake.email()
        created_at = fake.date_time_between(start_date="-5y", end_date="now").strftime("%Y-%m-%d %H:%M:%S")
        user_data.append([user_id, name, email, created_at])
    return pd.DataFrame(user_data, columns=["user_id", "name", "email", "created_at"])

def generate_user_roles(users_df):
    role_data = []
    role_names = ["法人", "個人"]

    for _, row in users_df.iterrows():
        user_id = row["user_id"]
        role_id = random.randint(1, 1000000)  # ランダムな一意の識別子
        role_name = random.choice(role_names)
        additional_info = (
            f"法人番号: {random.randint(100000, 999999)}"
            if role_name == "法人" else ""
        )
        role_data.append([role_id, role_name, additional_info, user_id])
    return pd.DataFrame(role_data, columns=["role_id", "role_name", "additional_info", "user_id"])

# データ生成
print("Generating users data...")
users_df = generate_users(NUM_USERS)

print("Generating user roles data...")
user_roles_df = generate_user_roles(users_df)

# CSVに保存
print("Saving to CSV files...")
users_csv_path = "users.csv"
user_roles_csv_path = "user_roles.csv"

users_df.to_csv(users_csv_path, index=False)
user_roles_df.to_csv(user_roles_csv_path, index=False)

print(f"Data generation complete! Saved to {users_csv_path} and {user_roles_csv_path}.")
