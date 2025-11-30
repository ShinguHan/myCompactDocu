import streamlit as st
from database import SessionLocal
from services.analytics_service import AnalyticsService
from exporter import export_to_excel

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard")

db = SessionLocal()
analytics_service = AnalyticsService(db)

# Filters
col1, col2 = st.columns(2)
with col1:
    companies = analytics_service.get_companies()
    company_names = ["All"] + [c.name for c in companies]
    selected_company = st.selectbox("Filter by Company", company_names)

with col2:
    items = analytics_service.get_items()
    item_names = ["All"] + [i.name for i in items]
    selected_item = st.selectbox("Filter by Item", item_names)

# Get Data
df = analytics_service.get_filtered_transactions(selected_company, selected_item)

# Display Data
if not df.empty:
    # Metrics
    total_amount = df["Total Amount"].sum()
    total_qty = df["Quantity"].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Transactions", len(df))
    m2.metric("Total Amount", f"{total_amount:,.0f} KRW")
    m3.metric("Total Quantity", f"{total_qty:,.0f}")

    # Export Button
    excel_data = export_to_excel(db)
    st.download_button(
        label="📥 Export to Excel",
        data=excel_data,
        file_name="transactions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.dataframe(df, width='stretch')
else:
    st.info("No transactions found.")

db.close()
