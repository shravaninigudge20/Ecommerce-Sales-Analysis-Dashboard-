# streamlit_ecommerce_optimized.py
# Optimized E‑Commerce Dashboard (Streamlit)
# Features:
# - Cached data loading
# - Robust preprocessing + column checks
# - Sidebar filters (date range, category, status, profit)
# - Multiple pages (Overview, Products, Customers, Raw Data)
# - KPIs, trends, heatmap, scatter, top lists
# - CSV download of filtered data
# - Optional forecasting (Prophet) if installed

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# -----------------------------
# Configuration
# -----------------------------
st.set_page_config(page_title="E-Commerce Sales Dashboard", layout="wide")

# -----------------------------
# Helpers & Caching
# -----------------------------
@st.cache_data(ttl=60 * 60)
def load_data(csv_url: str) -> pd.DataFrame:
    df = pd.read_csv(csv_url, low_memory=False)
    # normalize column names
    df.columns = df.columns.str.strip().str.lower()
    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Ensure commonly expected columns exist (create if missing)
    # Map potential misspellings
    col_map = {
        'received amount': 'recived amount',
        'received_amount': 'recived amount',
        'expense': 'expance',
        'expenses': 'expance',
        'order_id': 'order id',
        'orderid': 'order id',
        'orderid ': 'order id'
    }
    for src, dst in col_map.items():
        if src in df.columns and dst not in df.columns:
            df = df.rename(columns={src: dst})

    # Convert date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    else:
        # create a synthetic date column (if absolutely missing) so app doesn't crash
        df['date'] = pd.NaT

    # Numeric conversions (fill missing with 0 where meaningful)
    for col in ['amount', 'recived amount', 'expance', 'qty', 'profit']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            # create missing numeric columns as zeros when safe
            if col in ['amount', 'expance', 'qty', 'profit']:
                df[col] = 0

    # Create profit if not present
    if 'profit' not in df.columns or df['profit'].isna().all():
        df['profit'] = df['amount'].fillna(0) - df['expance'].fillna(0)

    # Basic cleanups
    # Strip string columns to avoid hidden whitespace
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype(str).fillna("").str.strip()

    # Remove obviously invalid rows (no amount, missing order id optional)
    if 'amount' in df.columns:
        df = df[df['amount'].fillna(0) > 0]

    return df


# -----------------------------
# UI: Sidebar filters + page navigation
# -----------------------------
with st.sidebar:
    st.title("Filters & Pages")

    csv_url = st.text_input(
        "Google Sheets CSV URL",
        value="https://docs.google.com/spreadsheets/d/1-CPu7c-5FD4_XyPEY6gPVRYOfPj1_d5S/export?format=csv",
        help="Paste your sheet's CSV export URL here (export?format=csv)"
    )

    page = st.selectbox("Page", ["Overview", "Products", "Customers", "Raw Data"])

    # Theme toggle (simple)
    theme = st.selectbox("Theme", ["Light", "Dark"]) 
    if theme == "Dark":
        st.markdown("<style>body{background-color:#0e1117;color:#ddd}</style>", unsafe_allow_html=True)

# -----------------------------
# Load + preprocess
# -----------------------------
try:
    df = load_data(csv_url)
except Exception as e:
    st.error(f"Couldn't load data from the URL. Error: {e}")
    st.stop()

df = preprocess(df)

# Derive filter values safely
categories = sorted(df['category'].dropna().unique()) if 'category' in df.columns else []
statuses = sorted(df['status'].dropna().unique()) if 'status' in df.columns else []

# Date bounds
if df['date'].notna().any():
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
else:
    min_date = datetime.today().date()
    max_date = datetime.today().date()

