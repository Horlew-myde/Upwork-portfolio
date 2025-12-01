import streamlit as st
import pandas as pd
import numpy as np
import io
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Automated Data Cleaning Pipeline", page_icon="🤖", layout="wide")

st.title("🤖 Automated Business Data Pipeline")
st.markdown("""
**The Problem:** Businesses spend hours manually cleaning Excel files, fixing dates, and removing duplicates.
**The Solution:** This Python automation script ingests raw, messy data, standardizes it, and prepares reports instantly.
""")

# --- 1. HELPER: GENERATE MESSY DATA ---
def generate_messy_data():
    np.random.seed(42)
    rows = 50
    
    # Create messy columns
    data = {
        'Transaction_ID': [f'TXN-{x}' for x in range(1000, 1000+rows)],
        'Customer Name': np.random.choice(['John Doe', ' Jane Smith ', 'Ali  Khan', 'Sarah Connor', 'John Doe'], rows), # Duplicates & spaces
        'Date': np.random.choice(['2024-01-01', '01/02/2024', 'Jan 3, 2024', '2024/01/04', None], rows), # Inconsistent formats
        'Amount': np.random.choice([100, 250, 500, '1,000', None, 50], rows), # Mixed types (strings with commas)
        'Status': np.random.choice(['Paid', 'pending', 'PAID', 'Unpaid', 'Error'], rows) # Inconsistent casing
    }
    
    # Intentionally add duplicates
    df = pd.DataFrame(data)
    df = pd.concat([df, df.iloc[:5]], ignore_index=True) # Duplicate first 5 rows
    return df

# --- 2. THE AUTOMATION LOGIC ---
def clean_data(df):
    report_log = []
    
    # A. Standardize Column Names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    report_log.append("✅ Standardized column headers (lowercase, no spaces).")
    
    # B. Remove Duplicates
    initial_count = len(df)
    df = df.drop_duplicates()
    removed_count = initial_count - len(df)
    report_log.append(f"✅ Removed {removed_count} duplicate rows.")
    
    # C. Fix 'Amount' Column (Remove commas, convert to float)
    if 'amount' in df.columns:
        df['amount'] = df['amount'].astype(str).str.replace(',', '', regex=True)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['amount'].fillna(0, inplace=True) # Fill missing money with 0
        report_log.append("✅ Cleaned 'Amount' column (removed commas, converted text to numbers).")

    # D. Fix 'Status' Column (Capitalize consistently)
    if 'status' in df.columns:
        df['status'] = df['status'].str.title()
        report_log.append("✅ Standardized 'Status' column casing.")
        
    # E. Fix Date Column
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']) # Drop rows where date is completely broken
        report_log.append("✅ Parsed mixed Date formats into ISO standard (YYYY-MM-DD).")
        
    return df, report_log

# --- 3. UI LAYOUT ---

# Sidebar
st.sidebar.header("1. Upload / Generate")
data_source = st.sidebar.radio("Choose Data Source:", ["Use Messy Demo Data", "Upload CSV File"])

if data_source == "Use Messy Demo Data":
    df_raw = generate_messy_data()
    st.sidebar.info("Generated a sample dataset with intentional errors (duplicates, bad dates, text in number fields).")
else:
    uploaded_file = st.sidebar.file_uploader("Upload your messy CSV", type=["csv"])
    if uploaded_file:
        df_raw = pd.read_csv(uploaded_file)
    else:
        st.stop()

# Main Area
col1, col2 = st.columns(2)

with col1:
    st.subheader("❌ Raw / Messy Data")
    st.dataframe(df_raw.head(10))
    st.error(f"Rows: {len(df_raw)} | Columns with Errors: Dates, Case sensitivity, Duplicates")

# Button to trigger automation
if st.button("🚀 Run Automation Pipeline", type="primary"):
    
    with st.spinner("Running cleaning algorithms..."):
        time.sleep(1.5) # Simulate processing time for effect
        df_clean, logs = clean_data(df_raw.copy())
    
    # Success Area
    st.balloons()
    
    with col2:
        st.subheader("✅ Cleaned / Standardized Data")
        st.dataframe(df_clean.head(10))
        st.success(f"Rows: {len(df_clean)} | Data is now clean and ready for analysis.")

    # Automation Logs
    st.markdown("---")
    st.subheader("⚙️ Automation Execution Log")
    for log in logs:
        st.write(log)
    
    # Calculate Impact
    total_revenue = df_clean['amount'].sum()
    st.metric(label="Total Recovered Revenue (Calculated from Clean Data)", value=f"${total_revenue:,.2f}")

    # Simulate Email
    with st.expander("📧 Email Notification Preview"):
        st.info(f"""
        **To:** manager@company.com
        **Subject:** Daily Sales Data Processed Successfully
        
        Hello Team,
        The daily data pipeline has finished.
        - {len(df_raw)} records processed.
        - {len(df_clean)} valid records saved.
        - Total Revenue: ${total_revenue:,.2f}
        
        The clean file is attached.
        
        *Sent by Python Automation Bot*
        """)
        
    # Download Button
    csv = df_clean.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Cleaned CSV",
        data=csv,
        file_name='clean_data_export.csv',
        mime='text/csv',
    )