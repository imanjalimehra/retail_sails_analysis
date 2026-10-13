
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Project folders
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "SampleSuperstore.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load dataset
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
df.columns = df.columns.str.strip()

print("\n--- ORIGINAL DATA ---")
print("Shape:", df.shape)
print(df.head())
print("\nMissing values:\n", df.isnull().sum())
print("\nDuplicate rows:", df.duplicated().sum())

# Convert dates
df["Order Date"] = pd.to_datetime(
    df["Order Date"], errors="coerce"
)
df["Ship Date"] = pd.to_datetime(
    df["Ship Date"], errors="coerce"
)

# Convert numerical columns
for col in ["Sales", "Quantity", "Discount", "Profit"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove exact duplicates
df = df.drop_duplicates().copy()

# Remove rows missing essential fields
df = df.dropna(subset=[
    "Order ID", "Order Date", "Sales",
    "Profit", "Category", "Region"
]).copy()

# Create date columns
df["Year"] = df["Order Date"].dt.year
df["Month"] = df["Order Date"].dt.month
df["Year-Month"] = df["Order Date"].dt.to_period("M").astype(str)

# Calculate shipping time
df["Shipping Days"] = (
    df["Ship Date"] - df["Order Date"]
).dt.days

# Calculate row-level profit margin
df["Profit Margin (%)"] = np.where(
    df["Sales"] != 0,
    df["Profit"] / df["Sales"] * 100,
    np.nan
)

# Save cleaned data
df.to_csv(OUTPUT_DIR / "cleaned_superstore.csv", index=False)

# KPI calculations
total_sales = df["Sales"].sum()
total_profit = df["Profit"].sum()
total_orders = df["Order ID"].nunique()
profit_margin = (
    total_profit / total_sales * 100
    if total_sales != 0 else 0
)

print("\n--- BUSINESS KPIs ---")
print(f"Total Revenue: ${total_sales:,.2f}")
print(f"Total Profit: ${total_profit:,.2f}")
print(f"Total Orders: {total_orders:,}")
print(f"Overall Profit Margin: {profit_margin:.2f}%")

# Category analysis
category = df.groupby("Category").agg(
    Revenue=("Sales", "sum"),
    Profit=("Profit", "sum"),
    Quantity=("Quantity", "sum"),
    Orders=("Order ID", "nunique")
).reset_index()

category["Profit Margin (%)"] = np.where(
    category["Revenue"] != 0,
    category["Profit"] / category["Revenue"] * 100,
    np.nan
)

category.to_csv(OUTPUT_DIR / "category_analysis.csv", index=False)
print("\n--- CATEGORY ANALYSIS ---")
print(category.to_string(index=False))

# Regional analysis
region = df.groupby("Region").agg(
    Revenue=("Sales", "sum"),
    Profit=("Profit", "sum"),
    Orders=("Order ID", "nunique")
).reset_index()

region.to_csv(OUTPUT_DIR / "regional_analysis.csv", index=False)
print("\n--- REGIONAL ANALYSIS ---")
print(region.to_string(index=False))

# Monthly analysis
monthly = df.groupby("Year-Month").agg(
    Revenue=("Sales", "sum"),
    Profit=("Profit", "sum"),
    Orders=("Order ID", "nunique")
).reset_index().sort_values("Year-Month")

monthly["Revenue MoM Growth (%)"] = (
    monthly["Revenue"].pct_change() * 100
)

monthly.to_csv(OUTPUT_DIR / "monthly_analysis.csv", index=False)

# Product analysis
product = df.groupby(["Product ID", "Product Name"]).agg(
    Revenue=("Sales", "sum"),
    Profit=("Profit", "sum"),
    Quantity=("Quantity", "sum")
).reset_index()

product.to_csv(OUTPUT_DIR / "product_analysis.csv", index=False)

print("\n--- TOP 10 PRODUCTS BY PROFIT ---")
print(product.nlargest(10, "Profit").to_string(index=False))

print("\n--- 10 LOWEST-PROFIT PRODUCTS ---")
print(product.nsmallest(10, "Profit").to_string(index=False))

# Segment analysis
segment = df.groupby("Segment").agg(
    Revenue=("Sales", "sum"),
    Profit=("Profit", "sum"),
    Orders=("Order ID", "nunique")
).reset_index()

segment.to_csv(OUTPUT_DIR / "segment_analysis.csv", index=False)

# SQL database
database = OUTPUT_DIR / "retail_sales.db"

with sqlite3.connect(database) as conn:
    df.to_sql("Superstore", conn, if_exists="replace", index=False)

    query = """
        SELECT Category,
               ROUND(SUM(Sales), 2) AS Revenue,
               ROUND(SUM(Profit), 2) AS Profit
        FROM Superstore
        GROUP BY Category
        ORDER BY Profit DESC;
    """

    print("\n--- SQL CATEGORY RESULTS ---")
    print(pd.read_sql_query(query, conn).to_string(index=False))

# Visualizations
sns.set_theme(style="whitegrid")

plt.figure(figsize=(8, 5))
sns.barplot(data=category, x="Category", y="Revenue")
plt.title("Revenue by Category")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "revenue_by_category.png", dpi=150)
plt.close()

plt.figure(figsize=(8, 5))
sns.barplot(data=region, x="Region", y="Profit")
plt.title("Profit by Region")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "profit_by_region.png", dpi=150)
plt.close()

plt.figure(figsize=(12, 5))
sns.lineplot(data=monthly, x="Year-Month", y="Revenue", marker="o")
plt.title("Monthly Revenue Trend")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "monthly_revenue.png", dpi=150)
plt.close()

print("\nSUCCESS! Analysis completed.")
print("Check your outputs folder.")