# Sidebar inputs (below pages selection)
with st.sidebar.expander("Data Filters", expanded=True):
    selected_categories = st.multiselect("Category", categories, default=None)
    selected_status = st.multiselect("Order Status", statuses, default=None)
    date_range = st.date_input("Date range", [min_date, max_date])

    profit_min = int(df['profit'].min()) if not df['profit'].isna().all() else 0
    profit_max = int(df['profit'].max()) if not df['profit'].isna().all() else 0
    # Profit range safety
    if profit_min > profit_max:
        profit_min, profit_max = 0, 0

    profit_range = st.slider(
        "Profit range",
        min_value=int(profit_min),
        max_value=int(profit_max),
        value=(int(profit_min), int(profit_max))
    ))

# -----------------------------
# Filter dataframe centrally
# -----------------------------
@st.cache_data
def apply_filters(df, cats, statuses, date_range, profit_range):
    dff = df.copy()
    if cats:
        dff = dff[dff['category'].isin(cats)]
    if statuses:
        dff = dff[dff['status'].isin(statuses)]

    # Date range
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        dff = dff[(dff['date'] >= start_date) & (dff['date'] <= end_date)]

    # Profit range
    dff = dff[(dff['profit'] >= profit_range[0]) & (dff['profit'] <= profit_range[1])]

    return dff

# Apply filters
dff = apply_filters(df, selected_categories, selected_status, date_range, profit_range)

# -----------------------------
# Utility: currency format
# -----------------------------
def fmt(x):
    try:
        return f"₹{x:,.0f}"
    except Exception:
        return x

# -----------------------------
# PAGE: Overview
# -----------------------------
if page == "Overview":
    st.title("📦 E-Commerce Sales Analysis")

    # KPIs
    total_sales = dff['amount'].sum()
    total_profit = dff['profit'].sum()
    avg_profit = dff['profit'].mean() if len(dff) else 0
    total_orders = len(dff)
    total_expense = dff['expance'].sum() if 'expance' in dff.columns else 0
    avg_order_value = total_sales / total_orders if total_orders else 0

    st.markdown("### Key Performance Indicators")
    k1, k2, k3, k4, k5 = st.columns([1.2, 1.2, 1.2, 1.0, 1.2])
    k1.metric("Total Sales", fmt(total_sales))
    k2.metric("Total Profit", fmt(total_profit))
    k3.metric("Average Profit", fmt(avg_profit))
    k4.metric("Total Orders", f"{total_orders:,}")
    k5.metric("Avg Order Value", fmt(avg_order_value))

    # Monthly trend
    st.markdown("---")
    if dff['date'].notna().any():
        monthly = dff.groupby(dff['date'].dt.to_period('M'))['amount'].sum().reset_index()
        monthly['date'] = monthly['date'].dt.to_timestamp()
        fig_trend = px.line(monthly, x='date', y='amount', title='📈 Monthly Sales Trend', markers=True, template='plotly_white', hover_data=['amount'])
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No valid date data to show time series.")

    # Profit heatmap (month vs category)
    st.markdown("---")
    if 'category' in dff.columns and dff['date'].notna().any():
        pivot = dff.pivot_table(values='profit', index=dff['date'].dt.strftime('%Y-%m'), columns='category', aggfunc='sum').fillna(0)
        if not pivot.empty:
            fig_heat = px.imshow(pivot, aspect='auto', title='🔥 Profit Heatmap (Month x Category)')
            st.plotly_chart(fig_heat, use_container_width=True)

    # Expense vs Profit scatter
    st.markdown("---")
    if 'expance' in dff.columns:
        fig_ep = px.scatter(dff, x='expance', y='profit', color='category' if 'category' in dff.columns else None,
                            size='amount' if 'amount' in dff.columns else None,
                            hover_name='order id' if 'order id' in dff.columns else None,
                            title='💸 Expense vs Profit')
        st.plotly_chart(fig_ep, use_container_width=True)

    # Top Categories
    st.markdown("---")
    if 'category' in dff.columns:
        top_categories = dff.groupby('category', as_index=False)['amount'].sum().sort_values('amount', ascending=False).head(10)
        fig_cat = px.pie(top_categories, names='category', values='amount', title='🏷️ Top Categories by Sales (Pie Chart)')
        st.plotly_chart(fig_cat, use_container_width=True)

    # Quick insights box
    st.markdown("---")
    st.subheader("Quick Insights")
    insights = []
    if total_sales > 0:
        top_cat = top_categories.iloc[0]['category'] if ('top_categories' in locals() and not top_categories.empty) else None
        if top_cat:
            insights.append(f"Top category by sales: **{top_cat}**")
        high_profit_items = dff.nlargest(3, 'profit')[['order id' if 'order id' in dff.columns else dff.columns[0], 'profit']]
        insights.append(f"Top 3 profitable orders: {', '.join([str(x) for x in high_profit_items['profit'].round(0)])}")
    if insights:
        for i in insights:
            st.markdown("- " + i)

