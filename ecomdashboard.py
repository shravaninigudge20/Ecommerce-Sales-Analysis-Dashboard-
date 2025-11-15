# ====================================================
# Clean & Optimized E-Commerce Dashboard (Streamlit)
# Version: Option B – Stable Sidebar + Clean Filters
# ====================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ----------------------------------------------------
# Page Config
# ----------------------------------------------------
st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

# ----------------------------------------------------
# Cached Data Loader
# ----------------------------------------------------
@st.cache_data(ttl=3600)
def load_data(csv_url: str) -> pd.DataFrame:
    df = pd.read_csv(csv_url, low_memory=False)
    df.columns = df.columns.str.strip().str.lower()
    return df


# ----------------------------------------------------
# Preprocessing Function
# ----------------------------------------------------
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Fix common misspellings
    rename_map = {
        "received amount": "recived amount",
        "received_amount": "recived amount",
        "expense": "expance",
        "expenses": "expance",
        "order_id": "order id",
        "orderid": "order id",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    # Convert date column
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        df["date"] = pd.NaT

    # Numeric conversions
    numeric_cols = ["amount", "recived amount", "expance", "qty", "profit"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    # Create profit if missing
    if df["profit"].sum() == 0:
        df["profit"] = df["amount"] - df["expance"]

    # Clean string columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    # Remove rows with no amount
    df = df[df["amount"] > 0]

    return df


# ----------------------------------------------------
# Sidebar UI
# ----------------------------------------------------
with st.sidebar:
    st.title("⚙ Filters")

    csv_url = st.text_input(
        "Google Sheets CSV URL",
        value="https://docs.google.com/spreadsheets/d/1-CPu7c-5FD4_XyPEY6gPVRYOfPj1_d5S/export?format=csv",
        help="Paste Google Sheet CSV link (must end with export?format=csv)",
    )

    page = st.selectbox("Page", ["Overview", "Products", "Customers", "Raw Data"])

# ----------------------------------------------------
# Load + Preprocess
# ----------------------------------------------------
try:
    df = load_data(csv_url)
except:
    st.error("❌ Could not load CSV. Check your URL.")
    st.stop()

df = preprocess(df)

# Category & status lists
categories = sorted(df["category"].dropna().unique()) if "category" in df.columns else []
statuses = sorted(df["status"].dropna().unique()) if "status" in df.columns else []

# Date bounds
valid_dates = df["date"].dropna()
min_date = valid_dates.min().date() if not valid_dates.empty else datetime.today().date()
max_date = valid_dates.max().date() if not valid_dates.empty else datetime.today().date()

# -----------------------------
# Sidebar Filters Section
# -----------------------------
with st.sidebar:
    st.subheader("Data Filters")

    selected_categories = st.multiselect("Category", categories)
    selected_status = st.multiselect("Status", statuses)
    date_range = st.date_input("Date Range", [min_date, max_date])

    profit_min = int(df["profit"].min())
    profit_max = int(df["profit"].max())

    profit_range = st.slider(
        "Profit Range",
        min_value=profit_min,
        max_value=profit_max,
        value=(profit_min, profit_max),
    )


# ----------------------------------------------------
# Apply Filters
# ----------------------------------------------------
@st.cache_data
def apply_filters(df, cats, sts, date_range, profit_range):
    dff = df.copy()

    if cats:
        dff = dff[dff["category"].isin(cats)]
    if sts:
        dff = dff[dff["status"].isin(sts)]

    # Date filter
    if len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        dff = dff[(dff["date"] >= start) & (dff["date"] <= end)]

    # Profit filter
    dff = dff[(dff["profit"] >= profit_range[0]) & (dff["profit"] <= profit_range[1])]

    return dff


dff = apply_filters(df, selected_categories, selected_status, date_range, profit_range)


# Utility formatter
def fmt(x):
    return f"₹{x:,.0f}"


# ----------------------------------------------------
# PAGE: OVERVIEW
# ----------------------------------------------------
if page == "Overview":
    st.title("📊 Sales Overview")

    total_sales = dff["amount"].sum()
    total_profit = dff["profit"].sum()
    total_orders = len(dff)
    avg_profit = dff["profit"].mean() if len(dff) else 0
    avg_order_value = total_sales / total_orders if total_orders else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Sales", fmt(total_sales))
    k2.metric("Total Profit", fmt(total_profit))
    k3.metric("Avg Profit", fmt(avg_profit))
    k4.metric("Total Orders", f"{total_orders:,}")
    k5.metric("Avg Order Value", fmt(avg_order_value))

    st.markdown("---")

    # Trend chart
    if dff["date"].notna().any():
        m = dff.groupby(dff["date"].dt.to_period("M"))["amount"].sum().reset_index()
        m["date"] = m["date"].dt.to_timestamp()
        fig = px.line(m, x="date", y="amount", markers=True, title="📈 Monthly Sales")
        st.plotly_chart(fig, use_container_width=True)

    # Top categories
    if "category" in dff.columns:
        st.markdown("---")
        cat = dff.groupby("category")["amount"].sum().reset_index()
        fig = px.pie(cat, names="category", values="amount", title="Top Categories")
        st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------
# PAGE: PRODUCTS
# ----------------------------------------------------
elif page == "Products":
    st.title("🛒 Product Performance")

    prod_col = "style" if "style" in dff.columns else ("product" if "product" in dff.columns else None)

    if prod_col:
        p = dff.groupby(prod_col)["amount"].sum().reset_index().sort_values("amount", ascending=False)

        fig = px.bar(p.head(20), x=prod_col, y="amount", title="Top Products")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(p)
    else:
        st.info("No product/style column found.")

# ----------------------------------------------------
# PAGE: CUSTOMERS
# ----------------------------------------------------
elif page == "Customers":
    st.title("👥 Customer Breakdown")

    if "customer" in dff.columns:
        c = dff.groupby("customer")["amount"].sum().reset_index().sort_values("amount", ascending=False)

        fig = px.bar(c.head(20), x="customer", y="amount", title="Top Customers")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(c)
    else:
        st.info("No customer column found.")

# ----------------------------------------------------
# PAGE: RAW DATA
# ----------------------------------------------------
elif page == "Raw Data":
    st.title("📄 Raw Data (Filtered)")
    st.write(f"Rows: **{len(dff):,}**")

    csv = dff.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "filtered_data.csv", "text/csv")

    st.dataframe(dff)

