import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Retail Insights Dashboard", page_icon="📊", layout="wide")

st.title("📊 Retail Business Insights Dashboard")
st.markdown("_Prototype built for Upwork Portfolio Showcase_")

# --- 2. DATA GENERATION (Cached for performance) ---
@st.cache_data
def load_data():
    # Simulating the Superstore Dataset
    np.random.seed(42)
    n_rows = 3000
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', periods=n_rows)
    categories = ['Furniture', 'Office Supplies', 'Technology']
    segments = ['Consumer', 'Corporate', 'Home Office']
    regions = ['North', 'South', 'East', 'West']
    
    data = {
        'Order Date': dates,
        'Category': np.random.choice(categories, n_rows),
        'Segment': np.random.choice(segments, n_rows),
        'Region': np.random.choice(regions, n_rows),
        'Sales': np.random.uniform(10, 1000, n_rows),
        'Profit_Margin': np.random.uniform(-0.10, 0.40, n_rows),
        'Returned': np.random.choice([0, 1], n_rows, p=[0.90, 0.10]),
        'CustomerID': np.random.randint(100, 150, n_rows)
    }
    
    df = pd.DataFrame(data)
    df['Profit'] = df['Sales'] * df['Profit_Margin']
    df['YearMonth'] = df['Order Date'].dt.to_period('M').astype(str)
    return df

df = load_data()

# --- 3. SIDEBAR FILTERS ---
st.sidebar.header("Filter Options")

# Filter by Region
region_filter = st.sidebar.multiselect(
    "Select Region:",
    options=df["Region"].unique(),
    default=df["Region"].unique()
)

# Filter by Segment
segment_filter = st.sidebar.multiselect(
    "Select Segment:",
    options=df["Segment"].unique(),
    default=df["Segment"].unique()
)

# Apply Filters
df_selection = df.query(
    "Region == @region_filter & Segment == @segment_filter"
)

# Check if dataframe is empty
if df_selection.empty:
    st.warning("No data available based on the current filter selection!")
    st.stop()

# --- 4. KPI ROW ---
st.markdown("### Key Performance Indicators (KPIs)")
total_sales = df_selection['Sales'].sum()
total_profit = df_selection['Profit'].sum()
avg_return_rate = (df_selection['Returned'].sum() / len(df_selection)) * 100
avg_profit_margin = (total_profit / total_sales) * 100

left_column, middle_column, right_column, far_right = st.columns(4)

with left_column:
    st.metric(label="Total Sales", value=f"${total_sales:,.0f}")
with middle_column:
    st.metric(label="Total Profit", value=f"${total_profit:,.0f}")
with right_column:
    st.metric(label="Return Rate", value=f"{avg_return_rate:.2f}%")
with far_right:
    st.metric(label="Profit Margin", value=f"{avg_profit_margin:.2f}%")

st.markdown("---")

# --- 5. CHARTS & ANALYSIS ---

# Create Tabs for better organization
tab1, tab2, tab3 = st.tabs(["📈 Sales Trends", "🌍 Geographic & Category", "👥 Customer Behavior (RFM)"])

with tab1:
    st.subheader("Sales Trend & Forecasting")
    # Prepare data
    monthly_sales = df_selection.groupby('YearMonth')['Sales'].sum().reset_index()
    monthly_sales['Sales_MA_3'] = monthly_sales['Sales'].rolling(window=3).mean()
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=monthly_sales['YearMonth'], y=monthly_sales['Sales'], name='Actual Sales', marker_color='#0083B8'))
    fig_trend.add_trace(go.Scatter(x=monthly_sales['YearMonth'], y=monthly_sales['Sales_MA_3'], name='3-Month Moving Avg', line=dict(color='orange', width=3)))
    
    fig_trend.update_layout(xaxis_title="Month", yaxis_title="Sales ($)", template="plotly_white")
    st.plotly_chart(fig_trend, use_container_width=True)

with tab2:
    st.subheader("Sales Distribution")
    col1, col2 = st.columns(2)
    
    with col1:
        # Sunburst
        category_group = df_selection.groupby(['Category', 'Region'])[['Sales', 'Profit']].sum().reset_index()
        fig_sun = px.sunburst(category_group, path=['Category', 'Region'], values='Sales', color='Profit', title="Sales by Category & Region")
        st.plotly_chart(fig_sun, use_container_width=True)
        
    with col2:
        # Bar Chart for Returns
        return_data = df_selection[df_selection['Returned']==1].groupby('Category')['Sales'].count().reset_index(name='Return_Count')
        fig_ret = px.bar(return_data, x='Category', y='Return_Count', title="Total Returns by Category", color='Category', color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_ret, use_container_width=True)

with tab3:
    st.subheader("Customer Segmentation (RFM Analysis)")
    st.markdown("We classify customers based on **Recency** (last purchase), **Frequency** (count), and **Monetary** (total spend).")
    
    snapshot_date = df['Order Date'].max() + datetime.timedelta(days=1)
    rfm = df_selection.groupby('CustomerID').agg({
        'Order Date': lambda x: (snapshot_date - x.max()).days,
        'CustomerID': 'count',
        'Sales': 'sum'
    }).rename(columns={'Order Date': 'Recency', 'CustomerID': 'Frequency', 'Sales': 'Monetary'})
    
    # Calculate simple segments
    rfm['Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1]).astype(int) + \
                   pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4]).astype(int) + \
                   pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4]).astype(int)
    
    def segment_me(score):
        if score >= 10: return 'Gold Tier (Loyal)'
        elif score >= 7: return 'Silver Tier (Promising)'
        else: return 'Bronze Tier (Needs Attention)'
        
    rfm['Segment'] = rfm['Score'].apply(segment_me)
    
    # Scatter Plot
    fig_rfm = px.scatter(rfm, x='Recency', y='Monetary', color='Segment', size='Frequency', 
                         title="RFM Segments: Recency vs Monetary Value", hover_data=['Frequency'])
    st.plotly_chart(fig_rfm, use_container_width=True)

# --- 6. FOOTER ---
st.markdown("---")
st.markdown("### Raw Data View")
if st.checkbox("Show Raw Data"):
    st.dataframe(df_selection)