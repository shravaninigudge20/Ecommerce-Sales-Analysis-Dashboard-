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

/* CHART BLOCKS */
.block-container {
    padding-top: 1rem;
}

.css-1kyxreq, .css-1ws7g6d, .css-12w0qpk {
    background: #ffffff !important;
    padding: 20px !important;
    border-radius: 15px;
    border: 1px solid #e4e4e4;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
}

/* BUTTONS */
.stButton > button {
    background: #1976d2;
    color: white;
    border-radius: 8px;
    padding: 10px 22px;
    font-weight: 600;
    border: none;
}

.stButton > button:hover {
    background: #145a96;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.15);
}

/* HIDE FOOTER */
footer {visibility:hidden;}
</style>
"""

st.markdown(light_theme_css, unsafe_allow_html=True)


# ==============================================
# LOAD DATA
# ==============================================
@st.cache_data
def load_data():
    return pd.read_csv("Ecommerce_Sales_Cleaned_Final.csv", low_memory=False)

df = load_data()

st.title("📊 Ecommerce Sales Dashboard (Light Theme)")


# ==============================================
# FILTERS
# ==============================================
st.sidebar.header("🔎 Filters")

categories = st.sidebar.multiselect(
    "Select Category",
    options=df["Category"].unique(),
    default=df["Category"].unique()
)

states = st.sidebar.multiselect(
    "Select State",
    options=df["State"].unique(),
    default=df["State"].unique()
)

df_filtered = df[df["Category"].isin(categories) & df["State"].isin(states)]


# ==============================================
# KPI METRICS
# ==============================================
col1, col2, col3 = st.columns(3)

col1.metric("Total Sales", f"${int(df_filtered['Amount'].sum()):,}")
col2.metric("Total Orders", f"{df_filtered.shape[0]:,}")
col3.metric("Avg Order Value", f"${df_filtered['Amount'].mean():.2f}")


# ==============================================
# SALES BY CATEGORY
# ============================================
