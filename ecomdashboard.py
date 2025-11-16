# =====================================================
# E-Commerce Interactive Dashboard (Streamlit Version)
# Upgraded & Easy-to-Explain
# =====================================================
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------------------------------
# Load Dataset
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
df.rename(columns={"recived amount": "received_amount", "expance": "expense"}, inplace=True)

# -----------------------------------------------------
# Convert Date Column
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
# Clean & Standardize Order Status
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
    df["profit"] = df["amount"] - df["expense"] if "expense" in df.columns else df["amount"]

# -----------------------------------------------------
# Filter Valid Sales
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
st.sidebar.header("Filters")

# Date Range Filter
if "date" in df.columns:
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        value=[df['date'].min(), df['date'].max()]
    )
    df = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

# Category Filter
categories = sorted(df["category"].dropna().unique()) if "category" in df.columns else []
selected_categories = st.sidebar.multiselect("Select Category:", categories)
if selected_categories:
    df = df[df["category"].isin(selected_categories)]

# Status Filter
statuses = sorted(df["status"].dropna().unique()) if "status" in df.columns else []
selected_status = st.sidebar.multiselect("Select Order Status:", statuses)
if selected_status:
    df = df[df["status"].isin(selected_status)]

# -----------------------------------------------------
# Download Filtered Data
# -----------------------------------------------------
st.sidebar.markdown("### 📥 Download Filtered Data")
st.sidebar.download_button(
    "Download CSV",
    df.to_csv(index=False),
    "filtered_data.csv",
    "text/csv"
)

# -----------------------------------------------------
# Create Tabs for Organized Layout
# -----------------------------------------------------
tabs = st.tabs(["Overview", "Sales Analysis", "Profit & Expenses", "Top Products"])

# =====================================================
# TAB 1: Overview
# =====================================================
with tabs[0]:
    st.subheader("📊 Key Performance Indicators (KPIs)")
    total_sales = df["amount"].sum()
    total_profit = df["profit"].sum()
    avg_profit = df["profit"].mean()
    total_orders = len(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sales", f"₹{total_sales:,.0f}")
    col2.metric("Total Profit", f"₹{total_profit:,.0f}")
    col3.metric("Average Profit", f"₹{avg_profit:,.0f}")
    col4.metric("Total Orders", f"{total_orders:,}")

    # Monthly Sales Trend
    if "date" in df.columns:
        monthly_sales = df.groupby(df["date"].dt.to_period("M"))["amount"].sum().reset_index()
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

# =====================================================
# TAB 2: Sales Analysis
# =====================================================
with tabs[1]:
    st.subheader("🏷️ Top Categories by Sales")
    if "category" in df.columns:
        top_categories = df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False).head(10)
        fig_cat = px.bar(
            top_categories,
            x="category",
            y="amount",
            title="Top 10 Categories by Sales",
            color="amount",
            color_continuous_scale="Agsunset"
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    # Status Summary
    st.subheader("📦 Order Status Distribution")
    if "status" in df.columns:
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_status = px.pie(status_counts, names="Status", values="Count", title="Orders by Status")
        st.plotly_chart(fig_status, use_container_width=True)

# =====================================================
# TAB 3: Profit & Expenses
# =====================================================
with tabs[2]:
    st.subheader("💸 Expense vs Profit")
    if "expense" in df.columns:
        fig_ep = px.scatter(
            df,
            x="expense",
            y="profit",
            color="category" if "category" in df.columns else None,
            size="amount",
            hover_name="order id" if "order id" in df.columns else None,
            title="Expense vs Profit Distribution"
        )
        st.plotly_chart(fig_ep, use_container_width=True)

# =====================================================
# TAB 4: Top Products
# =====================================================
with tabs[3]:
    st.subheader("🛒 Top 10 Products by Sales")
    if "style" in df.columns:
        top_products = df.groupby("style", as_index=False)["amount"].sum().sort_values("amount", ascending=False).head(10)
        fig_products = px.bar(
            top_products,
            x="style",
            y="amount",
            title="Top 10 Products by Sales",
            color="amount",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_products, use_container_width=True)
