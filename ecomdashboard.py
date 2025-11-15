import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================================
# 🌟 LIGHT THEME CSS (Modern & Clean)
# ==============================================
light_theme_css = """
<style>
/* GLOBAL BACKGROUND */
.stApp {
    background: linear-gradient(135deg, #ffffff, #f3f6fb);
    font-family: 'Segoe UI', sans-serif;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #e8e8e8;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #2b3a4b !important;
}

/* KPI CARDS */
div[data-testid="metric-container"] {
    background: #ffffff;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #e4e4e4;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.06);
}

div[data-testid="metric-container"] > label {
    color: #34495e !important;
    font-size: 0.92rem;
}

div[data-testid="metric-container"] > div {
    color: #1976d2 !important;
    font-weight: 700 !important;
}

/* CHART BOXES */
.block-container {
    padding-top: 1rem;
}

footer {visibility:hidden;}
</style>
"""
st.markdown(light_theme_css, unsafe_allow_html=True)


# ==============================================
# LOAD DATA FROM GOOGLE SHEETS
# ==============================================
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1-CPu7c-5FD4_XyPEY6gPVRYOfPj1_d5S/export?format=csv"
    df = pd.read_csv(url, low_memory=False)
    df.columns = df.columns.str.lower().str.strip()

    # Fix date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Convert numeric fields
    for col in ["amount", "recived amount", "expance", "qty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Create profit column
    if "profit" not in df.columns:
        df["profit"] = df["amount"] - df["expance"]

    return df

df = load_data()


# ==============================================
# PAGE TITLE
# ==============================================
st.title("📊 E-Commerce Sales Dashboard (Light Theme)")


# ==============================================
# FILTERS
# ==============================================
st.sidebar.header("🔎 Filters")

category_list = sorted(df["category"].dropna().unique())
state_list = sorted(df["ship-state"].dropna().unique())

selected_categories = st.sidebar.multiselect("Select Category", category_list, default=category_list)
selected_states = st.sidebar.multiselect("Select Ship State", state_list, default=state_list)

# Apply filters
df_filtered = df[
    (df["category"].isin(selected_categories)) &
    (df["ship-state"].isin(selected_states))
]


# ==============================================
# KPIs
# ==============================================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Revenue", f"₹{df_filtered['amount'].sum():,.0f}")
col2.metric("Total Orders", f"{df_filtered.shape[0]:,}")
col3.metric("Total Profit", f"₹{df_filtered['profit'].sum():,.0f}")
col4.metric("Average Order Value", f"₹{df_filtered['amount'].mean():,.0f}")


# ==============================================
# SALES BY CATEGORY
# ==============================================
st.subheader("📦 Sales by Category")

cat_sales = df_filtered.groupby("category")["amount"].sum().reset_index()

fig1 = px.bar(
    cat_sales,
    x="category",
    y="amount",
    title="",
    color="amount",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig1, use_container_width=True)


# ==============================================
# SALES BY STATE
# ==============================================
st.subheader("📍 Sales by Ship-State")
