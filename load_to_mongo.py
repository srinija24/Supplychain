import pandas as pd
from pymongo import MongoClient

# 1. Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["supply_chain_db"]
collection = db["sales_data"]

# 2. Load CSV
df = pd.read_csv("supply_chain_data.csv")
data = df.to_dict(orient="records")

# 3. Insert into MongoDB
collection.delete_many({})  # Clear old data if any
collection.insert_many(data)

print("✅ Data loaded successfully into MongoDB!")
