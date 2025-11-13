# =====================================================
# E-Commerce Interactive Dashboard (Streamlit Version)
# =====================================================
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------------------------------
# Load and Clean Dataset
# -----------------------------------------------------
df = pd.read_csv("Ecommerce_Sales_Cleaned_Final.csv", low_memory=False)
df.columns = df.columns.str.strip().str.lower()

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

for col in ["amount", "recived amount", "expance", "qty"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if "profit" not in df.columns:
    df["profit"] = df["amount"] - df["expance"]

df = df[df["amount"] > 0]

# -----------------------------------------------------
# Streamlit Page Config
# -----------------------------------------------------
st.set_page_config(page_title="E-Commerce Sales Dashboard", layout="wide")
st.title("📦 E-Commerce Sales Dashboard")

# -----------------------------------------------------
# Sidebar Filters
# -----------------------------------------------------
categories = sorted(df["category"].dropna().unique())
statuses = sorted(df["status"].dropna().unique())

selected_categories = st.sidebar.multiselect("Select Category:", categories, default=None)
selected_status = st.sidebar.multiselect("Select Order Status:", statuses, default=None)

# -----------------------------------------------------
# Filter Data
# -----------------------------------------------------
dff = df.copy()

if selected_categories:
    dff = dff[dff["category"].isin(selected_categories)]

if selected_status:
    dff = dff[dff["status"].isin(selected_status)]

# -----------------------------------------------------
# KPIs
# -----------------------------------------------------
total_sales = dff["amount"].sum()
total_profit = dff["profit"].sum()
avg_profit = dff["profit"].mean()
total_orders = len(dff)

st.markdown("### Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales", f"₹{total_sales:,.0f}")
col2.metric("Total Profit", f"₹{total_profit:,.0f}")
col3.metric("Average Profit", f"₹{avg_profit:,.0f}")
col4.metric("Total Orders", f"{total_orders:,}")

# -----------------------------------------------------
# Monthly Sales Trend
# -----------------------------------------------------
monthly_sales = dff.groupby(dff["date"].dt.to_period("M"))["amount"].sum().reset_index()
monthly_sales["date"] = monthly_sales["date"].dt.to_timestamp()
fig_trend = px.line(monthly_sales, x="date", y="amount", title="📈 Monthly Sales Trend", markers=True, color_discrete_sequence=["#27ae60"])
st.plotly_chart(fig_trend, use_container_width=True)

# -----------------------------------------------------
# Top Categories
# -----------------------------------------------------
top_categories = (
    dff.groupby("category", as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
    .head(10)
)
fig_cat = px.bar(top_categories, x="category", y="amount", title="🏷️ Top 10 Categories by Sales", color="amount", color_continuous_scale="Agsunset")
st.plotly_chart(fig_cat, use_container_width=True)

# -----------------------------------------------------
# Expense vs Profit
# -----------------------------------------------------
fig_ep = px.scatter(dff, x="expance", y="profit", color="category", size="amount", hover_name="order id", title="💸 Expense vs Profit Distribution", color_continuous_scale="Viridis")
st.plotly_chart(fig_ep, use_container_width=True)

# -----------------------------------------------------
# Top 10 Products by Sales
# -----------------------------------------------------
if "style" in df.columns:
    top_products = (
        dff.groupby("style", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .head(10)
    )
    fig_products = px.bar(top_products, x="style", y="amount", title="🛒 Top 10 Products by Sales", color="amount", color_continuous_scale="Blues")
    st.plotly_chart(fig_products, use_container_width=True)
