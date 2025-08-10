from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from bson import json_util
import pandas as pd
from prophet import Prophet
import json

app = FastAPI()

@app.get("/all_data")
def get_all_data():
    data = list(collection.find())
    return json.loads(json_util.dumps(data))


# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["supply_chain_db"]
collection = db["sales_data"]

# === Forecast Endpoint ===
@app.get("/forecast/{product_id}")
def forecast_demand(product_id: str):
    # Step 1: Fetch data for given product
    data = list(collection.find({"product_id": product_id}))
    if not data:
        return {"error": "Product not found"}

    # Step 2: Convert to DataFrame
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Step 3: Prepare for Prophet
    df_prophet = df[["date", "sales_quantity"]].rename(columns={
        "date": "ds",
        "sales_quantity": "y"
    })

    # Step 4: Train Prophet model
    model = Prophet()
    model.fit(df_prophet)

    # Step 5: Forecast future (next 30 days)
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)

    # Step 6: Return prediction
    result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(30)
    return json.loads(result.to_json(orient="records", date_format="iso"))


@app.get("/inventory_optimize/{product_id}")
def optimize_inventory(product_id: str):
    # === Fetch data ===
    data = list(collection.find({"product_id": product_id}))
    if not data:
        return {"error": "Product not found"}

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    current_inventory = int(df.iloc[-1]["inventory_level"])

    # === Forecast ===
    df_prophet = df[["date", "sales_quantity"]].rename(columns={"date": "ds", "sales_quantity": "y"})
    model = Prophet()
    model.fit(df_prophet)
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    next_30_days = forecast.tail(30)

    # === Advanced Variables ===
    lead_time_days = 5  # You can later fetch this per product
    holding_cost_per_unit = 2.5  # Simulated; not used yet
    safety_stock = next_30_days["yhat"].std() * 1.65  # 90% confidence
    avg_daily_demand = next_30_days["yhat"].mean()

    reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
    reorder_qty = reorder_point - current_inventory
    reorder_qty = max(0, reorder_qty)

    return {
        "product_id": str(product_id),
        "current_inventory": current_inventory,
        "predicted_avg_daily_demand": round(float(avg_daily_demand), 2),
        "predicted_demand_std_dev": round(float(next_30_days['yhat'].std()), 2),
        "lead_time_days": lead_time_days,
        "safety_stock": round(float(safety_stock), 2),
        "reorder_point": round(float(reorder_point), 2),
        "recommended_reorder_quantity": int(round(reorder_qty)),
        "note": "Uses Reorder Point formula with safety stock (90% confidence)"
    }

from transformers import pipeline
sentiment_analyzer = pipeline("sentiment-analysis")

@app.post("/market_analysis")
def analyze_market_trend(text: str):
    result = sentiment_analyzer(text)
    sentiment = result[0]['label']
    score = result[0]['score']

    if sentiment == "NEGATIVE":
        action = "⚠️ Consider lowering demand forecast or pausing stock."
    elif sentiment == "POSITIVE":
        action = "✅ Consider boosting inventory for increased demand."
    else:
        action = "🔍 Monitor closely."

    return {
        "text": text,
        "sentiment": sentiment,
        "confidence": round(score, 2),
        "suggested_action": action
    }
