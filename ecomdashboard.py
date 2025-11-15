import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------------------------------
# Load Dataset from Google Sheets CSV
# -----------------------------------------------------
csv_url = "https://docs.google.com/spreadsheets/d/1-CPu7c-5FD4_XyPEY6gPVRYOfPj1_d5S/export?format=csv"
df = pd.read_csv(csv_url, low_memory=False)

# Clean columns
df.columns = df.columns.str.strip().str.lower()

# Convert date
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Ensure numeric columns
for col in ["amount", "recived amount", "expance", "qty"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Add profit column
if "profit" not in df.columns:
    df["profit"] = df["amount"] - df["expance"]

# Filter for valid sales
df = df[df["amount"] > 0]

# -----------------------------------------------------
# Streamlit Page Config
# -----------------------------------------------------
st.set_page_config(page_title="E-Commerce Sales Dashboard", layout="wide")

# -----------------------------------------------------
# Custom HTML + CSS Design
# -----------------------------------------------------
st.markdown("""
<style>
/* Main Page Style */
body {
    background-color: #f5f5f5;
}

/* Title Banner */
.main-title {
    background: linear-gradient(90deg, #4b79a1, #283e51);
    padding: 18px;
    border-radius: 10px;
    text-align: center;
    font-size: 32px;
    font-weight: bold;
    color: white;
    margin-bottom: 25px;
}

/* KPI Cards */
.metric-card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    text-align: center;
    margin: 10px;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #1f2937 !important;
}
section[data-testid="stSidebar"] span, label {
    color: white !important;
}

/* Plot Containers */
.chart-box {
    background: white;
    padding: 18px;
    border-radius: 15px;
    margin-bottom: 28px;
    box-shadow: 0px 4px 18px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# App Title Styled
st.markdown('<div class="main-title">📦 E-Commerce Sales Dashboard</div>', unsafe_allow_html=True)

# -----------------------------------------------------
# Sidebar Filters
# -----------------------------------------------------
categories = sorted(df["category"].dropna().unique())
statuses = sorted(df["status"].dropna().unique())

st.sidebar.header("🔍 Filters")
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

st.markdown("### 📊 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Total Sales</h3>
        <h2>₹{total_sales:,.0f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Total Profit</h3>
        <h2>₹{total_profit:,.0f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Average Profit</h3>
        <h2>₹{avg_profit:,.0f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Total Orders</h3>
        <h2>{total_orders:,}</h2>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------
# Monthly Sales Trend
# -----------------------------------------------------
st.markdown('<div class="chart-box">', unsafe_allow_html=True)
monthly_sales = dff.groupby(dff["date"].dt.to_period("M"))["amount"].sum().reset_index()
monthly_sales["date"] = monthly_sales["date"].dt.to_timestamp()
fig_trend = px.line(monthly_sales, x="date", y="amount",
                    title="📈 Monthly Sales Trend", markers=True)
st.plotly_chart(fig_trend, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------
# Top Categories
# -----------------------------------------------------
st.markdown('<div class="chart-box">', unsafe_allow_html=True)
top_categories = (
    dff.groupby("category", as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
    .head(10)
)
fig_cat = px.bar(top_categories, x="category", y="amount",
                 title="🏷️ Top 10 Categories by Sales", color="amount")
st.plotly_chart(fig_cat, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------
# Expense vs Profit
# -----------------------------------------------------
st.markdown('<div class="chart-box">', unsafe_allow_html=True)
fig_ep = px.scatter(dff, x="expance", y="profit",
                    color="category", size="amount",
                    hover_name="order id",
                    title="💸 Expense vs Profit Distribution")
st.plotly_chart(fig_ep, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------
# Top 10 Products by Sales
# -----------------------------------------------------
if "style" in df.columns:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    top_products = (
        dff.groupby("style", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .head(10)
    )
    fig_products = px.bar(top_products, x="style", y="amount",
                          title="🛒 Top 10 Products by Sales",
                          color="amount")
    st.plotly_chart(fig_products, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
