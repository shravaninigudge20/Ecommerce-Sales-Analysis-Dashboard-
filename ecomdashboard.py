# =====================================================
# E-Commerce Interactive Dashboard (Streamlit Version)
# =====================================================
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------------------------------
# Load Dataset from Google Sheets CSV with Error Handling
# -----------------------------------------------------
csv_url = "https://docs.google.com/spreadsheets/d/1-CPu7c-5FD4_XyPEY6gPVRYOfPj1_d5S/export?format=csv"

@st.cache_data
def load_data(url):
    return pd.read_csv(url, low_memory=False)

try:
    df = load_data(csv_url)
except Exception as e:
    st.error("❌ Failed to load data. Check your CSV link.")
    st.stop()

# -----------------------------------------------------
# Clean Columns
# -----------------------------------------------------
df.columns = df.columns.str.strip().str.lower()

# Fix spelling issues in column names
df.rename(columns={
    "recived amount": "received_amount",
    "expance": "expense"
}, inplace=True)

# -----------------------------------------------------
# Convert Date
# -----------------------------------------------------
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

# -----------------------------------------------------
# Ensure Numeric Columns
# -----------------------------------------------------
for col in ["amount", "received_amount", "expense", "qty"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# -----------------------------------------------------
# Standardize Order Status
# -----------------------------------------------------
if "status" in df.columns:
    df["status"] = df["status"].astype(str).str.strip().str.lower()

    status_mapping = {
        "delivered": "Delivered",
        "deliverd": "Delivered",
        "delvrd": "Delivered",
        "completed": "Delivered",
        "done": "Delivered",

        "paid": "Paid",
        "payment done": "Paid",
        "payed": "Paid",

        "cancel": "Cancelled",
        "canceled": "Cancelled",
        "cancelled": "Cancelled",

        "pending": "Pending",
        "in process": "Pending",
        "in-progress": "Pending"
    }

    df["status"] = df["status"].replace(status_mapping)
    df["status"] = df["status"].str.title()

# -----------------------------------------------------
# Add Profit Column
# -----------------------------------------------------
if "profit" not in df.columns:
    if "expense" in df.columns:
        df["profit"] = df["amount"] - df["expense"]
    else:
        df["profit"] = df["amount"]

# -----------------------------------------------------
# Filter for Valid Sales
# -----------------------------------------------------
df = df[df["amount"] > 0]

# -----------------------------------------------------
# Streamlit Page Config
# -----------------------------------------------------
st.set_page_config(page_title="E-Commerce Sales Dashboard", layout="wide")
st.title("📦 E-Commerce Sales Analysis")

# -----------------------------------------------------
# Sidebar Filters
# -----------------------------------------------------
categories = sorted(df["category"].dropna().unique()) if "category" in df.columns else []
statuses = sorted(df["status"].dropna().unique()) if "status" in df.columns else []

selected_categories = st.sidebar.multiselect("Select Category:", categories)
selected_status = st.sidebar.multiselect("Select Order Status:", statuses)

# -----------------------------------------------------
# Filter Data
# -----------------------------------------------------
dff = df.copy()
if selected_categories:
    dff = dff[dff["category"].isin(selected_categories)]
if selected_status:
    dff = dff[dff["status"].isin(selected_status)]

if dff.empty:
    st.warning("⚠ No data available for selected filters.")
    st.stop()

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
if "date" in dff.columns:
    monthly_sales = (
        dff.groupby(dff["date"].dt.to_period("M"))["amount"]
        .sum()
        .reset_index()
    )
    monthly_sales["date"] = monthly_sales["date"].dt.to_timestamp()

    fig_trend = px.line(
        monthly_sales,
        x="date",
        y="amount",
        title="📈 Monthly Sales Trend",
        markers=True,
        color_discrete_sequence=["#27ae60"]
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# -----------------------------------------------------
# Top Categories
# -----------------------------------------------------
if "category" in dff.columns:
    top_categories = (
        dff.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .head(10)
    )

    fig_cat = px.bar(
        top_categories,
        x="category",
        y="amount",
        title="🏷️ Top 10 Categories by Sales",
        color="amount",
        color_continuous_scale="Agsunset"
    )
    st.plotly_chart(fig_cat, use_container_width=True)

# -----------------------------------------------------
# Expense vs Profit
# -----------------------------------------------------
if "expense" in dff.columns:
    fig_ep = px.scatter(
        dff,
        x="expense",
        y="profit",
        color="category" if "category" in dff.columns else None,
        size="amount",
        hover_name="order id" if "order id" in dff.columns else None,
        title="💸 Expense vs Profit Distribution"
    )
    st.plotly_chart(fig_ep, use_container_width=True)

# -----------------------------------------------------
# Top 10 Products by Sales
# -----------------------------------------------------
if "style" in dff.columns:
    top_products = (
        dff.groupby("style", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .head(10)
    )

    fig_products = px.bar(
        top_products,
        x="style",
        y="amount",
        title="🛒 Top 10 Products by Sales",
        color="amount",
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig_products, use_container_width=True)
