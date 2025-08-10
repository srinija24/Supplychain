import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# === Config ===
FASTAPI_URL = "http://localhost:8000"

st.set_page_config(page_title="📦 Supply Chain Analytics", layout="wide")

# === Sidebar ===
st.sidebar.title("Supply Chain Tools")
tabs = ["📈 Demand Forecast", "📦 Inventory Optimizer", "🧠 Market Sentiment"]
selected_tab = st.sidebar.radio("Navigate", tabs)

# === Tab 1: Forecast ===
if selected_tab == "📈 Demand Forecast":
    st.title("📈 Demand Forecast (Prophet)")
    product_id = st.text_input("Enter Product ID:", "P001")

    if st.button("Get Forecast"):
        res = requests.get(f"{FASTAPI_URL}/forecast/{product_id}")
        if res.status_code == 200:
            data = pd.DataFrame(res.json())
            st.success("Forecast Loaded!")
            fig = px.line(data, x="ds", y="yhat", title="30-Day Forecast")
            st.plotly_chart(fig)
            st.dataframe(data)
        else:
            st.error("Product ID not found.")

# === Tab 2: Inventory Suggestion ===
elif selected_tab == "📦 Inventory Optimizer":
    st.title("📦 Inventory Optimization")

    product_id = st.text_input("Enter Product ID:", "P001", key="inventory")

    if st.button("Get Inventory Suggestion"):
        res = requests.get(f"{FASTAPI_URL}/inventory_optimize/{product_id}")
        if res.status_code == 200:
            result = res.json()
            st.metric("📦 Current Inventory", result['current_inventory'])
            st.metric("📈 Reorder Point", result['reorder_point'])
            st.metric("✅ Reorder Quantity", result['recommended_reorder_quantity'])

            st.info(result['note'])
            st.json(result)
        else:
            st.error("Product ID not found.")

# === Tab 3: Market NLP ===
elif selected_tab == "🧠 Market Sentiment":
    st.title("🧠 Market Sentiment Analysis")

    input_text = st.text_area("Enter market news, customer reviews, or text:")
    if st.button("Analyze"):
        res = requests.post(f"{FASTAPI_URL}/market_analysis", params={"text": input_text})
        if res.status_code == 200:
            result = res.json()
            st.success(f"Sentiment: {result['sentiment']} ({result['confidence']*100:.2f}%)")
            st.info(result["suggested_action"])
        else:
            st.error("Analysis failed.")