# -----------------------------
# PAGE: Products
# -----------------------------
elif page == "Products":
    st.title("🛒 Product Analysis")

    prod_col = 'style' if 'style' in dff.columns else ('product' if 'product' in dff.columns else None)
    if prod_col:
        top_products = dff.groupby(prod_col, as_index=False)['amount'].sum().sort_values('amount', ascending=False).head(20)
        st.markdown("### Top Products by Sales")
        fig_products = px.bar(top_products, x=prod_col, y='amount', title='Top Products', template='plotly_white')
        st.plotly_chart(fig_products, use_container_width=True)

        # Product table with filters
        st.markdown("### Product Table")
        st.dataframe(top_products)
    else:
        st.info("No product/style/product column found in dataset.")

# -----------------------------
# PAGE: Customers
# -----------------------------
elif page == "Customers":
    st.title("👥 Customer Analysis")
    if 'customer' in dff.columns:
        cust_sales = dff.groupby('customer', as_index=False)['amount'].sum().sort_values('amount', ascending=False).head(20)
        st.dataframe(cust_sales)
        fig_cust = px.bar(cust_sales, x='customer', y='amount', title='Top Customers', template='plotly_white')
        st.plotly_chart(fig_cust, use_container_width=True)
    else:
        st.info("No customer column found in dataset.")

# -----------------------------
# PAGE: Raw Data
# -----------------------------
elif page == "Raw Data":
    st.title("📄 Filtered Raw Data")
    st.write(f"Showing **{len(dff):,}** rows after filters")

    # Download
    csv = dff.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Download Filtered Data", csv, "filtered_data.csv", "text/csv")

    # Table
    st.dataframe(dff)

# -----------------------------
# Optional: Forecasting (light)
# -----------------------------
with st.sidebar.expander("Forecasting (optional)"):
    do_forecast = st.checkbox("Enable simple forecast (monthly)")

if do_forecast and dff['date'].notna().any():
    st.markdown("---")
    st.header("📊 Simple Monthly Forecast")
    # Try to import Prophet if available, otherwise fallback to naive growth
    try:
        from prophet import Prophet
        monthly = dff.groupby(dff['date'].dt.to_period('M'))['amount'].sum().reset_index()
        monthly['ds'] = monthly['date'].dt.to_timestamp()
        monthly['y'] = monthly['amount']
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(monthly[['ds', 'y']])
        future = m.make_future_dataframe(periods=3, freq='M')
        forecast = m.predict(future)
        fig = px.line(forecast, x='ds', y='yhat', title='Forecasted Sales (monthly)')
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.warning("Prophet not installed or forecasting failed. Showing simple moving average as fallback.")
        monthly = dff.groupby(dff['date'].dt.to_period('M'))['amount'].sum().reset_index()
        monthly['date'] = monthly['date'].dt.to_timestamp()
        monthly['ma3'] = monthly['amount'].rolling(3, min_periods=1).mean()
        fig = px.line(monthly, x='date', y=['amount', 'ma3'], title='Sales + 3-month MA')
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Final notes shown to user
# -----------------------------
st.markdown("---")
st.caption("Tips: add unit tests for your preprocessing, pin the sheet URL, and deploy via Streamlit Cloud or Docker for production.")
