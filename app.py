
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Retail Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "outputs" / "cleaned_superstore.csv"

st.title("📊 Retail Sales & Business Intelligence Dashboard")
st.write("Explore sales, profit, products, and regional performance.")

df = pd.read_csv(DATA_FILE)
df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

# Sidebar filters
st.sidebar.header("Filters")

regions = sorted(df["Region"].dropna().unique())
selected_regions = st.sidebar.multiselect(
    "Select Region",
    regions,
    default=regions
)

categories = sorted(df["Category"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Select Category",
    categories,
    default=categories
)

filtered_df = df[
    df["Region"].isin(selected_regions)
    & df["Category"].isin(selected_categories)
]

# KPI metrics
total_sales = filtered_df["Sales"].sum()
total_profit = filtered_df["Profit"].sum()
total_orders = filtered_df["Order ID"].nunique()
profit_margin = (
    total_profit / total_sales * 100 if total_sales else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric("Total Profit", f"${total_profit:,.2f}")
col3.metric("Total Orders", f"{total_orders:,}")
col4.metric("Profit Margin", f"{profit_margin:.2f}%")

st.divider()

# Sales by category
st.subheader("Sales by Category")
category_data = (
    filtered_df.groupby("Category", as_index=False)["Sales"]
    .sum()
)
fig1 = px.bar(
    category_data,
    x="Category",
    y="Sales",
    color="Category",
    title="Revenue by Product Category"
)
st.plotly_chart(fig1, use_container_width=True)

# Profit by region
st.subheader("Profit by Region")
region_data = (
    filtered_df.groupby("Region", as_index=False)["Profit"]
    .sum()
)
fig2 = px.bar(
    region_data,
    x="Region",
    y="Profit",
    color="Region",
    title="Profit Across Regions"
)
st.plotly_chart(fig2, use_container_width=True)

# Monthly sales trend
st.subheader("Monthly Sales Trend")
monthly_data = (
    filtered_df.dropna(subset=["Order Date"])
    .assign(Month=lambda x: x["Order Date"].dt.to_period("M").astype(str))
    .groupby("Month", as_index=False)["Sales"]
    .sum()
    .sort_values("Month")
)
fig3 = px.line(
    monthly_data,
    x="Month",
    y="Sales",
    markers=True,
    title="Monthly Revenue Over Time"
)
st.plotly_chart(fig3, use_container_width=True)

# Top products
st.subheader("Top 10 Products by Sales")
top_products = (
    filtered_df.groupby("Product Name", as_index=False)["Sales"]
    .sum()
    .nlargest(10, "Sales")
    .sort_values("Sales")
)
fig4 = px.bar(
    top_products,
    x="Sales",
    y="Product Name",
    orientation="h",
    title="Top 10 Products"
)
st.plotly_chart(fig4, use_container_width=True)

# Data preview
with st.expander("View Filtered Dataset"):
    st.dataframe(filtered_df, use_container_width=True)

st.caption("Built using Python, Pandas, SQL, Streamlit and Plotly.")
